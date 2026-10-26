#fetch_weather.py_script-v3.6
#v2.0:取得項目追加
#v2.1:取得項目追加＋重複行の自動削除（最新行を残す）
#v3.0: JST固定＋過去2日分取得＋重複削除（最新行を残す）
#v3.1: 525日より古いデータを自動削除（DRP01長期運用対応）
#v3.2: date列の混在フォーマットを format='mixed' で完全吸収（安定版）
#v3.3: v3.2の不具合修正　時間軸が日付化　→　日時に修正(Time Stamp 保持)
#v3.4: date format をISO8601に修正（DRP02とともに統一）
#v3.5: pandasの処理エラー解消のためthreshold_date を ISO8601 の「文字列」に変換
#v3.6: 名古屋、大宰府の追加

import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import os

# -----------------------------
# ① JST の現在日付（TIMESTAMPで保持）---v3.3
# -----------------------------
JST = timezone(timedelta(hours=9))
today = datetime.now(JST)

# 過去2日分を取得（TIMESTAMPで保持）---v3.3
start_date = (today - timedelta(days=2)).date()
end_date   = (today - timedelta(days=1)).date()

start_str = start_date.strftime("%Y-%m-%d")
end_str = end_date.strftime("%Y-%m-%d")

# -----------------------------
# ② 取得する地点リスト
# -----------------------------
LOCATIONS = [
    {"name": "Tokyo", "lat": 35.6895, "lon": 139.6917},
    {"name": "Osaka", "lat": 34.6937, "lon": 135.5023},
	{"name": "nagoya", "lat": 35.1815, "lon": 136.9066},
	{"name": "dazaifu", "lat": 33.5123, "lon": 130.5230},
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
# ⑦ 525日より古いデータを削除（format='mixed' で安定化）&（TIMESTAMPで保持）---v3.3　→v3.5: threshold_date を ISO8601 の「文字列」に変換
# -----------------------------
retention_days = 525
threshold_date = (today - timedelta(days=retention_days)).replace(tzinfo=None)
threshold_date_str = threshold_date.strftime("%Y-%m-%dT%H:%M:%S")

# ★ v3.2 の重要ポイント：混在フォーマットを完全吸収 &（TIMESTAMPで保持）---v3.3　→v3.4にてISO8601フォーマットに修正
df_all["date"] = pd.to_datetime(df_all["date"], format='mixed').dt.strftime("%Y-%m-%dT%H:%M:%S")
df_all = df_all[df_all["date"] >= threshold_date_str]


# -----------------------------
# ⑧ 保存
# -----------------------------
df_all.to_csv(csv_path, index=False)

print("Weather data updated:", start_str, "to", end_str)
print("Rows collected:", len(rows))
print("Old data removed before:", threshold_date)
