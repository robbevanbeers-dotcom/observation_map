import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, FeatureGroupSubGroup
import re
from streamlit_folium import st_folium

st.set_page_config(page_title="Bio Observation Mapper", layout="wide")

st.title("🌿 Biological Session Mapper")
st.write("Upload your Excel and KML files to generate your interactive field map.")

# 1. File Uploaders
col1, col2 = st.columns(2)
with col1:
    excel_file = st.file_uploader("Upload Observations (.xlsx)", type=['xlsx'])
with col2:
    kml_file = st.file_uploader("Upload Trajectory (.kml)", type=['kml'])


# Helper function for KML
def extract_trajectory(kml_content):
    all_matches = re.findall(r'<coordinates>(.*?)</coordinates>', kml_content, re.DOTALL)
    paths = []
    for match in all_matches:
        points = [[float(p.split(',')[1]), float(p.split(',')[0])] for p in match.strip().split() if ',' in p]
        if len(points) > 1: paths.append(points)
    return max(paths, key=len) if paths else []


if excel_file and kml_file:
    df = pd.read_excel(excel_file)
    kml_data = kml_file.getvalue().decode("utf-8")

    # Create Map
    m = folium.Map(
        location=[df.lat.mean(), df.lng.mean()],
        zoom_start=16, max_zoom=18,
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri Satellite'
    )

    # Add Path
    trajectory = extract_trajectory(kml_data)
    if trajectory:
        path_layer = folium.FeatureGroup(name="Trajectory", control=False).add_to(m)
        folium.PolyLine(trajectory, color="white", weight=2, opacity=0.5, dash_array='5').add_to(path_layer)
        folium.Marker(trajectory[0], icon=folium.Icon(color='green', icon='play'), interactive=False).add_to(path_layer)
        folium.Marker(trajectory[-1], icon=folium.Icon(color='red', icon='stop'), interactive=False).add_to(path_layer)

    # Add Species
    mc = MarkerCluster(
        options={'showCoverageOnHover': False, 'spiderfyOnMaxZoom': True, 'disableClusteringAtZoom': 17}).add_to(m)
    colors = {'Vogels': '#ff4757', 'Planten': '#2ed573', 'Reptielen en amfibieën': '#ffa502'}

    for group_name, group_df in df.groupby('species group'):
        sub_group = FeatureGroupSubGroup(mc, group_name)
        m.add_child(sub_group)
        color = colors.get(group_name, '#7f8c8d')

        for _, row in group_df.iterrows():
            popup_html = f'<div style="font-family:Arial; width:180px;"><b style="color:{color}">{row["species name"]}</b><br><a href="{row["link"]}" target="_blank">Link ↗</a></div>'
            folium.CircleMarker(
                location=[row['lat'], row['lng']],
                radius=6, color='white', weight=1, fill=True,
                fill_color=color, fill_opacity=0.9,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(sub_group)

    folium.LayerControl(collapsed=False).add_to(m)

    # Display Map in Streamlit
    st_folium(m, width=1200, height=700)
else:
    st.info("Waiting for both files to be uploaded...")