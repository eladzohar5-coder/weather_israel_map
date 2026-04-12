import pandas as pd
import folium
import requests
import xml.etree.ElementTree as ET

# טעינת האקסל
df_meta = pd.read_excel('stations_metadata.xlsx')

# משיכת ה-XML מהשירות המטאורולוגי
url = "https://ims.gov.il/sites/default/files/ims_data/xml_files/imslasthour.xml"
response = requests.get(url)
root = ET.fromstring(response.content)

# יצירת מפה
m = folium.Map(location=[32.0, 34.8], zoom_start=8)

# חיבור הנתונים
for obs in root.findall('.//Observation'):
    try:
        sid = int(obs.find('stn_num').text)
        temp = obs.find('TD').text
        
        row = df_meta[df_meta['stn_num'] == sid]
        if not row.empty:
            lat, lon = row.iloc[0]['lat'], row.iloc[0]['lon']
            name = row.iloc[0]['stn_name']
            
            folium.Marker(
                [lat, lon], 
                popup=f"{name}: {temp}C",
                icon=folium.DivIcon(html=f'<div style="font-weight:bold; color:blue;">{temp}</div>')
            ).add_to(m)
    except:
        continue

m.save("index.html")
