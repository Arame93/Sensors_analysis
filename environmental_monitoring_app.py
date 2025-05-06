import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import calendar

# Title and config
st.set_page_config(layout="wide")
#st.title("Environmental Monitoring App")
st.markdown("""
    <style>
        .main-title {
            background-color: #28a745;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            color: white;
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 20px;
        }
    </style>
    <div class="main-title">Environmental Monitoring App</div>
""", unsafe_allow_html=True)

# Load data
df = pd.read_csv("Sensors_data/air_quality_data.csv")

# Preprocessing
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df.dropna(subset=["timestamp", "value", "region", "value_type"], inplace=True)
df["date"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour
df["month"] = df["timestamp"].dt.month

# Clean and rename value_type labels
rename_map = {
    'P2': 'PM2.5',
    'humidity': 'Humidity',
    'temperature': 'Temperature',
    'P1': 'PM10',
    'P10': 'PM10',
    'pressure': 'Pressure',
    'durP1': 'durPM10',
    'durP2': 'durPM2.5',
    'noise_Leq': 'Noise_Leq'
}
df["value_type"] = df["value_type"].replace(rename_map)


# Filters
with st.container():
    col1, col2 = st.columns([1, 1])
    selected_region = col1.selectbox("Select Region", regions)
    selected_month_name = col2.selectbox("Select Month", month_names)

    st.markdown("#### Select Variables")
    cols = st.columns(3)
    selected_vars = [v for i, v in enumerate(expected_variables) if cols[i % 3].checkbox(v, key=v)]

# Sidebar filters
st.sidebar.header("Filters")

regions = df["region"].dropna().unique()
selected_region = st.sidebar.selectbox("Select Region", sorted(regions))

# Month selector
month_numbers = sorted(df["month"].dropna().unique())
month_names = [calendar.month_name[int(m)] for m in month_numbers]
month_mapping = dict(zip(month_names, month_numbers))
selected_month_name = st.sidebar.selectbox("Select Month", month_names)
selected_month = month_mapping[selected_month_name]

# 3-column checkbox for variables
all_vars = sorted(df["value_type"].dropna().unique())
cols = st.sidebar.columns(3)
selected_vars = [var for i, var in enumerate(all_vars) if cols[i % 3].checkbox(var)]

# Filter data
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

#st.subheader("Daily and Hourly Averages")
col1, col2 = st.columns(2)

# 1. Descriptive Daily Analysis
#st.header("Descriptive Analysis")
with col1:
    st.markdown("##### Daily Average")
    if available_vars:
        daily_df = pivot_df.groupby("date")[available_vars].mean().reset_index()
        fig = px.line(
            daily_df,
            x="date",
            y=available_vars,
            title=f"Daily Average of {' + '.join(available_vars)} in {selected_region} ({selected_month_name})",
            labels={"value": "Average Value", "variable": "Variable"},
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Please select at least one variable to display daily trends.")
with col2:
    st.markdown("##### Hourly Average")

# 2. Hourly Trends
#st.header("Hourly Trends")
    if available_vars:
        hourly_df = pivot_df.groupby("hour")[available_vars].mean().reset_index()
        fig_hourly = px.line(
            hourly_df,
            x="hour",
            y=available_vars,
            title=f"Hourly Average of {' + '.join(available_vars)}",
            labels={"value": "Average Value", "variable": "Variable"},
        )
        st.plotly_chart(fig_hourly, use_container_width=True)
    else:
        st.warning("Please select at least one variable to display hourly trends.")

# 3. Geospatial Map
#st.header("Geospatial Air Quality Map")
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

# 4. Regional Comparison (independent of region/month filters)
#st.header("Regional Comparison")
compare_df = df[df["value_type"].isin(selected_vars)]
region_avg = compare_df.groupby(["region", "value_type"])["value"].mean().reset_index()
if not region_avg.empty:
    fig_compare = px.bar(
        region_avg,
        x="region",
        y="value",
        color="value_type",
        barmode="group",
        title="Average Values by Region",
        labels={"value": "Average", "value_type": "Variable"},
    )
    st.plotly_chart(fig_compare, use_container_width=True)
else:
    st.warning("No regional comparison data available.")

## 5. Trend Detection (7-day rolling)
#st.header("Trend Detection")
#if available_vars and not pivot_df.empty:
    #pivot_df.set_index("timestamp", inplace=True)
    #for var in available_vars:
        #if var in pivot_df.columns:
            #rolling = pivot_df[var].resample("D").mean().rolling(window=7).mean()
            #st.subheader(f"{var} - 7 Day Rolling Average")
            #st.line_chart(rolling)
    #pivot_df.reset_index(inplace=True)
#else:
    #st.warning("No data for trend detection.")

# 6. Anomaly Detection (Boxplot)
#st.header("Anomaly Detection")
if not filtered_df.empty and available_vars:
    fig_anomaly = px.box(
        filtered_df[filtered_df["value_type"].isin(available_vars)],
        x="value_type",
        y="value",
        title="Anomaly Detection (Detect Outliers)",
        points="outliers",
        labels={"value": "Value", "value_type": "Variable"}
    )
    st.plotly_chart(fig_anomaly, use_container_width=True)
else:
    st.warning("No data for anomaly detection.")

# 7. Correlation placeholder
st.header("🌦️ Weather Correlation")
st.info("Add weather data to perform correlation analysis with temperature, humidity, etc.")

st.markdown("</div>", unsafe_allow_html=True)


# Footer
st.caption("Built with Streamlit and openAFRICA data")
