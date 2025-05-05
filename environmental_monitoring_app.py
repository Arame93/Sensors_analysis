import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import pydeck as pdk
import io
import seaborn as sns
import matplotlib.pyplot as plt

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

st.sidebar.header("Filters")
regions = pivot_df["region"].dropna().unique()
selected_region = st.sidebar.selectbox("Select Region", regions)
selected_month = st.sidebar.selectbox("Select Month", sorted(pivot_df["month"].dropna().unique()))
selected_variable = st.sidebar.selectbox("Select Variable", pivot_df.columns[8:])

df_filtered = pivot_df[
    (pivot_df["region"] == selected_region) &
    (pivot_df["month"] == selected_month)
]

# --- Choropleth-style Map ---
#st.subheader("Choropleth-style map by region")
region_avg = pivot_df.groupby("region")[selected_variable].mean().reset_index()

fig_map = px.choropleth(
    region_avg,
    locations="region",
    locationmode="geojson-id",  # This can be changed to 'ISO-3' or 'country names' if using global data
    color=selected_variable,
    color_continuous_scale="Viridis",
    title=f"Average {selected_variable} by Region (Approximation)"
)

st.plotly_chart(fig_map, use_container_width=True)

## --- Bubble Map by Location ---
#st.subheader("Map of sensor locations by variable level")
#location_avg = df_filtered.groupby(["lat", "lon"])[selected_variable].mean().reset_index()

#fig_bubble = px.scatter_mapbox(
    #location_avg,
    #lat="lat",
    #lon="lon",
    #color=selected_variable,
    #size=selected_variable,
    #color_continuous_scale="Plasma",
    #size_max=30,
    #zoom=8,
    #mapbox_style="open-street-map",
    #title=f"{selected_variable} at sensor locations in {selected_region} (Month {selected_month})"
#)

#st.plotly_chart(fig_bubble, use_container_width=True)

# --- Heatmap of variable by hour and day ---
st.subheader("Heatmap: Variable by hour and day")

if not df_filtered.empty:
    heatmap_data = df_filtered.pivot_table(
        index="day", columns="hour", values=selected_variable, aggfunc="mean"
    )

    # Ensure correct order for days
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(days_order)

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(heatmap_data, cmap="YlGnBu", ax=ax)
    ax.set_title(f"Heatmap of {selected_variable} by Hour and Day ({selected_region} - Month {selected_month})")
    st.pyplot(fig)
else:
    st.warning("No data available for the selected region and month.")

# Footer
st.caption("📡 Data sourced from openAFRICA | Developed with Streamlit")

