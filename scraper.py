import hashlib
import json
from datetime import datetime, timezone, timedelta
from curl_cffi import requests
from bs4 import BeautifulSoup

URL = "https://energy-ua.info/cherga/6-1"

def main():
    # impersonate="chrome" подменяет TLS-отпечаток и заголовки под настоящий Chrome
    resp = requests.get(URL, impersonate="chrome", timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    period_list = soup.find("div", id="periodList")
    if not period_list:
        raise RuntimeError("Не найден блок #periodList — проверь разметку или доступность сайта")

    periods = []
    for row in period_list.find_all("div", class_="period-row"):
        classes = row.get("class", [])
        has_power = "status-green" in classes
        from_min = int(row["data-from"])
        to_min = int(row["data-to"])

        time_tag = row.select_one(".period-time strong")
        time_str = (
            time_tag.get_text(strip=True)
            if time_tag
            else f"{from_min // 60:02d}:{from_min % 60:02d} - {to_min // 60:02d}:{to_min % 60:02d}"
        )

        periods.append({
            "time": time_str,
            "from_min": from_min,
            "to_min": to_min,
            "has_power": has_power
        })

    schedule_hash = hashlib.md5(
        json.dumps(periods, sort_keys=True).encode("utf-8")
    ).hexdigest()

    kyiv_tz = timezone(timedelta(hours=2))
    now_str = datetime.now(kyiv_tz).strftime("%Y-%m-%d %H:%M:%S")

    output = {
        "queue": "6.1",
        "updated_at": now_str,
        "hash": schedule_hash,
        "periods": periods
    }

    with open("schedule.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
