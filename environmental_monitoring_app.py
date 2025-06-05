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
# Map of Selected Variable by Region (moved under Regional Comparison)
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
    <div class="subtitle">Map by Region</div>
""", unsafe_allow_html=True)
if selected_vars:
    map_var = st.selectbox("Select variable to show on the map", selected_vars, key="map_var_final")

    map_df = df[
        (df["value_type"] == map_var) &
        (df["month"] == selected_month) &
        (df["lat"].notna()) & (df["lon"].notna())
    ].copy()

if not map_df.empty:
    map_agg = map_df.groupby(["region", "lat", "lon"])["value"].mean().reset_index()
    
    # Créer une carte Folium avec OpenStreetMap
    lat_center = map_agg["lat"].mean()
    lon_center = map_agg["lon"].mean()
    
    m = folium.Map(
        location=[lat_center, lon_center],
        zoom_start=6,
        tiles='OpenStreetMap'  # OpenStreetMap direct !
    )
    
    # Ajouter les points
    for _, row in map_agg.iterrows():
        # Taille du cercle basée sur la valeur
        radius = row['value'] / map_agg['value'].max() * 20 + 5
        
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=radius,
            popup=f"{row['region']}: {row['value']:.2f}",
            color='red',
            fill=True,
            fillColor='red',
            fillOpacity=0.6
        ).add_to(m)
    
    # Afficher dans Streamlit
    st_folium(m, width=700, height=500)

# Solution 2: Pydeck avec OpenStreetMap
import pydeck as pdk

if not map_df.empty:
    map_agg = map_df.groupby(["region", "lat", "lon"])["value"].mean().reset_index()
    
    # Normaliser les valeurs
    map_agg["normalized_value"] = (map_agg["value"] - map_agg["value"].min()) / (map_agg["value"].max() - map_agg["value"].min())
    
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_agg,
        get_position=["lon", "lat"],
        get_radius="normalized_value * 2000 + 500",
        get_color="[255, 0, 0, 180]",  # Rouge
        pickable=True,
    )
    
    view_state = pdk.ViewState(
        latitude=map_agg["lat"].mean(),
        longitude=map_agg["lon"].mean(),
        zoom=6,
        pitch=0,
    )
    
    # Pydeck utilise automatiquement OpenStreetMap !
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "Region: {region}\nValue: {value}"},
        map_style="road"  # Style route basé sur OSM
    )
    
    st.pydeck_chart(deck)

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
