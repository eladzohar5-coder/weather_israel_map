import pandas as pd
import folium
import requests
import xml.etree.ElementTree as ET

def load_excel_smart(filename):
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

# 1. טעינת האקסל
try:
    df_meta = load_excel_smart('stations_metadata.xlsx')
except Exception as e:
    print(f"Excel Error: {e}")
    exit(1)

# 2. משיכת נתונים רגעיים (Synop) - המקור המדויק יותר
url = "https://ims.gov.il/sites/default/files/ims_data/xml_files/imssynop.xml"
try:
    response = requests.get(url)
    root = ET.fromstring(response.content)
except Exception as e:
    print(f"XML Fetch Error: {e}")
    exit(1)

# 3. יצירת המפה
m = folium.Map(location=[32.0, 34.8], zoom_start=8)
found_count = 0

# חיפוש נתונים בתוך מבנה ה-Synop
for station in root.findall('.//Station'):
    try:
        sid = int(station.find('stn_num').text)
        # ב-Synop הפרמטר המדויק לטמפרטורה עכשיו הוא בדרך כלל TD
        temp_element = station.find('.//TD')
        if temp_element is None or temp_element.text is None:
            continue
            
        temp = temp_element.text
        
        # הצלבה עם האקסל המקצועי שלך
        row = df_meta[df_meta['stn_num'] == sid]
        
        if not row.empty:
            lat, lon = float(row.iloc[0]['lat']), float(row.iloc[0]['lon'])
            name = row.iloc[0]['stn_name']
            
            # עיצוב מקצועי יותר לסמן
            folium.Marker(
                [lat, lon],
                icon=folium.DivIcon(html=f"""
                    <div style="
                        background-color: white; 
                        border: 2px solid #e67e22; 
                        border-radius: 4px; 
                        padding: 2px;
                        width: 32px; 
                        text-align: center;
                        font-size: 12px; 
                        font-weight: bold;
                        box-shadow: 1px 1px 3px rgba(0,0,0,0.5);
                    ">{temp}</div>
                """),
                popup=f"<b>{name}</b><br>טמפרטורה: {temp}°C"
            ).add_to(m)
            found_count += 1
    except:
        continue

print(f"Accuracy Update: Added {found_count} stations from Synop data.")
m.save("index.html")
