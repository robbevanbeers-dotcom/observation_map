import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, FeatureGroupSubGroup
import re
from streamlit_folium import st_folium

# 1. Page Configuration
st.set_page_config(page_title="Lovenhoek Field Session", layout="wide")

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
    # Sort by time for the table
    df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    df = df.sort_values('timestamp')
    trajectory = extract_trajectory(KML_FILE)
    return df, trajectory

df, trajectory = load_all_data()

# --- APP LAYOUT ---
st.title("📍 Lovenhoek Biological Field Session")
st.markdown("Explore the trajectory and observations from the April 25th session.")

# 4. Map Section
m = folium.Map(
    location=[df.lat.mean(), df.lng.mean()], 
    zoom_start=16, max_zoom=18,
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri Satellite'
)

# Add Path & Start/End
if trajectory:
    path_layer = folium.FeatureGroup(name="Trajectory", control=False).add_to(m)
    folium.PolyLine(trajectory, color="white", weight=2, opacity=0.5, dash_array='5').add_to(path_layer)
    folium.Marker(trajectory[0], icon=folium.Icon(color='green', icon='play'), interactive=False).add_to(path_layer)
    folium.Marker(trajectory[-1], icon=folium.Icon(color='red', icon='stop'), interactive=False).add_to(path_layer)

# Species Groups & Clustering
mc = MarkerCluster(options={'showCoverageOnHover': False, 'spiderfyOnMaxZoom': True, 'disableClusteringAtZoom': 17}).add_to(m)
colors = {'Vogels': '#ff4757', 'Planten': '#2ed573', 'Reptielen en amfibieën': '#ffa502'}

for group_name, group_df in df.groupby('species group'):
    sub_group = FeatureGroupSubGroup(mc, group_name)
    m.add_child(sub_group)
    color = colors.get(group_name, '#7f8c8d')
    
    for _, row in group_df.iterrows():
        popup_html = f'<div style="font-family:Arial; width:180px;"><b style="color:{color}">{row["species name"]}</b><br><a href="{row["link"]}" target="_blank">View Record ↗</a></div>'
        folium.CircleMarker(
            location=[row['lat'], row['lng']],
            radius=6, color='white', weight=1, fill=True,
            fill_color=color, fill_opacity=0.9,
            popup=folium.Popup(popup_html, max_width=250)
        ).add_to(sub_group)

folium.LayerControl(collapsed=False).add_to(m)

# Display Map
st_folium(m, width=1400, height=600, returned_objects=[])

# 5. Observation List Section (Simplified Data Table)
st.divider()
st.subheader("📋 Observation List")

# We create a simplified version of the dataframe for display
# We use st.column_config to make the 'link' column a clickable button
display_df = df[['time', 'species name', 'scientific name', 'species group', 'number', 'link']].copy()

st.dataframe(
    display_df,
    column_config={
        "time": "Time",
        "species name": "Common Name",
        "scientific name": "Scientific Name",
        "species group": "Group",
        "number": "Count",
        "link": st.column_config.LinkColumn("Observation Link")
    },
    hide_index=True,
    use_container_width=True
)
