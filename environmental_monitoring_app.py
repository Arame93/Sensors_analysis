import streamlit as st
import pandas as pd
import plotly.express as px
import calendar

# Setup page
st.set_page_config(layout="wide")

# Load your data here
df = pd.read_csv("Sensors_data/air_quality_data.csv")
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df.dropna(subset=["timestamp", "value", "region", "value_type"], inplace=True)
df["date"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour
df["month"] = df["timestamp"].dt.month

# Rename value_type for display
rename_map = {
    'P2': 'PM2.5', 'humidity': 'Humidity', 'temperature': 'Temperature',
    'P1': 'PM10', 'P10': 'PM10', 'pressure': 'Pressure',
    'durP1': 'durPM10', 'durP2': 'durPM2.5', 'noise_Leq': 'Noise_Leq'
}
df["value_type"] = df["value_type"].replace(rename_map)

# Custom CSS
st.markdown("""
    <style>
        .frame-box {
            background-color: #f9f9f9;
            padding: 30px;
            border-radius: 12px;
            border: 2px solid #d3d3d3;
            margin-bottom: 30px;
        }
        .section-title {
            font-size: 22px;
            font-weight: 600;
            color: #444;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Open Frame
st.markdown('<div class="frame-box">', unsafe_allow_html=True)

# ───────── Filters Section ───────── #
st.markdown('<div class="section-title">🔍 Filters</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

# Region Filter
regions = sorted(df["region"].dropna().unique())
selected_region = col1.selectbox("Select Region", regions, key="region_select")

# Month Filter
month_numbers = sorted(df["month"].dropna().unique())
month_names = [calendar.month_name[int(m)] for m in month_numbers]
month_map = dict(zip(month_names, month_numbers))
selected_month_name = col2.selectbox("Select Month", month_names, key="month_select")
selected_month = month_map[selected_month_name]

# Variable checkboxes in 3 columns
all_vars = sorted(df["value_type"].dropna().unique())
st.markdown("##### Select Variables")
var_cols = st.columns(3)
selected_vars = [v for i, v in enumerate(all_vars) if var_cols[i % 3].checkbox(v, key=f"var_{v}")]

# Filtered Data
filtered_df = df[
    (df["region"] == selected_region) &
    (df["month"] == selected_month) &
    (df["value_type"].isin(selected_vars))
]

# Pivot for daily/hourly
pivot_df = filtered_df.pivot_table(
    index=["timestamp", "date", "hour"],
    columns="value_type",
    values="value",
    aggfunc="mean"
).reset_index()

available_vars = [var for var in selected_vars if var in pivot_df.columns]

# ───────── Daily and Hourly Trends ───────── #
if available_vars:
    st.markdown('<div class="section-title">📊 Daily and Hourly Trends</div>', unsafe_allow_html=True)
    col_d, col_h = st.columns(2)

    # Daily Plot
    with col_d:
        daily_df = pivot_df.groupby("date")[available_vars].mean().reset_index()
        fig_daily = px.line(
            daily_df, x="date", y=available_vars,
            title="Daily Average", labels={"value": "Avg", "variable": "Type"}
        )
        fig_daily.update_layout(xaxis_title=None)
        st.plotly_chart(fig_daily, use_container_width=True)

    # Hourly Plot
    with col_h:
        hourly_df = pivot_df.groupby("hour")[available_vars].mean().reset_index()
        fig_hourly = px.line(
            hourly_df, x="hour", y=available_vars,
            title="Hourly Average", labels={"value": "Avg", "variable": "Type"}
        )
        fig_hourly.update_layout(xaxis_title=None)
        st.plotly_chart(fig_hourly, use_container_width=True)

else:
    st.warning("⚠️ Please select at least one variable.")

# ───────── Anomaly Detection ───────── #
if not filtered_df.empty and available_vars:
    st.markdown('<div class="section-title">⚠️ Anomaly Detection</div>', unsafe_allow_html=True)
    fig_box = px.box(
        filtered_df[filtered_df["value_type"].isin(available_vars)],
        x="value_type", y="value",
        points="outliers", title="Outlier Detection"
    )
    fig_box.update_layout(xaxis_title=None)
    st.plotly_chart(fig_box, use_container_width=True)
else:
    st.warning("⚠️ No data available for anomaly detection.")

# Close Frame
st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.caption("Built with Streamlit and openAFRICA data")
