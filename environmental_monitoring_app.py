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

# Data cleaning and feature engineering
df["value_type"] = df["value_type"].replace(
    ['P2', 'humidity', 'temperature', 'P1', 'pressure', 'durP1', 'durP2', 'P10'],
    ['PM2.5', 'Humidity', 'Temperature', 'PM10', 'Pressure', 'durPM10', 'durPM2.5', 'PM10']
)

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df = df.dropna(subset=["timestamp", "value", "region"])  # Ensure essential fields are present

df["date"] = df["timestamp"].dt.date
df["month"] = df["timestamp"].dt.month
df["day_name"] = df["timestamp"].dt.day_name()

# Sidebar filters
st.sidebar.header("Filters")

# Region selector
regions = df["region"].dropna().unique()
selected_region = st.sidebar.selectbox("Select Region", sorted(regions))

# Month selector
month_numbers = sorted(df["month"].dropna().unique())
month_names = [calendar.month_name[int(m)] for m in month_numbers]
month_mapping = dict(zip(month_names, month_numbers))
selected_month_name = st.sidebar.selectbox("Select Month", month_names)
selected_month = month_mapping[selected_month_name]

# Filter data by region and month
filtered_df = df[
    (df["region"] == selected_region) &
    (df["month"] == selected_month)
]

# Pivot data to get variable columns
pivot_df = filtered_df.pivot_table(
    index=["date"],
    columns="value_type",
    values="value",
    aggfunc="mean"
).reset_index()

# Sidebar variable checkboxes in 3-column layout
variable_options = list(pivot_df.columns[1:])  # skip "date"
cols = st.sidebar.columns(3)
selected_vars = [var for i, var in enumerate(variable_options) if cols[i % 3].checkbox(var)]

# Line chart of selected variables by day
if not selected_vars:
    st.warning("Please select at least one variable.")
else:
    chart_df = pivot_df[["date"] + selected_vars]
    chart_df = chart_df.dropna(how="all", subset=selected_vars)

    if chart_df.empty:
        st.warning("No data available for selected variables and filters.")
    else:
        fig = px.line(
            chart_df,
            x="date",
            y=selected_vars,
            title=f"Daily Variation of Selected Variables in {selected_region} ({selected_month_name})",
            labels={"value": "Average Value", "variable": "Parameter"},
        )
        st.plotly_chart(fig, use_container_width=True)

# Optional: Display raw filtered data for verification
# st.dataframe(chart_df)
