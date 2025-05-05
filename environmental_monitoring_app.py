import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import calendar


# Page setup
st.set_page_config(layout="wide")
st.title("Environmental Monitoring App")

# Load data
path = "Sensors_data/air_quality_data.csv"
df = pd.read_csv(path)

# Preprocessing
df.value_type = df.value_type.replace(
    ['P2', 'humidity', 'temperature', 'P1', 'pressure', 'durP1', 'durP2', 'P10'],
    ['PM2.5', 'Humidity', 'Temperature', 'PM10', 'Pressure', 'durPM10', 'durPM2.5', 'PM10']
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

# Sidebar filters
st.sidebar.header("Filters")

# Region select (single)
regions = pivot_df["region"].dropna().unique()
selected_region = st.sidebar.selectbox("Select Region", regions)

# Convert month numbers to names
month_numbers = sorted(pivot_df["month"].dropna().unique())
month_names = [calendar.month_name[int(m)] for m in month_numbers]
month_mapping = dict(zip(month_names, month_numbers))

selected_month_name = st.sidebar.selectbox("Select Month", month_names)
selected_month = month_mapping[selected_month_name]

# Multiselect for variables (displayed as checkboxes)
variable_options = list(pivot_df.columns[8:])
cols = st.sidebar.columns(3)  # Creates 3 buttons per row
selected_vars = []
for i, var in enumerate(variable_options):
    if cols[i % 3].checkbox(var):
        selected_vars.append(var)

# If no variables selected, show a message
if not selected_vars:
    st.warning("Please select at least one variable for the map.")

# Get data for the selected variables
if selected_vars:
    # Aggregated by region for selected variables
    selected_df = pivot_df.groupby("region")[selected_vars].mean().reset_index()

    # Drop rows where all selected variables are NaN
    selected_df = selected_df.dropna(subset=selected_vars)

    # Load GeoJSON data for regions (make sure you have a geojson file with region boundaries)
    # This could be a local file or fetched from an API
    with open("Sensors_data/map.geojson") as f:
        geojson = json.load(f)

    # Now create the choropleth map using Plotly
    fig = go.Figure(go.Choropleth(
        z=selected_df[selected_vars[0]],  # use the first selected variable
        hoverinfo='location+z',  # show region and value
        locations=selected_df["region"],  # map the regions
        locationmode='geojson-id',  # reference to geojson id
        geojson=geojson,  # Use the GeoJSON boundary file
        colorscale="Viridis",  # Color scheme for the regions
        colorbar_title=selected_vars[0],  # Add a colorbar title
    ))

    fig.update_layout(
        geo=dict(
            visible=True,
            lakecolor='rgb(255, 255, 255)',  # Optional: Set background color of the map
            projection_type='mercator',  # Optional: Set the map projection type
        ),
        title=f"Average {selected_vars[0]} by Region",  # Title based on the selected variable
    )

    # Plot the figure in Streamlit
    st.plotly_chart(fig)
