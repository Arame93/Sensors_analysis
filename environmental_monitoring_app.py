import streamlit as st
import pandas as pd
import plotly.express as px
import calendar

# ---------------- CONFIGURATION ----------------
st.set_page_config(layout="wide")

# ---------------- TITLE ----------------
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

# ---------------- LOAD DATA ----------------
df = pd.read_csv("Sensors_data/air_quality_data.csv")

# ---------------- PREPROCESSING ----------------
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df.dropna(subset=["timestamp", "value", "region", "value_type"], inplace=True)
df["date"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour
df["month"] = df["timestamp"].dt.month

# Rename value_type labels
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

# ---------------- FILTERS ON MAIN PAGE ----------------
with st.container():
    col1, col2 = st.columns(2)

    regions = df["region"].dropna().unique()
    selected_region = col1.selectbox("Select Region", sorted(regions), key="region_select")

    month_numbers = sorted(df["month"].dropna().unique())
    month_names = [calendar.month_name[int(m)] for m in month_numbers]
    month_mapping = dict(zip(month_names, month_numbers))
    selected_month_name = col2.selectbox("Select Month", month_names, key="month_select")
    selected_month = month_mapping[selected_month_name]

    # Variable checkboxes in 3 columns
    st.markdown("###### Select variables")
    all_vars = sorted(df["value_type"].dropna().unique())
    var_cols = st.columns(3)
    selected_vars = [var for i, var in enumerate(all_vars) if var_cols[i % 3].checkbox(var, key=f"var_{var}")]

# ---------------- FILTER DATA ----------------
filtered_df = df.copy()

if selected_region:
    filtered_df = filtered_df[filtered_df["region"] == selected_region]

if selected_month:
    filtered_df = filtered_df[filtered_df["month"] == selected_month]

if selected_vars:
    filtered_df = filtered_df[filtered_df["value_type"].isin(selected_vars)]

# DEBUG
st.write("🔍 Filtered Data Preview", filtered_df.head())
st.write("Filtered data rows:", filtered_df.shape[0])

if filtered_df.empty:
    st.warning("⚠️ No data available for the selected filters. Try adjusting your region, month, or variables.")
else:
    # Pivot
    pivot_df = filtered_df.pivot_table(
        index=["timestamp", "date", "hour"],
        columns="value_type",
        values="value",
        aggfunc="mean"
    ).reset_index()

    available_vars = [var for var in selected_vars if var in pivot_df.columns]

    # ---------------- DAILY & HOURLY PLOTS ----------------
    st.header("Daily and Hourly Trends")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Daily Average")
        if available_vars:
            daily_df = pivot_df.groupby("date")[available_vars].mean().reset_index()
            fig = px.line(
                daily_df,
                x="date",
                y=available_vars,
                title=f"Daily Average of {' + '.join(available_vars)} in {selected_region} ({selected_month_name})"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### Hourly Average")
        if available_vars:
            hourly_df = pivot_df.groupby("hour")[available_vars].mean().reset_index()
            fig_hourly = px.line(
                hourly_df,
                x="hour",
                y=available_vars,
                title=f"Hourly Average of {' + '.join(available_vars)}"
            )
            st.plotly_chart(fig_hourly, use_container_width=True)

    # ---------------- ANOMALY DETECTION ----------------
    st.header("Anomaly Detection (Boxplot)")
    fig_anomaly = px.box(
        filtered_df[filtered_df["value_type"].isin(available_vars)],
        x="value_type",
        y="value",
        title="Boxplot for Outlier Detection",
        points="outliers",
        labels={"value": "Value", "value_type": "Variable"}
    )
    st.plotly_chart(fig_anomaly, use_container_width=True)

# ---------------- REGIONAL COMPARISON (Independent) ----------------
st.header("Regional Comparison")
compare_df = df[df["value_type"].isin(selected_vars)]
region_avg = compare_df.groupby(["region", "value_type"])["value"].mean().reset_index()

if not region_avg.empty:
    fig_compare = px.bar(
        region_avg,
        x="region",
        y="value",
        color="value_type",
        barmode="group",
        title="Average Values by Region",
        labels={"value": "Average", "value_type": "Variable"}
    )
    st.plotly_chart(fig_compare, use_container_width=True)
else:
    st.warning("No regional comparison data available.")

# ---------------- PLACEHOLDER FOR WEATHER ----------------
st.header("🌦️ Weather Correlation")
st.info("Add weather data to perform correlation analysis with temperature, humidity, etc.")

# ---------------- FOOTER ----------------
st.caption("Built with Streamlit and openAFRICA data.")
