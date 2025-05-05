import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import calendar
import os

# Page setup
st.set_page_config(layout="wide")
st.title("Environmental Monitoring App")

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

# Pivot data
pivot_df = df.pivot_table(
    index=["timestamp", "region", "lat", "lon", "date", "hour", "month", "day"],
    columns="value_type",
    values="value",
    aggfunc="mean"
).reset_index()

# Sidebar filters
st.sidebar.header("Filters")

regions = pivot_df["region"].dropna().unique()
selected_region = st.sidebar.selectbox("Select Region", sorted(regions))

# Month selection
month_numbers = sorted(pivot_df["month"].dropna().unique())
month_names = [calendar.month_name[int(m)] for m in month_numbers]
month_mapping = dict(zip(month_names, month_numbers))
selected_month_name = st.sidebar.selectbox("Select Month", month_names)
selected_month = month_mapping[selected_month_name]

# Multiselect as checkboxes
variable_options = list(pivot_df.columns[8:])
cols = st.sidebar.columns(3)
selected_vars = [var for i, var in enumerate(variable_options) if cols[i % 3].checkbox(var)]

# Filtered data
filtered_df = pivot_df[
    (pivot_df["region"] == selected_region) & 
    (pivot_df["month"] == selected_month)
]

# Time-series line chart
if selected_vars:
    if filtered_df.empty:
        st.warning("No data available for the selected region and month.")
    else:
        daily_avg = filtered_df.groupby("date")[selected_vars].mean().reset_index()

        if daily_avg[selected_vars].isnull().all().all():
            st.warning("Selected variables contain only missing values for this filter.")
        else:
            fig = px.line(
                daily_avg,
                x="date",
                y=selected_vars,
                title=f"Daily Variation in {selected_region} ({selected_month_name})",
                labels={"value": "Average Value", "variable": "Parameter"},
            )
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Please select at least one variable to visualize.")

# Choropleth Map
if selected_vars:
    selected_df = pivot_df.groupby("region")[selected_vars].mean().reset_index()
    selected_df = selected_df.dropna(subset=[selected_vars[0]])

    geojson_path = "Sensors_data/map.geojson"
    if not os.path.exists(geojson_path):
        st.error("GeoJSON file not found. Please place it at `Sensors_data/map.geojson`.")
    else:
        with open(geojson_path, "r") as f:
            geojson = json.load(f)

        # Plot choropleth map
        fig_map = px.choropleth(
            selected_df,
            geojson=geojson,
            locations="region",
            featureidkey="properties.region",  # <-- This must match your GeoJSON property
            color=selected_vars[0],
            color_continuous_scale="Viridis",
            title=f"Average {selected_vars[0]} by Region",
        )
        fig_map.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig_map, use_container_width=True)
