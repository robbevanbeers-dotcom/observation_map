import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, FeatureGroupSubGroup
import re
from streamlit_folium import st_folium

# Basic page config
st.set_page_config(page_title="Lovenhoek Observation Map", layout="wide")


# 1. Helper to extract the trajectory line from your KML
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
    except:
        return []


# 2. Hardcoded File Loading (Baking the data in)
EXCEL_FILE = 'observation-2026-04-25-18-38-sessie-2026-04-25-271055.xlsx'
KML_FILE = 'observation-2026-04-27-09-42-sessie-2026-04-25-271055.kml'


@st.cache_data  # This makes the map load faster for visitors
def load_data():
    df = pd.read_excel(EXCEL_FILE)
    trajectory = extract_trajectory(KML_FILE)
    return df, trajectory


df, trajectory = load_data()

# 3. Create the Folium Map
m = folium.Map(
    location=[df.lat.mean(), df.lng.mean()],
    zoom_start=16, max_zoom=18,
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri Satellite'
)

# Add Path
if trajectory:
    path_layer = folium.FeatureGroup(name="Path", control=False).add_to(m)
    folium.PolyLine(trajectory, color="white", weight=2, opacity=0.5, dash_array='5').add_to(path_layer)
    folium.Marker(trajectory[0], icon=folium.Icon(color='green', icon='play'), interactive=False).add_to(path_layer)
    folium.Marker(trajectory[-1], icon=folium.Icon(color='red', icon='stop'), interactive=False).add_to(path_layer)

# 4. Marker Clustering & Species Groups
mc = MarkerCluster(
    options={'showCoverageOnHover': False, 'spiderfyOnMaxZoom': True, 'disableClusteringAtZoom': 17}).add_to(m)
colors = {'Vogels': '#ff4757', 'Planten': '#2ed573', 'Reptielen en amfibieën': '#ffa502'}

for group_name, group_df in df.groupby('species group'):
    sub_group = FeatureGroupSubGroup(mc, group_name)
    m.add_child(sub_group)
    color = colors.get(group_name, '#7f8c8d')

    for _, row in group_df.iterrows():
        popup_html = f'<div style="font-family:Arial; width:180px;"><b style="color:{color}">{row["species name"]}</b><br><a href="{row["link"]}" target="_blank">View on Waarnemingen.be ↗</a></div>'
        folium.CircleMarker(
            location=[row['lat'], row['lng']],
            radius=6, color='white', weight=1, fill=True,
            fill_color=color, fill_opacity=0.9,
            popup=folium.Popup(popup_html, max_width=250)
        ).add_to(sub_group)

folium.LayerControl(collapsed=False).add_to(m)

# 5. Display the Map
st.title("📍 Lovenhoek Field Session Map")
st_folium(m, width=1400, height=800, returned_objects=[])
