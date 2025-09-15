import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import streamlit as st
import branca

# Set wide page layout
st.set_page_config(layout="wide")

# Load income data
income = pd.read_csv(
    "https://raw.githubusercontent.com/pri-data/50-states/master/data/income-counties-states-national.csv",
    dtype={"fips": str},
)

# Convert income columns to numeric
income["income-2015"] = pd.to_numeric(income["income-2015"], errors="coerce")
income["income-1989a"] = pd.to_numeric(income["income-1989a"], errors="coerce")
income["income-1989b"] = pd.to_numeric(income["income-1989b"], errors="coerce")
income["income-1989"] = income[["income-1989a", "income-1989b"]].mean(axis=1)

# Compute state-level median income
state_medians = income.groupby("state").agg(medianincome=("income-2015", "median")).reset_index()

# Load GeoJSON for US states
geojson_url = "https://raw.githubusercontent.com/python-visualization/folium-example-data/main/us_states.json"
geojson_data = requests.get(geojson_url).json()

# Add median income to geojson properties
for feature in geojson_data["features"]:
    state_name = feature["properties"]["name"]
    match = state_medians[state_medians["state"] == state_name]
    feature["properties"]["medianincome"] = float(match["medianincome"]) if not match.empty else 0

# Build folium map
income_map = folium.Map(location=[37.8, -96], zoom_start=4)

# Choropleth
folium.Choropleth(
    geo_data=geojson_data,
    data=state_medians,
    columns=["state", "medianincome"],
    key_on="feature.properties.name",
    fill_color="YlGn",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Median Income 2015 (USD)"
).add_to(income_map)

# Tooltips
folium.GeoJson(
    geojson_data,
    style_function=lambda feature: {
        'fillColor': 'lightgreen',
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.7,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['name', 'medianincome'],
        aliases=['State:', 'Median Income:'],
        localize=True
    )
).add_to(income_map)

# Streamlit layout
st.markdown("<h1 style='background-color:white; padding:10px;'>US State Median Income Map</h1>", unsafe_allow_html=True)

left_col, right_col = st.columns([1, 2])

# State dropdown and county table
with left_col:
    st.subheader("Select a State")
    state_option = st.selectbox("Choose a state:", sorted(income["state"].unique()))
    
    # Filter counties for selected state
    state_counties = income[income["state"] == state_option].copy()
    
    # Compute county-level median stats
    county_table = state_counties[["county", "income-1989", "income-2015"]]
    county_medians = pd.DataFrame({
        "county": ["Median"],
        "income-1989": [state_counties["income-1989"].median()],
        "income-2015": [state_counties["income-2015"].median()]
    })
    
    # Combine
    display_table = pd.concat([county_table, county_medians], ignore_index=True)
    
    st.dataframe(display_table.style.format({"income-1989": "${:,.0f}", "income-2015": "${:,.0f}"}))

# Display map
with right_col:
    st.subheader("Interactive Map")
    st_folium(income_map, width=700, height=500)
