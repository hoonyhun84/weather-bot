import os
import requests
from datetime import datetime

API_KEY = os.environ["OPENWEATHER_API_KEY"]
SLACK_URL = os.environ["SLACK_WEBHOOK_URL"]
CITY = "Chuncheon"  # 원하는 도시로 변경

def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather"
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

    # 우산 여부 판단
    umbrella = "☂️ 오늘 우산 챙기세요!" if rain > 0 else "☀️ 우산 필요 없어요"

    return {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🌤 {CITY} 오늘의 날씨"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*현재 기온*\n{temp:.1f}°C (체감 {feels:.1f}°C)"},
                    {"type": "mrkdwn", "text": f"*날씨*\n{desc}"},
                    {"type": "mrkdwn", "text": f"*습도*\n{humidity}%"},
                    {"type": "mrkdwn", "text": f"*풍속*\n{wind} m/s"},
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": umbrella}
            }
        ]
    }

def send_slack(payload):
    res = requests.post(SLACK_URL, json=payload)
    res.raise_for_status()
    print("Slack 전송 완료!")

if __name__ == "__main__":
    data = get_weather()
    payload = build_message(data)
    send_slack(payload)
