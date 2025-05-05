import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import calendar
import os

# Page setup
st.set_page_config(layout="wide")
st.title("🌍 Environmental Monitoring App")

# Load data
path = "Sensors_data/air_quality_data.csv"
df = pd.read_csv(path)

# Preprocessing
df["value_type"] = df["value_type"].replace(
    ['P2', 'humidity', 'temperature', 'P1', 'pressure', 'durP1', 'durP2', 'P10'],
    ['PM2.5', 'Humidity', 'Temperature', 'PM10', 'Pressure', 'durPM10', 'durPM2.5', 'PM10']
)

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df["date"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour
df["month"] = df["timestamp"].dt.month
df["day"] = df["timestamp"].dt.day_name()

# Pivot
pivot_df = df.pivot_table(
    index=["timestamp", "region", "lat", "lon", "date", "hour", "month", "day"],
    columns="value_type",
    values="value",
    aggfunc="mean"
).reset_index()

# Sidebar filters
st.sidebar.header("🧭 Filters")

regions = sorted(pivot_df["region"].dropna().unique())
selected_region = st.sidebar.selectbox("Select Region", regions)

month_numbers = sorted(pivot_df["month"].dropna().unique())
month_names = [calendar.month_name[int(m)] for m in month_numbers]
month_mapping = dict(zip(month_names, month_numbers))
selected_month_name = st.sidebar.selectbox("Select Month", month_names)
selected_month = month_mapping[selected_month_name]

# Variables
variable_options = list(pivot_df.columns[8:])
cols = st.sidebar.columns(3)
selected_vars = [var for i, var in enumerate(variable_options) if cols[i % 3].checkbox(var)]

# DEBUG: show table of selected region/month
st.subheader("🔍 Filtered Sample Data")
filtered_df = pivot_df[
    (pivot_df["region"] == selected_region) &
    (pivot_df["month"] == selected_month)
]

st.dataframe(filtered_df.head())

if not selected_vars:
    st.warning("Please select at least one variable to continue.")
else:
    daily_avg = filtered_df.groupby("date")[selected_vars].mean().reset_index()

    if daily_avg.empty or daily_avg[selected_vars].isnull().all().all():
        st.warning("⚠️ No valid data available for selected filters.")
    else:
        fig = px.line(
            daily_avg,
            x="date",
            y=selected_vars,
            title=f"Daily Variation in {selected_region} ({selected_month_name})",
            labels={"value": "Avg Value", "variable": "Metric"},
        )
        st.plotly_chart(fig, use_container_width=True)
    # Choropleth
    st.subheader("Choropleth Map")
    choropleth_df = pivot_df.groupby("region")[selected_vars].mean().reset_index()

    # Show debug table
    st.dataframe(choropleth_df)

    geojson_path = "Sensors_data/map.geojson"
    if not os.path.exists(geojson_path):
        st.error("GeoJSON not found. Please place it at `Sensors_data/map.geojson`.")
    else:
        with open(geojson_path) as f:
            geojson = json.load(f)

        # DEBUG: print keys in GeoJSON
        sample_props = geojson["features"][0]["properties"]
        st.markdown(f"GeoJSON sample properties: `{list(sample_props.keys())}`")

        # Try best guess: what field links region?
        matching_key = None
        for k in sample_props:
            if set(choropleth_df["region"]) & set([f["properties"][k] for f in geojson["features"]]):
                matching_key = k
                break

        if not matching_key:
            st.error("No matching region keys found in GeoJSON.")
        else:
            st.success(f" Matched region with GeoJSON key: `properties.{matching_key}`")

            fig_map = px.choropleth(
                choropleth_df,
                geojson=geojson,
                locations="region",
                featureidkey=f"properties.{matching_key}",
                color=selected_vars[0],
                color_continuous_scale="Viridis",
                title=f"Average {selected_vars[0]} by Region",
            )
            fig_map.update_geos(fitbounds="locations", visible=False)
            st.plotly_chart(fig_map, use_container_width=True)
