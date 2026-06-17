import os
import requests
from datetime import datetime, timezone, timedelta

API_KEY = os.environ["OPENWEATHER_API_KEY"]
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
CITY = "Chuncheon,KR"

KST = timezone(timedelta(hours=9))


def get_current_weather():
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": CITY, "appid": API_KEY, "units": "metric", "lang": "kr"}
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()


def get_forecast():
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"q": CITY, "appid": API_KEY, "units": "metric", "lang": "kr"}
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()


def get_weather_emoji(icon: str) -> str:
    if icon.startswith("11"):
        return "⛈"
    if icon.startswith("09") or icon.startswith("10"):
        return "🌧"
    if icon.startswith("13"):
        return "❄️"
    if icon.startswith("50"):
        return "🌫"
    if icon.startswith("01"):
        return "☀️"
    if icon.startswith("02"):
        return "🌤"
    if icon.startswith("03") or icon.startswith("04"):
        return "☁️"
    return "🌡"


def build_current_section(data: dict) -> str:
    temp     = data["main"]["temp"]
    feels    = data["main"]["feels_like"]
    temp_min = data["main"]["temp_min"]
    temp_max = data["main"]["temp_max"]
    desc     = data["weather"][0]["description"]
    icon     = data["weather"][0]["icon"]
    humidity = data["main"]["humidity"]
    wind     = data["wind"]["speed"]
    rain     = data.get("rain", {}).get("1h", 0)

    emoji    = get_weather_emoji(icon)
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


def build_hourly_section(forecast_data: dict, slots: int = 8) -> str:
    """
    시간대별 예보 섹션.
    UTC 타임스탬프 직접 비교 방식으로 단순화 — 복잡한 KST 변환 없이
    현재 시각(UTC) 이후 슬롯 최대 slots개(기본 8개 = 24시간)를 표시.
    """
    now_ts = datetime.now(timezone.utc).timestamp()

    # ── 디버그: API 응답 기본 정보 출력 ──────────────────────
    all_items = forecast_data.get("list", [])
    print(f"[DEBUG] forecast list 항목 수: {len(all_items)}")
    if all_items:
        first_ts = all_items[0]["dt"]
        first_kst = datetime.fromtimestamp(first_ts, tz=KST).strftime("%m/%d %H:%M")
        print(f"[DEBUG] 첫 번째 슬롯: {first_kst} KST (ts={first_ts})")
        print(f"[DEBUG] 현재 UTC ts: {int(now_ts)}")
    # ─────────────────────────────────────────────────────────

    # 현재 시각 이후 슬롯만 수집 (타임스탬프 직접 비교)
    future_items = [item for item in all_items if item["dt"] > now_ts][:slots]

    print(f"[DEBUG] 필터 후 표시할 슬롯 수: {len(future_items)}")

    if not future_items:
        return "\n\n⚠️ 시간대별 예보 데이터를 불러오지 못했어요."

    lines = ["\n\n⏱ <b>시간대별 예보</b>", "───────────────"]

    for item in future_items:
        dt_kst   = datetime.fromtimestamp(item["dt"], tz=KST)
        hour_str = dt_kst.strftime("%m/%d %H:%M")
        temp     = item["main"]["temp"]
        desc     = item["weather"][0]["description"]
        icon     = item["weather"][0]["icon"]
        pop      = int(item.get("pop", 0) * 100)
        rain     = item.get("rain", {}).get("3h", 0)
        snow     = item.get("snow", {}).get("3h", 0)

        emoji  = get_weather_emoji(icon)
        precip = f" 🌧{rain:.1f}mm" if rain > 0 else (f" ❄{snow:.1f}mm" if snow > 0 else "")
        pop_str = f" ({pop}%)" if pop >= 20 else ""

        lines.append(f"{emoji} <b>{hour_str}</b>  {temp:.1f}°C  {desc}{precip}{pop_str}")

    return "\n".join(lines)


def build_message(current_data: dict, forecast_data: dict) -> str:
    current_section = build_current_section(current_data)
    try:
        hourly_section = build_hourly_section(forecast_data)
    except Exception as e:
        print(f"[ERROR] build_hourly_section 예외 발생: {e}")
        hourly_section = f"\n\n⚠️ 예보 처리 중 오류: {e}"
    return current_section + hourly_section


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    if len(message) > 4096:
        message = message[:4090] + "\n..."
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    res = requests.post(url, json=payload)
    res.raise_for_status()
    print("텔레그램 전송 완료!")


if __name__ == "__main__":
    current_data  = get_current_weather()
    forecast_data = get_forecast()
    message       = build_message(current_data, forecast_data)
    print("\n── 전송 메시지 미리보기 ──")
    print(message)
    print("──────────────────────\n")
    send_telegram(message)
