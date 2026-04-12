import pandas as pd
import folium
import requests
import xml.etree.ElementTree as ET

# 1. פונקציית טעינת אקסל נשארת זהה
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
    except: return None

df_meta = load_excel_smart('stations_metadata.xlsx')

# 2. משיכת הקובץ
url = "https://ims.gov.il/sites/default/files/ims_data/xml_files/imslasthour.xml"
try:
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, timeout=20)
    root = ET.fromstring(response.content)
except Exception as e:
    print(f"Error: {e}")
    exit(1)

# 3. מנגנון בחירת הנתון העדכני ביותר לכל תחנה
latest_data = {} # כאן נשמור רק את השורה הכי חדשה לכל ID

for obs in root.findall('.//Observation'):
    try:
        sid = int(obs.find('stn_num').text)
        time_str = obs.find('time_obs').text # למשל 2026-04-12T15:50:00
        temp = obs.find('TD').text
        
        if temp is None or temp == "": continue
        
        # אם התחנה עוד לא קיימת במילון, או שהזמן הנוכחי חדש יותר ממה ששמרנו
        if sid not in latest_data or time_str > latest_data[sid]['time']:
            latest_data[sid] = {
                'temp': temp,
                'time': time_str
            }
    except: continue

# 4. יצירת המפה עם הנתונים המנופים
m = folium.Map(location=[32.0, 34.8], zoom_start=8)
found_count = 0

for sid, info in latest_data.items():
    row = df_meta[df_meta['stn_num'] == sid]
    if not row.empty:
        lat, lon = float(row.iloc[0]['lat']), float(row.iloc[0]['lon'])
        name = row.iloc[0]['stn_name']
        
        folium.Marker(
            [lat, lon],
            icon=folium.DivIcon(html=f"""
                <div style="background:white; border:2px solid #2c3e50; border-radius:4px; 
                padding:2px; width:35px; text-align:center; font-size:12px; font-weight:bold;
                box-shadow: 1px 1px 3px rgba(0,0,0,0.4);">{info['temp']}</div>
            """),
            popup=f"<b>{name}</b><br>טמפרטורה: {info['temp']}°C<br>זמן (UTC): {info['time']}"
        ).add_to(m)
        found_count += 1

print(f"Cleaned up! Showing {found_count} most recent observations.")
m.save("index.html")
