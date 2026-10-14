#fetch_weather.py_script-v3
#v2.0:取得項目追加
#v2.1:取得項目追加＋重複行の自動削除（最新行を残す）
#v3: JST固定＋過去2日分取得＋重複削除（最新行を残す）

import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import os

# -----------------------------
# ① JST の現在日付
# -----------------------------
JST = timezone(timedelta(hours=9))
today = datetime.now(JST).date()

# 過去2日分を取得（例：10/14 と 10/13）
start_date = today - timedelta(days=2)
end_date = today - timedelta(days=1)

start_str = start_date.strftime("%Y-%m-%d")
end_str = end_date.strftime("%Y-%m-%d")

# -----------------------------
# ② 取得する地点リスト
# -----------------------------
LOCATIONS = [
    {"name": "Tokyo", "lat": 35.6895, "lon": 139.6917},
    {"name": "Osaka", "lat": 34.6937, "lon": 135.5023},
]

# -----------------------------
# ③ Open-Meteo 過去データ API（項目フルセット）
# -----------------------------
HOURLY_PARAMS = (
    "temperature_2m,relativehumidity_2m,windspeed_10m,"
    "surface_pressure,shortwave_radiation,cloudcover,"
    "precipitation,dewpoint_2m,apparent_temperature"
)

def fetch_weather(lat, lon, start_str, end_str):
    url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={start_str}&end_date={end_str}"
        f"&hourly={HOURLY_PARAMS}"
        "&timezone=Asia/Tokyo"
    )
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

# -----------------------------
# ④ 過去2日分のデータを抽出
# -----------------------------
rows = []

for loc in LOCATIONS:
    data = fetch_weather(loc["lat"], loc["lon"], start_str, end_str)
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
# ⑥ 重複行の削除（同じ日時＋地点は最新行だけ残す）
# -----------------------------
df_all = df_all.sort_values(by=["date", "location"])
df_all = df_all.drop_duplicates(subset=["date", "location"], keep="last")

# -----------------------------
# ⑦ 保存
# -----------------------------
df_all.to_csv(csv_path, index=False)

print("Weather data updated:", start_str, "to", end_str)
print("Rows collected:", len(rows))
