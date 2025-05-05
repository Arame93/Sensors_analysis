import streamlit as st
import pandas as pd
import plotly.express as px
import calendar

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

# Drop missing lat/lon
pivot_df = pivot_df.dropna(subset=["lat", "lon"])

# Sidebar filters
st.sidebar.header("Filters")

# Regions
regions = pivot_df["region"].dropna().unique()
selected_region = st.sidebar.selectbox("Select Region (for detailed view)", ["All"] + list(regions))

# Month names
month_numbers = sorted(pivot_df["month"].dropna().unique())
month_names = [calendar.month_name[int(m)] for m in month_numbers]
month_mapping = dict(zip(month_names, month_numbers))

selected_month_name = st.sidebar.selectbox("Select Month", month_names)
selected_month = month_mapping[selected_month_name]

# Multiselect as checkboxes
variable_options = list(pivot_df.columns[8:])
cols = st.sidebar.columns(3)
selected_vars = [var for i, var in enumerate(variable_options) if cols[i % 3].checkbox(var)]

# Filter by selected month
filtered_df = pivot_df[pivot_df["month"] == selected_month].copy()

# Map: Show all regions by default
if selected_vars:
    filtered_df["composite"] = filtered_df[selected_vars].mean(axis=1)

    fig = px.scatter_mapbox(
        filtered_df,
        lat="lat",
        lon="lon",
        color="composite",
        size="composite",
        hover_name="region",
        color_continuous_scale="Viridis",
        size_max=30,
        zoom=4,
        height=600,
        title=f"Map of {' + '.join(selected_vars)} Across All Regions ({selected_month_name})"
    )

    fig.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig)
else:
    st.warning("Please select at least one variable to visualize on the map.")
