import pandas as pd
import folium
import requests
import xml.etree.ElementTree as ET

def load_excel_smart(filename):
    try:
        df = pd.read_excel(filename, header=None)
        header_row = 0
        for i, row in df.iterrows():
            if 'stn_num' in row.values:
                header_row = i
                break
        df = pd.read_excel(filename, skiprows=header_row)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
        return df
    except Exception as e:
        print(f"Excel error: {e}")
        return None

# 1. טעינת אקסל
df_meta = load_excel_smart('stations_metadata.xlsx')

# 2. משיכת נתונים מכתובת ה-XML הכי אמינה ופתוחה
url = "https://ims.gov.il/sites/default/files/ims_data/xml_files/imslasthour.xml"

try:
    # אנחנו משתמשים ב-Session כדי לשמור על חיבור יציב
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    response = session.get(url, timeout=20)
    root = ET.fromstring(response.content)
    print(f"Successfully connected to IMS data.")
except Exception as e:
    print(f"Connection Error: {e}")
    exit(1)

# 3. יצירת מפה
m = folium.Map(location=[32.0, 34.8], zoom_start=8)
found_count = 0

for station in root.findall('.//Observation'):
    try:
        sid_el = station.find('stn_num')
        td_el = station.find('TD')
        
        if sid_el is not None and td_el is not None:
            sid = int(sid_el.text)
            temp = td_el.text.strip()
            
            row = df_meta[df_meta['stn_num'] == sid]
            if not row.empty:
                lat, lon = float(row.iloc[0]['lat']), float(row.iloc[0]['lon'])
                name = row.iloc[0]['stn_name']
                
                folium.Marker(
                    [lat, lon],
                    icon=folium.DivIcon(html=f"""
                        <div style="background:white; border:2px solid #2980b9; border-radius:4px; 
                        padding:2px; width:35px; text-align:center; font-size:12px; font-weight:bold;
                        box-shadow: 1px 1px 3px rgba(0,0,0,0.4);">{temp}</div>
                    """),
                    popup=f"<b>{name}</b><br>טמפרטורה: {temp}°C"
                ).add_to(m)
                found_count += 1
    except:
        continue

print(f"Success! Added {found_count} stations.")
m.save("index.html")
