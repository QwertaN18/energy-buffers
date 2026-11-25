import hashlib
import json
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

URL = "https://energy-ua.info/cherga/6-1"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="uk-UA"
        )
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        # Ждём появления блока с периодами (до 15 секунд, если сработает JS-проверка)
        page.wait_for_selector("#periodList", timeout=15000)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    period_list = soup.find("div", id="periodList")
    if not period_list:
        raise RuntimeError("Блок #periodList не найден")

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
