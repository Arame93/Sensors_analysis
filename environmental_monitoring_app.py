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

# Multiselect for variables (displayed as checkboxes)
variable_options = list(pivot_df.columns[8:])
selected_variables = st.sidebar.multiselect("Select Variables", variable_options, default=[variable_options[0]])
