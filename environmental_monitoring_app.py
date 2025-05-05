import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import pydeck as pdk
import io
import seaborn as sns
import matplotlib.pyplot as plt
import calendar


# Page setup
st.set_page_config(layout="wide")
st.title("Environmental Monitoring App")

# Load data
path = "Sensors_data/air_quality_data.csv"
df = pd.read_csv(path)

# Preprocessing
df.value_type.replace(
    ['P2', 'humidity', 'temperature', 'P1', 'pressure', 'durP1', 'durP2', 'P10'],
    ['PM2.5', 'Humidity', 'Temperature', 'PM10', 'Pressure', 'durPM10', 'durPM2.5', 'PM10'],
    inplace=True
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

# Region select (single)
regions = pivot_df["region"].dropna().unique()
selected_region = st.sidebar.selectbox("Select Region", regions)

# Convert month numbers to names
month_numbers = sorted(pivot_df["month"].dropna().unique())
month_names = [calendar.month_name[int(m)] for m in month_numbers]
month_mapping = dict(zip(month_names, month_numbers))

selected_month_name = st.sidebar.selectbox("Select Month", month_names)
selected_month = month_mapping[selected_month_name]

## Multiselect for variables (displayed as checkboxes)
#variable_options = list(pivot_df.columns[8:])
##selected_variable = st.sidebar.radio("Select Variable", variable_options)
#cols = st.sidebar.columns(3)  # Creates 3 buttons per row
#selected_vars = []
#for i, var in enumerate(variable_options):
    #if cols[i % 3].checkbox(var):
        #selected_vars.append(var)

# Pivot data: value_type becomes columns
pivot_df = df.pivot_table(
    index=["region", "lat", "lon"],
    columns="value_type",
    values="value",
    aggfunc="mean"
).reset_index()

# Variables to choose from
variables = [col for col in pivot_df.columns if col not in ["region", "lat", "lon"]]

# Variable selector — radio with button style
selected_variable = st.radio(
    "Select a variable to visualize:",
    options=variables,
    horizontal=True,
)

# Plot choropleth-like map using lat/lon
fig = px.scatter_mapbox(
    pivot_df,
    lat="lat",
    lon="lon",
    color=selected_variable,
    size=selected_variable,
    hover_name="region",
    color_continuous_scale="Viridis",
    size_max=30,
    zoom=4,
    height=600,
    title=f"Average {selected_variable} by Region"
)

fig.update_layout(mapbox_style="open-street-map")
st.plotly_chart(fig)


