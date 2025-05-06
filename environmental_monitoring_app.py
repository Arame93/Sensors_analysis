import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import calendar

# Title
st.set_page_config(layout="wide")
st.title("Air Quality Explorer")

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

# Variable selection
variables = df["value_type"].dropna().unique()
selected_vars = st.sidebar.multiselect("Select Variables", variables)

# Apply filters
filtered_df = df[
    (df["region"] == selected_region) &
    (df["month"] == selected_month) &
    (df["value_type"].isin(selected_vars))
]

# Pivot data for easier analysis
pivot_df = filtered_df.pivot_table(
    index=["timestamp", "date", "hour"],
    columns="value_type",
    values="value",
    aggfunc="mean"
).reset_index()

# 1. Descriptive Analysis
st.header("📊 Descriptive Analysis")

if not pivot_df.empty:
    for var in selected_vars:
        st.subheader(f"Daily Average - {var}")
        avg_by_day = pivot_df.groupby("date")[var].mean().reset_index()
        st.line_chart(avg_by_day.set_index("date"))
else:
    st.warning("No data available for the selected filters.")

# 2. Time Series Analysis
st.header("⏱️ Hourly Trends")
if not pivot_df.empty:
    for var in selected_vars:
        st.subheader(f"Hourly Average - {var}")
        hourly_avg = pivot_df.groupby("hour")[var].mean().reset_index()
        fig_hourly = px.line(hourly_avg, x="hour", y=var, title=f"{var} by Hour")
        st.plotly_chart(fig_hourly)
else:
    st.warning("No data to show hourly trends.")

# 3. Geospatial Air Quality Map
st.header("🗺️ Geospatial Air Quality Map")

# Join lat/lon from original filtered_df
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
st.header("📍 Regional Comparison")
region_avg = df[df["value_type"].isin(selected_vars)].groupby("region")["value"].mean().reset_index()
if not region_avg.empty:
    fig_compare = px.bar(region_avg, x="region", y="value", title="Average Value by Region")
    st.plotly_chart(fig_compare)
else:
    st.warning("No comparison data available.")

# 5. Trend Detection
st.header("📈 Trend Detection")
if not pivot_df.empty:
    for var in selected_vars:
        rolling = pivot_df.set_index("timestamp")[var].resample("D").mean().rolling(window=7).mean()
        st.subheader(f"{var} - 7 Day Rolling Average")
        st.line_chart(rolling)
else:
    st.warning("Not enough data to detect trends.")

# 6. Anomaly Detection
st.header("🚨 Anomaly Detection")
if not filtered_df.empty:
    for var in selected_vars:
        sub_df = filtered_df[filtered_df["value_type"] == var]
        q3 = sub_df["value"].quantile(0.75)
        iqr = q3 - sub_df["value"].quantile(0.25)
        threshold = q3 + 1.5 * iqr
        anomalies = sub_df[sub_df["value"] > threshold]
        st.subheader(f"{var} Anomalies")
        st.write(f"Detected {len(anomalies)} anomalies")
        st.dataframe(anomalies[["timestamp", "value", "region"]].sort_values("value", ascending=False))
else:
    st.warning("No anomaly data to show.")

# 7. Correlation Placeholder
st.header("🌦️ Weather Correlation")
st.info("Add weather data to perform correlation analysis with temperature, humidity, etc.")

# Footer
st.caption("Built with Streamlit and openAFRICA data")
