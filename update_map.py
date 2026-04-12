import pandas as pd
import folium
import requests
import xml.etree.ElementTree as ET

def load_excel_smart(filename):
    # ננסה לקרוא את הקובץ ולמצוא איפה מתחילות הכותרות
    df = pd.read_excel(filename, header=None)
    
    # חיפוש השורה שבה מופיע 'stn_num'
    header_row = 0
    for i, row in df.iterrows():
        if 'stn_num' in row.values:
            header_row = i
            break
            
    # קריאה מחדש מהשורה הנכונה
    df = pd.read_excel(filename, skiprows=header_row)
    # ניקוי עמודות ריקות לחלוטין
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
    return df

# 1. טעינת האקסל
try:
    df_meta = load_excel_smart('stations_metadata.xlsx')
    print(f"Final columns identified: {df_meta.columns.tolist()}")
except Exception as e:
    print(f"Error: {e}")
    exit(1)

# 2. משיכת הנתונים
url = "https://ims.gov.il/sites/default/files/ims_data/xml_files/imslasthour.xml"
response = requests.get(url)
root = ET.fromstring(response.content)

# 3. יצירת המפה
m = folium.Map(location=[32.0, 34.8], zoom_start=8)
found_count = 0

for obs in root.findall('.//Observation'):
    try:
        sid = int(obs.find('stn_num').text)
        temp = obs.find('TD').text
        
        # חיפוש התחנה
        row = df_meta[df_meta['stn_num'] == sid]
        
        if not row.empty:
            lat, lon = float(row.iloc[0]['lat']), float(row.iloc[0]['lon'])
            name = row.iloc[0]['stn_name']
            
            folium.Marker(
                [lat, lon],
                icon=folium.DivIcon(html=f'<div style="background:white; border:2px solid blue; border-radius:50%; width:30px; height:30px; display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:bold;">{temp}</div>'),
                popup=f"{name}: {temp}°C"
            ).add_to(m)
            found_count += 1
    except:
        continue

print(f"Success! Added {found_count} stations.")
m.save("index.html")
