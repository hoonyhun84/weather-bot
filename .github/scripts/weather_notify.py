import os
import requests
from datetime import datetime, timezone, timedelta

API_KEY = os.environ["OPENWEATHER_API_KEY"]
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
CITY = "Chuncheon,KR"

KST = timezone(timedelta(hours=9))


def get_current_weather():
    """현재 날씨 조회"""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": CITY, "appid": API_KEY, "units": "metric", "lang": "kr"}
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()


def get_forecast():
    """3시간 간격 예보 조회 (최대 5일)"""
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"q": CITY, "appid": API_KEY, "units": "metric", "lang": "kr"}
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()


def get_weather_emoji(desc: str, icon: str) -> str:
    """날씨 설명 → 이모지 변환"""
    if "thunderstorm" in icon or "뇌우" in desc:
        return "⛈"
    if "rain" in icon or "비" in desc or "소나기" in desc:
        return "🌧"
    if "snow" in icon or "눈" in desc:
        return "❄️"
    if "mist" in icon or "fog" in icon or "안개" in desc or "연무" in desc:
        return "🌫"
    if icon.startswith("01"):
        return "☀️"
    if icon.startswith("02"):
        return "🌤"
    if icon.startswith("03") or icon.startswith("04"):
        return "☁️"
    return "🌡"


def build_current_section(data: dict) -> str:
    """현재 날씨 섹션"""
    temp = data["main"]["temp"]
    feels = data["main"]["feels_like"]
    temp_min = data["main"]["temp_min"]
    temp_max = data["main"]["temp_max"]
    desc = data["weather"][0]["description"]
    icon = data["weather"][0]["icon"]
    humidity = data["main"]["humidity"]
    wind = data["wind"]["speed"]
    rain = data.get("rain", {}).get("1h", 0)

    emoji = get_weather_emoji(desc, icon)
    umbrella = "☂ 우산 챙기세요!" if rain > 0 else "☀ 우산 필요 없어요"

    return (
        f"🌤 <b>춘천 오늘의 날씨</b>\n"
        f"───────────────\n"
        f"{emoji} 현재: <b>{temp:.1f}°C</b> (체감 {feels:.1f}°C)\n"
        f"🌡 최저 / 최고: {temp_min:.1f}°C / {temp_max:.1f}°C\n"
        f"🌥 날씨: {desc}\n"
        f"💧 습도: {humidity}%\n"
        f"💨 풍속: {wind} m/s\n"
        f"{umbrella}"
    )


def build_hourly_section(forecast_data: dict, hours: int = 24) -> str:
    """시간대별 예보 섹션
    
    break 대신 리스트 컴프리헨션으로 필터링하여
    경계값 문제 없이 안정적으로 동작
    """
    now_kst = datetime.now(KST)
    # 현재 3시간 슬롯 시작점 (예: 13:20 → 12:00 슬롯 포함)
    slot_start = now_kst - timedelta(hours=3)
    cutoff_kst = now_kst + timedelta(hours=hours)

    # 조건: 현재 슬롯 이후 ~ cutoff 이내 항목만 수집 (break 없이 전체 순회)
    items = []
    for item in forecast_data["list"]:
        dt_utc = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
        dt_kst = dt_utc.astimezone(KST)
        if slot_start < dt_kst <= cutoff_kst:
            items.append((dt_kst, item))

    if not items:
        return "\n\n⚠️ 시간대별 예보 데이터를 불러오지 못했어요."

    lines = ["\n\n⏱ <b>시간대별 예보</b>", "───────────────"]

    for dt_kst, item in items:
        temp = item["main"]["temp"]
        desc = item["weather"][0]["description"]
        icon = item["weather"][0]["icon"]
        pop = int(item.get("pop", 0) * 100)   # 강수 확률 (%)
        rain = item.get("rain", {}).get("3h", 0)
        snow = item.get("snow", {}).get("3h", 0)

        emoji = get_weather_emoji(desc, icon)

        # 강수/적설 표시
        precip = ""
        if rain > 0:
            precip = f" 🌧{rain:.1f}mm"
        elif snow > 0:
            precip = f" ❄{snow:.1f}mm"

        pop_str = f" ({pop}%)" if pop >= 20 else ""
        hour_str = dt_kst.strftime("%m/%d %H:%M")

        lines.append(
            f"{emoji} <b>{hour_str}</b>  {temp:.1f}°C  {desc}{precip}{pop_str}"
        )

    return "\n".join(lines)


def build_message(current_data: dict, forecast_data: dict) -> str:
    current_section = build_current_section(current_data)
    hourly_section = build_hourly_section(forecast_data, hours=24)
    return current_section + hourly_section


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    # 텔레그램 메시지 최대 4096자 제한 처리
    if len(message) > 4096:
        message = message[:4090] + "\n..."
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    res = requests.post(url, json=payload)
    res.raise_for_status()
    print("텔레그램 전송 완료!")


if __name__ == "__main__":
    current_data = get_current_weather()
    forecast_data = get_forecast()
    message = build_message(current_data, forecast_data)
    print(message)   # 로컬 테스트용 미리보기
    send_telegram(message)
