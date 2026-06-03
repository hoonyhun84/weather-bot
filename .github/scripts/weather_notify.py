import os
import requests

API_KEY = os.environ["OPENWEATHER_API_KEY"]
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
CITY = "Chuncheon,KR"

def get_weather():
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": CITY,
        "appid": API_KEY,
        "units": "metric",
        "lang": "kr"
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()

def build_message(data):
    temp = data["main"]["temp"]
    feels = data["main"]["feels_like"]
    desc = data["weather"][0]["description"]
    humidity = data["main"]["humidity"]
    wind = data["wind"]["speed"]
    rain = data.get("rain", {}).get("1h", 0)

    umbrella = "☂ 오늘 우산 챙기세요!" if rain > 0 else "☀ 우산 필요 없어요"

    return f"""🌤 <b>춘천 오늘의 날씨</b>
───────────────
🌡 현재 기온: <b>{temp:.1f}°C</b> (체감 {feels:.1f}°C)
🌥 날씨: {desc}
💧 습도: {humidity}%
💨 풍속: {wind} m/s

{umbrella}"""

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"  # <b>볼드</b> 태그 적용
    }
    res = requests.post(url, json=payload)
    res.raise_for_status()
    print("텔레그램 전송 완료!")

if __name__ == "__main__":
    data = get_weather()
    message = build_message(data)
    send_telegram(message)
