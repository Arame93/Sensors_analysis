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
    ['P2', 'humidity', 'temperature', 'P1', 'pressure', 'durP1', 'durP2', 'P10'],
    ['PM2.5', 'Humidity', 'Temperature', 'PM10', 'Pressure', 'durPM10', 'durPM2.5', 'PM10']
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

# 1. Descriptive Analysis
st.header("Descriptive Analysis")
daily_df = pivot_df[["date"] + selected_vars].dropna(how="all")
daily_df = daily_df.groupby("date")[selected_vars].mean().rolling(window=3, min_periods=1).mean().reset_index()
daily_long = daily_df.melt(id_vars="date", var_name="Variable", value_name="Value")
var_str = " + ".join(selected_vars)
fig_daily = px.line(daily_long, x="date", y="Value", color="Variable", title=f"Daily Average {var_str}")
st.plotly_chart(fig_daily, use_container_width=True)

# 2. Time Series Analysis
st.header("Hourly Trends")
hourly_df = pivot_df[["hour"] + selected_vars].dropna(how="all")
hourly_df = hourly_df.groupby("hour")[selected_vars].mean().rolling(window=2, min_periods=1).mean().reset_index()
hourly_long = hourly_df.melt(id_vars="hour", var_name="Variable", value_name="Value")
var_str = " + ".join(selected_vars)
fig_hour = px.line(hourly_long, x="hour", y="Value", color="Variable", title=f"Hourly Average {var_str}")
st.plotly_chart(fig_hour, use_container_width=True)

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
# 4. Comparative Analysis
st.header("Regional Comparison")

if selected_vars:
    region_avg = df[df["value_type"].isin(selected_vars)].groupby(["region", "value_type"])["value"].mean().reset_index()
    if not region_avg.empty:
        fig_compare = px.bar(
            region_avg,
            x="region",
            y="value",
            color="value_type",
            barmode="group",
            title="Average Values by Region",
            labels={"value_type": "Variable", "value": "Average"}
        )
        st.plotly_chart(fig_compare, use_container_width=True)
    else:
        st.warning("No comparison data available for the selected variables.")
else:
    st.info("Select at least one variable to see regional comparison.")
    
# 5. Trend Detection
st.header("Trend Detection")
if not pivot_df.empty and selected_vars:
    trend_df = pivot_df[["timestamp"] + selected_vars].set_index("timestamp").resample("D").mean().rolling(window=7).mean().reset_index()
    trend_long = trend_df.melt(id_vars="timestamp", value_vars=selected_vars, var_name="Variable", value_name="Value")
    fig_trend = px.line(trend_long, x="timestamp", y="Value", color="Variable", title="7-Day Rolling Averages")
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.warning("Not enough data to detect trends.")

# 6. Anomaly Detection
st.header("Anomaly Detection")
st.header("Anomaly Detection")
if not filtered_df.empty:
    anomaly_df = filtered_df[filtered_df["value_type"].isin(selected_vars)]
    fig_anomaly = px.box(
        anomaly_df,
        x="value_type",
        y="value",
        points="outliers",
        title="Anomaly Detection via Boxplot",
        labels={"value_type": "Variable", "value": "Sensor Value"}
    )
    st.plotly_chart(fig_anomaly, use_container_width=True)
else:
    st.warning("No anomaly data to show.")

# 7. Correlation Placeholder
st.header("🌦️ Weather Correlation")
st.info("Add weather data to perform correlation analysis with temperature, humidity, etc.")

# Footer
st.caption("Built with Streamlit and openAFRICA data")
