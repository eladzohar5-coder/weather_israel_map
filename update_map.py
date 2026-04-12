import pandas as pd
import folium
import requests
import xml.etree.ElementTree as ET

# 1. טעינת האקסל וטיפול בעמודות ריקות
try:
    # קוראים את האקסל
    df_meta = pd.read_excel('stations_metadata.xlsx', engine='openpyxl')
    
    # מסירים עמודות שאין להן שם (עמודות ריקות מצד שמאל)
    df_meta = df_meta.loc[:, ~df_meta.columns.str.contains('^Unnamed')]
    
    # אם עדיין יש עמודות ריקות שפנדס לא זיהה, ננקה אותן
    df_meta = df_meta.dropna(how='all', axis=1).dropna(how='all', axis=0)
    
    print("Excel loaded and cleaned!")
    print(f"Final columns: {df_meta.columns.tolist()}")
except Exception as e:
    print(f"Error loading Excel: {e}")
    exit(1)

# 2. משיכת הנתונים מהשירות המטאורולוגי
url = "https://ims.gov.il/sites/default/files/ims_data/xml_files/imslasthour.xml"
try:
    response = requests.get(url)
    root = ET.fromstring(response.content)
except Exception as e:
    print(f"Error fetching XML: {e}")
    exit(1)

# 3. יצירת המפה
m = folium.Map(location=[32.0, 34.8], zoom_start=8)

found_count = 0

for obs in root.findall('.//Observation'):
    try:
        sid = int(obs.find('stn_num').text)
        temp = obs.find('TD').text
        
        # חיפוש התחנה באקסל המנקה
        row = df_meta[df_meta['stn_num'] == sid]
        
        if not row.empty:
            lat = float(row.iloc[0]['lat'])
            lon = float(row.iloc[0]['lon'])
            name = row.iloc[0]['stn_name']
            
            # יצירת סמן עם הטמפרטורה
            folium.Marker(
                [lat, lon],
                icon=folium.DivIcon(html=f"""
                    <div style="
                        background-color: white; 
                        border: 2px solid #2c3e50; 
                        border-radius: 50%; 
                        width: 30px; 
                        height: 30px; 
                        display: flex; 
                        align-items: center; 
                        justify-content: center; 
                        font-size: 11px; 
                        font-weight: bold;
                        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
                    ">{temp}</div>
                """),
                popup=f"<b>{name}</b><br>טמפרטורה: {temp}°C"
            ).add_to(m)
            found_count += 1
    except:
        continue

print(f"Successfully added {found_count} stations to the map.")
m.save("index.html")
