#fetch_weather.py_script-v2.0
#v2.0:取得項目追加

import requests
import pandas as pd
from datetime import datetime, timedelta
import os

# -----------------------------
# ① 取得する地点リスト
# -----------------------------
LOCATIONS = [
    {"name": "Tokyo", "lat": 35.6895, "lon": 139.6917},
    {"name": "Osaka", "lat": 34.6937, "lon": 135.5023},
]

# -----------------------------
# ② 昨日の日付（JST）
# -----------------------------
today = datetime.now()
yesterday = today - timedelta(days=1)
date_str = yesterday.strftime("%Y-%m-%d")

# -----------------------------
# ③ Open-Meteo 過去データ API（項目フルセット）
# -----------------------------
HOURLY_PARAMS = (
    "temperature_2m,relativehumidity_2m,windspeed_10m,"
    "surface_pressure,shortwave_radiation,cloudcover,"
    "precipitation,dewpoint_2m,apparent_temperature"
)

def fetch_weather(lat, lon, date_str):
    url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={date_str}&end_date={date_str}"
        f"&hourly={HOURLY_PARAMS}"
        "&timezone=Asia/Tokyo"
    )
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

# -----------------------------
# ④ 昨日のデータを抽出
# -----------------------------
rows = []

for loc in LOCATIONS:
    data = fetch_weather(loc["lat"], loc["lon"], date_str)
    hourly = data["hourly"]

    for t, temp, rh, ws, pres, rad, cloud, prec, dew, app in zip(
        hourly["time"],
        hourly["temperature_2m"],
        hourly["relativehumidity_2m"],
        hourly["windspeed_10m"],
        hourly["surface_pressure"],
        hourly["shortwave_radiation"],
        hourly["cloudcover"],
        hourly["precipitation"],
        hourly["dewpoint_2m"],
        hourly["apparent_temperature"],
    ):
        rows.append({
            "date": t,
            "location": loc["name"],
            "temperature": temp,
            "humidity": rh,
            "wind_speed": ws,
            "pressure": pres,
            "radiation": rad,
            "cloud_cover": cloud,
            "precipitation": prec,
            "dewpoint": dew,
            "apparent_temperature": app,
        })

df_new = pd.DataFrame(rows)

# 保存先
csv_path = "data/weather.csv"

# -----------------------------
# ⑤ 既存 CSV があれば結合
# -----------------------------
if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
    df_old = pd.read_csv(csv_path)
    df_all = pd.concat([df_old, df_new], ignore_index=True)
else:
    df_all = df_new

# -----------------------------
# ⑥ 保存
# -----------------------------
df_all.to_csv(csv_path, index=False)

print("Weather data updated:", date_str)
print("Rows collected:", len(rows))