'''# Main App
st.title("Environmental Mornitoring App")
path = "Sensors_data/air_quality_data.csv"
df = pd.read_csv(path)

df.value_type.replace(['P2', 'humidity','temperature','P1', 'pressure','durP1', 'durP2', 'P10'], 
         ['PM2.5','Humidity','Temperature', 'PM10','Pressure', 'durPM10', 'durPM2.5', 'PM10'], inplace=True)


df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df["date"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour
df["month"] = df["timestamp"].dt.month

# if df.empty:
#     st.error("No data loaded from API.")
# else:
#     st.success(f"Loaded {len(df)} records.")
#     st.dataframe(df.head())

#st.sidebar.header("Filters")
#selected_city = st.sidebar.selectbox("Choose a region", df["region"].unique())

#df_filtered = df[df["region"] == selected_city]

# 1. Descriptive Analysis
#st.header("Descriptive Analysis")
st.write("Average air pollution level per day")

# Pivot the data
pivot_df = df.pivot_table(
    index=["timestamp", "region", "lat", "lon", "date", "hour", "month"],
    columns="value_type",
    values="value",
    aggfunc="mean"
).reset_index()

# Select variable for map
selected_variable = st.selectbox("Select variable for choropleth", pivot_df.columns[7:])

region_avg = pivot_df.groupby("region")[selected_variable].mean().reset_index()

# Average value by location
location_avg = df_filtered.groupby(["lat", "lon"])[selected_variable].mean().reset_index()

# Set your Mapbox token (optional, but better map styles if you have one)
px.set_mapbox_access_token("your_mapbox_token_here")  # You can skip if not using custom token

# Create the "choropleth-like" bubble map
fig = px.scatter_mapbox(
    location_avg,
    lat="lat",
    lon="lon",
    color=selected_variable,
    size=selected_variable,
    color_continuous_scale="Viridis",
    size_max=30,
    zoom=5,
    title=f"Average {selected_variable} by Location",
    height=600
)

st.plotly_chart(fig)

#avg_by_day = df_filtered.groupby("date")["value"].mean().reset_index()
#st.line_chart(avg_by_day.set_index("date"))

#max_day = avg_by_day.loc[avg_by_day['value'].idxmax()]
#st.write(f"Highest pollution day: **{max_day['date']}** with value **{max_day['value']:.2f}**")


# Filter section
selected_city = st.selectbox("Select city/region", pivot_df["region"].unique())
selected_month = st.selectbox("Select month", sorted(pivot_df["month"].dropna().unique()))
selected_heatmap_var = st.selectbox("Select variable for heatmap", pivot_df.columns[7:])

# Apply filter
filtered = pivot_df[
    (pivot_df["region"] == selected_city) & (pivot_df["month"] == selected_month)
]

st.header("Geospatial Pollution Map")

# Prepare clean data
map_df = df_filtered[["lat", "lon", selected_variable]].dropna()
map_df = map_df.astype({"lat": "float", "lon": "float"})
st.write("Sample coordinates", map_df.head())
map_df["scaled_value"] = map_df[selected_variable] * 20  # Adjust scale if needed

map_df = df_filtered[["lat", "lon", selected_variable]].dropna()
map_df = map_df.groupby(["lat", "lon"])[selected_variable].mean().reset_index()
map_df = map_df.astype({"lat": "float", "lon": "float"})

# Optional: scale value for color intensity
max_val = map_df[selected_variable].max()
map_df["color"] = map_df[selected_variable] / max_val * 255  # scale to 0–255

st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state=pdk.ViewState(
        latitude=map_df["lat"].mean(),
        longitude=map_df["lon"].mean(),
        zoom=10,
        pitch=50,
    ),
    layers=[
        pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position='[lon, lat]',
            get_color='[color, 100, 100, 140]',  # Red channel varies
            get_radius=200,
            pickable=True,
        ),
    ],
))

heatmap_data = filtered.groupby(["date", "hour"])[selected_heatmap_var].mean().unstack()

# Plot heatmap
st.write(f"Hourly average of {selected_heatmap_var} in {selected_city} for month {selected_month}")
fig = px.imshow(
    heatmap_data,
    labels=dict(x="Hour", y="Date", color=selected_heatmap_var),
    aspect="auto",
    color_continuous_scale="Turbo"
)
st.plotly_chart(fig)'''

'''# 2. Time Series Analysis
st.header("Time Series Analysis")
st.write("Hourly air quality trends") 

hourly_avg = df_filtered.groupby("hour")["value"].mean().reset_index()
fig_hourly = px.line(hourly_avg, x="hour", y="value", title="Average Pollution by Hour")
st.plotly_chart(fig_hourly)

# 3. Geospatial Analysis
st.header("Geospatial Air Quality Map")
st.write("Map of pollution by location (averaged)")

map_df = df_filtered.groupby(["lat", "lon"]).agg({"value": "mean"}).reset_index()
st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state=pdk.ViewState(
        latitude=map_df["lat"].mean(),
        longitude=map_df["lon"].mean(),
        zoom=10,
        pitch=50,
    ),
    layers=[
        pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position='[lon, lat]',
            get_color='[255, 0, 0, 160]',
            get_radius=200,
        ),
    ],
))

# 4. Comparative Analysis
st.header("Comparative Analysis")
city_avg = df.groupby("region")["value"].mean().reset_index()
fig_compare = px.bar(city_avg, x="region", y="value", title="Average Air Quality by Region")
st.plotly_chart(fig_compare)

# 5. Trend Detection
st.header("Trend Detection")
rolling = df_filtered.set_index("timestamp").resample("D")["value"].mean().rolling(window=7).mean()
st.line_chart(rolling, height=300)
st.write("7-day rolling average for trend smoothing.")

# 6. Anomaly Detection
st.header("Anomaly Detection")
q3 = df_filtered["value"].quantile(0.75)
iqr = q3 - df_filtered["value"].quantile(0.25)
threshold = q3 + 1.5 * iqr
anomalies = df_filtered[df_filtered["value"] > threshold]
st.write(f"Found **{len(anomalies)}** potential pollution spikes.")
st.dataframe(anomalies[["timestamp", "value", "region"]].sort_values("value", ascending=False))

# 7. Correlation Analysis (optional if weather data exists)
st.header("🌦️ Correlation with Weather")
st.write("Load and join weather data here for advanced analysis.")
st.warning("This section requires weather data (e.g., temperature, wind speed).")'''

# Footer
st.caption("Built with Streamlit and openAFRICA data")
