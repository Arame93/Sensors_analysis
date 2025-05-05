import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import pydeck as pdk
import io


# Main App
st.title("Environmental Mornitoring App")
path = "Sensors_data/air_quality_data.csv"
df = pd.read_csv(path)

df.value_type.replace(['P2', 'humidity','temperature','P1', 'pressure','durP1', 'durP2', 'P10'], 
         ['PM2.5','Humidity','Temperature', 'PM10','Pressure', 'durPM10', 'durPM2.5', 'PM10'], inplace=True)


df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df["date"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour

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

avg_by_day = df_filtered.groupby("date")["value"].mean().reset_index()
st.line_chart(avg_by_day.set_index("date"))

max_day = avg_by_day.loc[avg_by_day['value'].idxmax()]
st.write(f"Highest pollution day: **{max_day['date']}** with value **{max_day['value']:.2f}**")

# 2. Time Series Analysis
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
st.warning("This section requires weather data (e.g., temperature, wind speed).")

# Footer
st.caption("Built with Streamlit and openAFRICA data")
