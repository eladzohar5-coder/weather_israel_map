import pandas as pd
import folium
import requests

# 1. טעינת האקסל שלך
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

df_meta = load_excel_smart('stations_metadata.xlsx')

# 2. משיכת נתונים ממקור ה-JSON המהיר (כמו במזגל)
# המקור הזה מעדכן נתונים רגעיים ללא השהיה
url = "https://ims.gov.il/sites/default/files/ims_data/map_data/map_data-he.json"

try:
    response = requests.get(url, timeout=15)
    data = response.json()
    # הנתונים נמצאים תחת המפתח 'stns'
    stations_data = data.get('stns', [])
    print(f"Fetched {len(stations_data)} stations from JSON.")
except Exception as e:
    print(f"JSON Fetch Error: {e}")
    exit(1)

# 3. יצירת המפה
m = folium.Map(location=[32.0, 34.8], zoom_start=8)
found_count = 0

for stn in stations_data:
    try:
        # ב-JSON הזה הנתונים נמצאים במבנה שונה
        sid = int(stn.get('stn_num'))
        temp = stn.get('td') # טמפרטורה רגעית מדויקת
        
        if temp is None: continue

        # הצלבה עם האקסל המקצועי שלך
        row = df_meta[df_meta['stn_num'] == sid]
        
        if not row.empty:
            lat, lon = float(row.iloc[0]['lat']), float(row.iloc[0]['lon'])
            name = row.iloc[0]['stn_name']
            
            folium.Marker(
                [lat, lon],
                icon=folium.DivIcon(html=f"""
                    <div style="background:white; border:2px solid #2980b9; border-radius:4px; 
                    padding:2px; width:35px; text-align:center; font-size:12px; font-weight:bold;
                    box-shadow: 1px 1px 3px rgba(0,0,0,0.4); color: #2c3e50;">{temp}</div>
                """),
                popup=f"<b>{name}</b><br>טמפרטורה: {temp}°C"
            ).add_to(m)
            found_count += 1
    except:
        continue

print(f"Update finished! Added {found_count} real-time stations.")
m.save("index.html")
