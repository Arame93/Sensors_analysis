import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import calendar
from streamlit_plotly_events import plotly_events

# ------------------------------
# Page Setup and Title Styling
# ------------------------------
st.set_page_config(layout="wide")

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

# ------------------------------
# Load and Preprocess Data
# ------------------------------
df = pd.read_csv("Sensors_data/air_quality_data.csv")
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df.dropna(subset=["timestamp", "value", "region", "value_type"], inplace=True)
df["date"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour
df["month"] = df["timestamp"].dt.month

# Rename variables for clarity
rename_map = {
    'P2': 'PM2.5', 'humidity': 'Humidity', 'temperature': 'Temperature',
    'P1': 'PM10', 'P10': 'PM10', 'pressure': 'Pressure',
    'durP1': 'durPM10', 'durP2': 'durPM2.5', 'noise_Leq': 'Noise_Leq'
}
rename_items = {
    "Meru Sensor Mobile 6": "Meru", "Meru mobile sensor": "Meru"
}
df["value_type"] = df["value_type"].replace(rename_map)
df["region"] = df["region"].replace(rename_items)

# ------------------------------
# Filter UI
# ------------------------------
st.subheader("Filters")
col1, col2 = st.columns(2)

regions = df["region"].dropna().unique()
selected_region = col1.selectbox("Select Region", sorted(regions), key="region_select")

month_numbers = sorted(df["month"].dropna().unique())
month_names = [calendar.month_name[int(m)] for m in month_numbers]
month_mapping = dict(zip(month_names, month_numbers))
selected_month_name = col2.selectbox("Select Month", month_names, key="month_select")
selected_month = month_mapping[selected_month_name]

st.markdown("###### Select variables")
all_vars = sorted(df["value_type"].dropna().unique())
var_cols = st.columns(3)
selected_vars = [var for i, var in enumerate(all_vars) if var_cols[i % 3].checkbox(var, key=f"var_{var}")]

# ------------------------------
# Filter and Pivot the Data
# ------------------------------
filtered_df = pd.DataFrame()
pivot_df = pd.DataFrame()
available_vars = []

if selected_vars:
    filtered_df = df[
        (df["region"] == selected_region) &
        (df["month"] == selected_month) &
        (df["value_type"].isin(selected_vars))
    ]

    if not filtered_df.empty:
        pivot_df = filtered_df.pivot_table(
            index=["timestamp", "date", "hour"],
            columns="value_type",
            values="value",
            aggfunc="mean"
        ).reset_index()

        available_vars = [v for v in selected_vars if v in pivot_df.columns]

# --------------------------
# Daily and Hourly Trend Charts
# --------------------------
st.header("Daily and hourly trends")

# daily plot with click interaction
#st.header("Daily trends")
if not pivot_df.empty:
    # Compute daily averages
    daily_df = pivot_df.groupby("date")[available_vars].mean().reset_index()

    # Melt for proper plotting: one variable per line
    daily_melted = daily_df.melt(id_vars="date", value_vars=available_vars)

    # Plot with Plotly Express
    fig_daily = px.line(
        daily_melted,
        x="date", y="value", color="variable",
        title=f"Daily Averages in {selected_region} ({selected_month_name})",
        markers=True
    )
    st.markdown("Click on a point to see hourly trends for that date:")
    selected_points = plotly_events(fig_daily, click_event=True, select_event=False)
    st.write("")  # Add space

    # hourly trend on clicked day
    if selected_points:
        selected_date_str = selected_points[0]['x']  # clicked date string
        selected_date = pd.to_datetime(selected_date_str).date()

        st.subheader(f"Hourly trends for {selected_date}")
        hourly_df = pivot_df[pivot_df["date"] == selected_date].groupby("hour")[available_vars].mean().reset_index()
        fig_hourly = px.line(
            hourly_df, x="hour", y=available_vars,
            title=f"Hourly Averages on {selected_date}"
        )
        st.plotly_chart(fig_hourly, use_container_width=True)
    else:
        st.info("Click on a date in the daily chart to see hourly trends.")

# --------------------------
# Anomaly Detection
# --------------------------
st.subheader("⚠️ Anomaly Detection")
if not filtered_df.empty:
    fig_anomaly = px.box(
        filtered_df,
        x="value_type", y="value",
        title="Outlier Detection",
        points="outliers"
    )
    fig_anomaly.update_layout(xaxis_title=None)
    st.plotly_chart(fig_anomaly, use_container_width=True)
else:
    st.info("Not enough data to detect anomalies.")

# --------------------------
# Regional Comparison
# --------------------------
st.subheader("📍 Regional Comparison")
compare_df = df[df["value_type"].isin(selected_vars)]

if not compare_df.empty:
    region_avg = compare_df.groupby(["region", "value_type"])["value"].mean().reset_index()
    fig_compare = px.bar(
        region_avg,
        x="region", y="value", color="value_type",
        barmode="group", title="Average Values by Region"
    )
    st.plotly_chart(fig_compare, use_container_width=True)
else:
    st.info("No data available for regional comparison.")

# --------------------------
# Weather Correlation
# --------------------------
st.subheader("🌦️ Weather Correlation")

if available_vars and not pivot_df.empty:
    corr_df = pivot_df[available_vars].dropna()
    if len(corr_df.columns) >= 2:
        corr_matrix = corr_df.corr()
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=True,
            color_continuous_scale="RdBu_r",
            title="Correlation Heatmap between Selected Variables",
            labels=dict(color="Correlation"),
            aspect="auto"
        )
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.warning("Not enough variables selected to compute correlation.")
else:
    st.warning("Please select at least two variables to view correlation heatmap.")

# --------------------------
# Footer
# --------------------------
st.caption("Built with Streamlit and openAFRICA data")
