import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, FeatureGroupSubGroup
import re
from streamlit_folium import st_folium

# 1. Page Configuration
st.set_page_config(page_title="Lovenhoek Excursie", layout="wide")

# 2. Helper: Extract trajectory from KML
def extract_trajectory(kml_path):
    try:
        with open(kml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        all_matches = re.findall(r'<coordinates>(.*?)</coordinates>', content, re.DOTALL)
        paths = []
        for match in all_matches:
            points = [[float(p.split(',')[1]), float(p.split(',')[0])] for p in match.strip().split() if ',' in p]
            if len(points) > 1: paths.append(points)
        return max(paths, key=len) if paths else []
    except: return []

# 3. Load Data
EXCEL_FILE = 'observation-2026-04-25-18-38-sessie-2026-04-25-271055.xlsx'
KML_FILE = 'observation-2026-04-27-09-42-sessie-2026-04-25-271055.kml'

@st.cache_data
def load_all_data():
    df = pd.read_excel(EXCEL_FILE)
    df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    df = df.sort_values('timestamp')
    trajectory = extract_trajectory(KML_FILE)
    return df, trajectory

df, trajectory = load_all_data()

# --- APP LAYOUT ---
st.title("📍 Lovenhoek - Excursie voorjaarsbloeiers")

# 4. Map Section
# Fix for Point 3: Use use_container_width=True and fit_bounds
m = folium.Map(
    location=[df.lat.mean(), df.lng.mean()], 
    zoom_start=15, 
    max_zoom=19,
    tiles='OpenStreetMap'
)

# Add Path & Start/End
if trajectory:
    path_layer = folium.FeatureGroup(name="Trajectory", control=False).add_to(m)
    folium.PolyLine(trajectory, color="#3498db", weight=4, opacity=0.8, dash_array='5').add_to(path_layer)
    folium.Marker(trajectory[0], icon=folium.Icon(color='green', icon='play'), interactive=False).add_to(path_layer)
    folium.Marker(trajectory[-1], icon=folium.Icon(color='red', icon='stop'), interactive=False).add_to(path_layer)
    # Ensure the map fits the whole track on start (Good for mobile)
    m.fit_bounds(trajectory)

# Fix for Point 1: Distinct Colors
# Changed Birds to a vibrant blue and Reptiles to a bright orange
colors = {
    'Vogels': '#0077b6',                # Deep Ocean Blue
    'Planten': '#2d6a4f',               # Forest Green
    'Reptielen en amfibieën': '#f3722c'  # Bright Orange
}

# Fix for Point 2: Zoom-dependent labels
# We use a Tooltip with 'permanent=True' and a CSS trick to hide it at low zoom levels
label_css = """
<style>
    .leaflet-tooltip.zoom-label {
        background: transparent;
        border: none;
        box-shadow: none;
        font-weight: bold;
        color: #2c3e50;
        text-shadow: 1px 1px 1px #fff;
        font-size: 12px;
    }
    /* Hide labels when zoom is less than 17 */
    .leaflet-zoom-animated:not(.leaflet-zoom-17):not(.leaflet-zoom-18):not(.leaflet-zoom-19) .zoom-label {
        display: none;
    }
</style>
"""
m.get_root().header.add_child(folium.Element(label_css))

mc = MarkerCluster(options={'showCoverageOnHover': False, 'spiderfyOnMaxZoom': True, 'disableClusteringAtZoom': 17}).add_to(m)

for group_name, group_df in df.groupby('species group'):
    sub_group = FeatureGroupSubGroup(mc, group_name)
    m.add_child(sub_group)
    color = colors.get(group_name, '#7f8c8d')
    
    for _, row in group_df.iterrows():
        popup_html = f'<div style="font-family:Arial; width:180px;"><b style="color:{color}">{row["species name"]}</b><br><a href="{row["link"]}" target="_blank">View Record ↗</a></div>'
        
        folium.CircleMarker(
            location=[row['lat'], row['lng']],
            radius=7, 
            color='#ffffff', 
            weight=2,        
            fill=True,
            fill_color=color, 
            fill_opacity=1.0,
            popup=folium.Popup(popup_html, max_width=250),
            # This tooltip becomes visible when zooming in
            tooltip=folium.Tooltip(row["species name"], permanent=True, direction='top', className="zoom-label")
        ).add_to(sub_group)

folium.LayerControl(collapsed=False).add_to(m)

# Fix for Point 3: Sizing
# Removed fixed width=1400. use_container_width=True makes it responsive on phones.
st_folium(m, use_container_width=True, height=500, returned_objects=[])

# 5. Observation List
st.divider()
st.subheader("📋 Lijst met observaties")

display_df = df[['time', 'species name', 'scientific name', 'species group', 'number', 'link']].copy()
st.dataframe(
    display_df,
    column_config={
        "time": "Tijd",
        "species name": "Naam",
        "scientific name": "Wetenschappelijk",
        "species group": "Groep",
        "link": st.column_config.LinkColumn("Link")
    },
    hide_index=True,
    use_container_width=True
)
