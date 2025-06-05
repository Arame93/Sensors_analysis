import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import calendar
from streamlit_plotly_events import plotly_events
import folium
from streamlit_folium import st_folium

# ------------------------------
# Page Setup and Title Styling
# ------------------------------
st.set_page_config(layout="wide")
#layout="wide"

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
df = df[df.region != 'usman'].copy()
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
#st.subheader("Filters")
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
# Map of Selected Variable by Region
# --------------------------
if selected_vars:
    map_var = st.selectbox("Select variable to show on the map", selected_vars, key="map_var_final")
    map_df = df[
        (df["value_type"] == map_var) &
        (df["month"] == selected_month) &
        (df["lat"].notna()) & (df["lon"].notna())
    ].copy()
    
    if not map_df.empty:
    map_agg = map_df.groupby(["region", "lat", "lon"])["value"].mean().reset_index()


    lat_center = map_agg["lat"].mean()
    lon_center = map_agg["lon"].mean()
    
    import math
    
    def calculate_zoom(lat_range, lon_range):
        # Formule approximative pour calculer le zoom optimal
        max_range = max(lat_range, lon_range)
        if max_range == 0:
            return 10
        zoom = math.log2(360 / max_range) - 1
        return max(1, min(15, int(zoom)))  
    
    lat_range = map_agg["lat"].max() - map_agg["lat"].min()
    lon_range = map_agg["lon"].max() - map_agg["lon"].min()
    
    lat_range *= 1.2
    lon_range *= 1.2
    
    zoom_level = calculate_zoom(lat_range, lon_range)

    fig_map = px.scatter_mapbox(
        map_agg,
        lat="lat",
        lon="lon",
        size="value",
        color="value",
        color_continuous_scale="Reds",  
        size_max=20,
        zoom=zoom_level,
        center={"lat": lat_center, "lon": lon_center},
        hover_name="region",
        hover_data={"value": ":.2f"},  
        title=f"{map_var} - Average Values by Region ({selected_month_name})",
        #mapbox_style="carto-darkmatter"
        mapbox_style="carto-positron"
    )
    
    fig_map.update_layout(
        height=600,
        margin={"r":0,"t":40,"l":0,"b":0},
        title_font_size=16,
        title_x=0.5  
    )
    
    st.plotly_chart(fig_map, use_container_width=True)
# --------------------------
# Daily and Hourly Trend Charts
# --------------------------
# daily plot with click interaction
#st.header("Daily trends")
st.markdown("""
    <style>
        .subtitle {
            background-color: #f0f0f0;  /* light grey */
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            color: #333333;  /* dark grey text */
            font-size: 20px;  /* smaller font size */
            font-weight: normal;
            margin-top: 10px;
            margin-bottom: 20px;
        }
    </style>
    <div class="subtitle">Daily and hourly trends</div>
""", unsafe_allow_html=True)

#st.header("Daily and hourly trends")
#col1, col2 = st.columns(2)

# --- Left Column: Daily Trend Chart ---
#with col1:
if not pivot_df.empty:
    daily_df = pivot_df.groupby("date")[available_vars].mean().reset_index()
    fig = px.line(
        daily_df, x="date", y=available_vars,
        title=f"Daily Averages in {selected_region} ({selected_month_name})"
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Right Column: Hourly Trend Chart with Date Selector ---
#with col2:
if not pivot_df.empty:
    # Add a date selector based on available dates
    unique_dates = pivot_df["date"].dropna().unique()
    selected_date = st.selectbox("Select a date for hourly trends", sorted(unique_dates))

    # Filter and plot hourly data for selected date
    hourly_df = pivot_df[pivot_df["date"] == selected_date].groupby("hour")[available_vars].mean().reset_index()

    fig_hourly = px.line(
        hourly_df, x="hour", y=available_vars,
        title=f"Hourly Averages on {selected_date}"
    )
    st.plotly_chart(fig_hourly, use_container_width=True)

        
# --------------------------
# Anomaly Detection
# --------------------------
#st.subheader("Anomaly Detection")
st.markdown("""
    <style>
        .subtitle {
            background-color: #f0f0f0;  /* light grey */
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            color: #333333;  /* dark grey text */
            font-size: 20px;  /* smaller font size */
            font-weight: normal;
            margin-top: 10px;
            margin-bottom: 20px;
        }
    </style>
    <div class="subtitle">Anomaly Detection</div>
""", unsafe_allow_html=True)

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
#st.subheader("Regional Comparison")
#st.markdown("""
    #<style>
        #subtitle {
           # background-color: #f0f0f0;  /* light grey */
            #padding: 10px;
            #border-radius: 8px;
            #text-align: center;
            #color: #333333;  /* dark grey text */
            #font-size: 20px;  /* smaller font size */
            #font-weight: normal;
            #margin-top: 10px;
            #margin-bottom: 20px;
    #    }
    #</style>
    #<div class="subtitle">Regional Comparison</div> , unsafe_allow_html=True)

#compare_df = df[df["value_type"].isin(selected_vars)]

#if not compare_df.empty:
 #   region_avg = compare_df.groupby(["region", "value_type"])["value"].mean().reset_index()
  #  fig_compare = px.bar(
   #     region_avg,
    #    x="region", y="value", color="value_type",
     #   barmode="group", title="Average Values by Region"
    #)
    #st.plotly_chart(fig_compare, use_container_width=True)
#else:
    st.info("No data available for regional comparison.")



# --------------------------
# Weather Correlation
# --------------------------
#st.subheader("🌦️ Weather Correlation")
st.markdown("""
    <style>
        .subtitle {
            background-color: #f0f0f0;  /* light grey */
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            color: #333333;  /* dark grey text */
            font-size: 20px;  /* smaller font size */
            font-weight: normal;
            margin-top: 10px;
            margin-bottom: 20px;
        }
    </style>
    <div class="subtitle"> Variables Correlation</div>
""", unsafe_allow_html=True)


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
