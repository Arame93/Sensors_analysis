import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import calendar

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

rename_map = {
    'P2': 'PM2.5',
    'humidity': 'Humidity',
    'temperature': 'Temperature',
    'P1': 'PM10',
    'P10': 'PM10',
    'pressure': 'Pressure',
    'durP1': 'durPM10',
    'durP2': 'durPM2.5',
    'noise_Leq': 'Noise_Leq'
}
df["value_type"] = df["value_type"].replace(rename_map)

# ------------------------------
# Filter UI (Main Page Layout)
# ------------------------------
with st.container():
    st.markdown("""
        <div style='background-color:#f9f9f9; padding:20px; border:1px solid #ccc; border-radius:10px; margin-bottom:20px;'>
            <h4 style='color:#333;'>🔍 Filter Options</h4>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    regions = sorted(df["region"].dropna().unique())
    selected_region = col1.selectbox("Select Region", regions, key="region_select")

    month_numbers = sorted(df["month"].dropna().unique())
    month_names = [calendar.month_name[m] for m in month_numbers]
    month_mapping = dict(zip(month_names, month_numbers))
    selected_month_name = col2.selectbox("Select Month", month_names, key="month_select")
    selected_month = month_mapping[selected_month_name]

    st.markdown("#### Select variables to display")
    all_vars = sorted(df["value_type"].dropna().unique())
    var_cols = st.columns(3)
    selected_vars = [v for i, v in enumerate(all_vars) if var_cols[i % 3].checkbox(v, key=f"var_{v}")]

    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------
# Filter and Pivot the Data
# ------------------------------
if selected_vars:
    filtered_df = df[
        (df["region"] == selected_region) &
        (df["month"] == selected_month) &
        (df["value_type"].isin(selected_vars))
    ]

    pivot_df = filtered_df.pivot_table(
        index=["timestamp", "date", "hour"],
        columns="value_type",
        values="value",
        aggfunc="mean"
    ).reset_index()

    available_vars = [v for v in selected_vars if v in pivot_df.columns]

    # --------------------------
    # Daily & Hourly Trends
    # --------------------------
    st.header("Daily and Hourly Trends")
    col1, col2 = st.columns(2)

    with col1:
        #st.markdown("##### Daily Average")
        if not pivot_df.empty:
            daily_df = pivot_df.groupby("date")[available_vars].mean().reset_index()
            fig = px.line(
                daily_df, x="date", y=available_vars,
                title=f"Daily Averages in {selected_region} ({selected_month_name})"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        #st.markdown("##### Hourly Average")
        if not pivot_df.empty:
            hourly_df = pivot_df.groupby("hour")[available_vars].mean().reset_index()
            fig_hourly = px.line(
                hourly_df, x="hour", y=available_vars,
                title=f"Hourly Averages in {selected_region} ({selected_month_name})"
            )
            st.plotly_chart(fig_hourly, use_container_width=True)

    # --------------------------
    # Anomaly Detection
    # --------------------------
    st.header("⚠️ Anomaly Detection")
    if not filtered_df.empty:
        fig_anomaly = px.box(
            filtered_df,
            x="value_type", y="value",
            title="Outlier Detection",
            points="outliers"
        )
        # Hide x-axis title
        fig_anomaly.update_layout(
        xaxis_title=None  
        )

        st.plotly_chart(fig_anomaly, use_container_width=True)

    # --------------------------
    # Regional Comparison
    # --------------------------
    st.header("Regional Comparison")
    compare_df = df[df["value_type"].isin(selected_vars)]
    region_avg = compare_df.groupby(["region", "value_type"])["value"].mean().reset_index()
    if not region_avg.empty:
        fig_compare = px.bar(
            region_avg,
            x="region", y="value", color="value_type",
            barmode="group", title="Average Values by Region"
        )
        st.plotly_chart(fig_compare, use_container_width=True)

else:
    st.warning("Please select **at least one variable** to display analysis.")

# ------------------------------
# Weather Placeholder
# ------------------------------
st.header("🌦️ Weather Correlation")
st.info("Add weather data to perform correlation analysis with temperature, humidity, etc.")

# ------------------------------
# Footer
# ------------------------------
st.caption("Built with Streamlit and openAFRICA data")
