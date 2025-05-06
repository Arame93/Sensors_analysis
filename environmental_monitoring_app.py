import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import calendar

# Title
st.set_page_config(layout="wide")
st.title("Environmental Mornitoring App")

# Load data
df = pd.read_csv("Sensors_data/air_quality_data.csv")

# Preprocessing
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df["date"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour
df["month"] = df["timestamp"].dt.month
df["value_type"] = df["value_type"].replace(
    ['P2', 'humidity', 'temperature', 'P1', 'pressure', 'durP1', 'durP2', 'P10', "noise_Leq"],
    ['PM2.5', 'Humidity', 'Temperature', 'PM10', 'Pressure', 'durPM10', 'durPM2.5', 'PM10', "Noise_Leq"]
)

# Sidebar filters
st.sidebar.header("Filters")

regions = df["region"].dropna().unique()
selected_region = st.sidebar.selectbox("Select Region", regions)

month_numbers = sorted(df["month"].dropna().unique())
month_names = [calendar.month_name[int(m)] for m in month_numbers]
month_mapping = dict(zip(month_names, month_numbers))
selected_month_name = st.sidebar.selectbox("Select Month", month_names)
selected_month = month_mapping[selected_month_name]

# 3-column checkbox variable selector
all_vars = df["value_type"].dropna().unique()
cols = st.sidebar.columns(3)
selected_vars = [var for i, var in enumerate(all_vars) if cols[i % 3].checkbox(var)]


# Variables (multicolumn checkboxes)
expected_variables = sorted(df["value_type"].dropna().unique())
cols = st.sidebar.columns(3)
selected_vars = [v for i, v in enumerate(expected_variables) if cols[i % 3].checkbox(v)]


# Apply filters
filtered_df = df[
    (df["region"] == selected_region) &
    (df["month"] == selected_month) &
    (df["value_type"].isin(selected_vars))
]

# Pivot data
pivot_df = filtered_df.pivot_table(
    index=["timestamp", "date", "hour"],
    columns="value_type",
    values="value",
    aggfunc="mean"
).reset_index()

available_vars = [var for var in selected_vars if var in pivot_df.columns]


# 1. Descriptive Analysis
st.header("Descriptive Analysis")
if selected_vars:
    daily_df = pivot_df.groupby("date")[selected_vars].mean().reset_index()
    fig = px.line(
        daily_df,
        x="date",
        y=selected_vars,
        title=f"Daily Average of {' + '.join(selected_vars)} in {selected_region} ({selected_month_name})",
        labels={"value": "Average Value", "variable": "Variable"},
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Please select at least one variable to display daily trends.")

# 2. Time Series Analysis
st.header("Hourly Trends")
if selected_vars:
    hourly_df = pivot_df.groupby("hour")[selected_vars].mean().reset_index()
    fig_hourly = px.line(
        hourly_df,
        x="hour",
        y=selected_vars,
        title=f"Hourly Average of {' + '.join(selected_vars)}",
        labels={"value": "Average Value", "variable": "Variable"},
    )
    st.plotly_chart(fig_hourly, use_container_width=True)
else:
    st.warning("Please select at least one variable to display hourly trends.")

# 3. Geospatial Air Quality Map
st.header("Geospatial Air Quality Map")
location_avg = filtered_df.groupby(["lat", "lon"])[["value"]].mean().reset_index()
if not location_avg.empty:
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(
            latitude=location_avg["lat"].mean(),
            longitude=location_avg["lon"].mean(),
            zoom=10,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=location_avg,
                get_position='[lon, lat]',
                get_color='[200, 30, 0, 160]',
                get_radius=300,
            ),
        ],
    ))
else:
    st.warning("No map data to display.")

# 4. Comparative Analysis
compare_df = df[df["value_type"].isin(selected_vars)]
region_avg = compare_df.groupby(["region", "value_type"])["value"].mean().reset_index()

if not region_avg.empty:
    fig_compare = px.bar(
        region_avg,
        x="region",
        y="value",
        color="value_type",
        barmode="group",
        title="📊 Average Values by Region",
        labels={"value": "Average", "value_type": "Variable"},
    )
    st.plotly_chart(fig_compare, use_container_width=True)
else:
    st.warning("No regional comparison data available.")

#else:
    #st.info("Select at least one variable to see regional comparison.")
    
# 5. Trend Detection
st.header("Trend Detection")
if selected_vars and not pivot_df.empty:
    pivot_df.set_index("timestamp", inplace=True)
    for var in selected_vars:
        if var in pivot_df.columns:
            rolling = pivot_df[var].resample("D").mean().rolling(window=7).mean()
            st.subheader(f"{var} - 7 Day Rolling Average")
            st.line_chart(rolling)
    pivot_df.reset_index(inplace=True)
else:
    st.warning("No data for trend detection.")


# 6. Anomaly Detection
st.header("Anomaly Detection")
if not filtered_df.empty and selected_vars:
    fig_anomaly = px.box(
        filtered_df[filtered_df["value_type"].isin(selected_vars)],
        x="value_type",
        y="value",
        title="Boxplot of Selected Variables (Detect Outliers)",
        points="outliers",
        labels={"value": "Value", "value_type": "Variable"}
    )
    st.plotly_chart(fig_anomaly, use_container_width=True)
else:
    st.warning("No data for anomaly detection.")

# 7. Correlation Placeholder
st.header("🌦️ Weather Correlation")
st.info("Add weather data to perform correlation analysis with temperature, humidity, etc.")

# Footer
st.caption("Built with Streamlit and openAFRICA data")
