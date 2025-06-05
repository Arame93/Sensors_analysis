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
col1, col2 = st.columns(2)

# Ajouter "All" aux options de régions
regions = df["region"].dropna().unique()
region_options = ['All'] + sorted(regions)
selected_region = col1.selectbox("Select Region", region_options, index=0, key="region_select")

# Si "All" est sélectionné, utiliser toutes les régions
if selected_region == 'All':
    final_selected_regions = regions
else:
    final_selected_regions = [selected_region]

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
# CARTE EN PREMIÈRE POSITION
# ------------------------------
if selected_vars:
    st.markdown("""
        <style>
            .subtitle {
                background-color: #f0f0f0;
                padding: 10px;
                border-radius: 8px;
                text-align: center;
                color: #333333;
                font-size: 20px;
                font-weight: normal;
                margin-top: 10px;
                margin-bottom: 20px;
            }
        </style>
        <div class="subtitle">Geographic Visualization</div>
    """, unsafe_allow_html=True)
    
    # Utiliser la première variable sélectionnée pour la carte
    map_var = selected_vars[0]
    
    # Filtrer les données selon les filtres principaux
    map_df = df[
        (df["value_type"] == map_var) &
        (df["month"] == selected_month) &
        (df["region"].isin(final_selected_regions)) &
        (df["lat"].notna()) & (df["lon"].notna())
    ].copy()
    
    if not map_df.empty:
        map_agg = map_df.groupby(["region", "lat", "lon"])["value"].mean().reset_index()
        
        lat_center = map_agg["lat"].mean()
        lon_center = map_agg["lon"].mean()
        
        import math
        
        def calculate_zoom(lat_range, lon_range):
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
            mapbox_style="carto-positron"
        )
        
        fig_map.update_layout(
            height=600,
            margin={"r":0,"t":40,"l":0,"b":0},
            title_font_size=16,
            title_x=0.5  
        )
        
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("No geographic data available for the selected filters.")

# ------------------------------
# Filter and Pivot the Data pour les graphiques suivants
# ------------------------------
filtered_df = pd.DataFrame()
pivot_df = pd.DataFrame()
available_vars = []

if selected_vars:
    # Utiliser toutes les régions sélectionnées pour tous les graphiques
    filtered_df = df[
        (df["region"].isin(final_selected_regions)) &
        (df["month"] == selected_month) &
        (df["value_type"].isin(selected_vars))
    ]

    if not filtered_df.empty:
        pivot_df = filtered_df.pivot_table(
            index=["timestamp", "date", "hour", "region"],
            columns="value_type",
            values="value",
            aggfunc="mean"
        ).reset_index()

        available_vars = [v for v in selected_vars if v in pivot_df.columns]

# --------------------------
# Daily and Hourly Trend Charts
# --------------------------
st.markdown("""
    <style>
        .subtitle {
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            color: #333333;
            font-size: 20px;
            font-weight: normal;
            margin-top: 10px;
            margin-bottom: 20px;
        }
    </style>
    <div class="subtitle">Daily and hourly trends</div>
""", unsafe_allow_html=True)

if not pivot_df.empty:
    # Daily trends - moyenne par région et date
    daily_df = pivot_df.groupby(["date", "region"])[available_vars].mean().reset_index()
    
    # Créer un graphique avec une ligne par région
    fig = px.line(
        daily_df, x="date", y=available_vars[0] if available_vars else None,
        color="region",
        title=f"Daily Averages by Region ({selected_month_name})"
    )
    
    # Ajouter les autres variables si disponibles
    for var in available_vars[1:]:
        fig_var = px.line(daily_df, x="date", y=var, color="region")
        for trace in fig_var.data:
            trace.name = f"{trace.name} - {var}"
            fig.add_trace(trace)
    
    st.plotly_chart(fig, use_container_width=True)

    # Hourly trends with date selector
    unique_dates = pivot_df["date"].dropna().unique()
    selected_date = st.selectbox("Select a date for hourly trends", sorted(unique_dates))

    hourly_df = pivot_df[pivot_df["date"] == selected_date].groupby(["hour", "region"])[available_vars].mean().reset_index()

    fig_hourly = px.line(
        hourly_df, x="hour", y=available_vars[0] if available_vars else None,
        color="region",
        title=f"Hourly Averages on {selected_date} by Region"
    )
    
    # Ajouter les autres variables si disponibles
    for var in available_vars[1:]:
        fig_var = px.line(hourly_df, x="hour", y=var, color="region")
        for trace in fig_var.data:
            trace.name = f"{trace.name} - {var}"
            fig_hourly.add_trace(trace)
    
    st.plotly_chart(fig_hourly, use_container_width=True)
else:
    st.info("Please select variables and ensure data is available for detailed trends.")

# --------------------------
# Anomaly Detection
# --------------------------
st.markdown("""
    <style>
        .subtitle {
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            color: #333333;
            font-size: 20px;
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
        color="region",
        title="Outlier Detection by Region",
        points="outliers"
    )
    fig_anomaly.update_layout(xaxis_title=None)
    st.plotly_chart(fig_anomaly, use_container_width=True)
else:
    st.info("Not enough data to detect anomalies.")

# --------------------------
# Variables Correlation
# --------------------------
st.markdown("""
    <style>
        .subtitle {
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            color: #333333;
            font-size: 20px;
            font-weight: normal;
            margin-top: 10px;
            margin-bottom: 20px;
        }
    </style>
    <div class="subtitle">Variables Correlation</div>
""", unsafe_allow_html=True)

if available_vars and not pivot_df.empty:
    # Créer une corrélation pour chaque région
    regions_in_data = pivot_df["region"].unique()
    
    if len(available_vars) >= 2:
        for region in regions_in_data:
            region_data = pivot_df[pivot_df["region"] == region][available_vars].dropna()
            
            if len(region_data) > 1:
                corr_matrix = region_data.corr()
                fig_corr = px.imshow(
                    corr_matrix,
                    text_auto=True,
                    color_continuous_scale="RdBu_r",
                    title=f"Correlation Heatmap - {region}",
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
