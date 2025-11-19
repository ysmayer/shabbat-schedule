import json
import re
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

def get_next_friday_date():
    today = date.today()
    days_ahead = (4 - today.weekday() + 7) % 7
    if days_ahead == 0: days_ahead = 0
    next_friday = today + timedelta(days=days_ahead)
    return next_friday.strftime("%a, %d %b %Y 00:00:00 GMT")

def to_24h(time_str):
    if not time_str: return "00:00"
    parts = time_str.split(':')
    hour = int(parts[0])
    minute = parts[1]
    if hour < 11: hour += 12
    return f"{hour}:{minute}"

def scrape_times():
    target_date = get_next_friday_date()
    base_url = "https://itimlabina.co.il/calendar/weekly"
    full_url = f"{base_url}?address=Jerusalem&lat=31.7198189&lng=35.2306758&date={target_date}"
    
    print(f"🌍 Connecting to: {full_url}")

    data = {
        "parsha": "שבת שלום",
        "candles": "16:00",
        "havdalah": "17:00",
        "source": "Scrape Failed"
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Huge viewport to see Friday/Shabbat rows
        page = browser.new_page(viewport={'width': 1280, 'height': 3000})
        
        try:
            page.goto(full_url, timeout=90000)
            
            # 1. Dismiss Popup (The "Use Location" dialog)
            # We press Escape to close any modals
            page.keyboard.press("Escape")
            
            print("⏳ Waiting for text...")
            page.wait_for_selector("text=הדלקת נרות", timeout=60000)
            
            # Scroll down to ensure lazy text loads
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            text_content = page.inner_text("body")
            clean_text = text_content.replace("\n", " ")

            # --- 1. FIND PARSHA (Updated for COLON) ---
            # This Regex matches: "פרשת" then OPTIONAL colon ":" then spaces, then Hebrew Name
            parsha_matches = re.findall(r'פרשת[:\s]+([\u0590-\u05FF]+(?:[\s\-][\u0590-\u05FF]+)?)', text_content)
            
            for match in parsha_matches:
                # Filter out generic headers
                if "השבוע" not in match and "החודש" not in match and "דרכים" not in match:
                    data["parsha"] = match.strip()
                    print(f"📖 Found Parsha: {data['parsha']}")
                    break 

            # --- 2. FIND TIMES ---
            candles_search = re.search(r'הדלקת נרות.*?(\d{1,2}:\d{2})', clean_text)
            if candles_search:
                raw_time = candles_search.group(1)
                data["candles"] = to_24h(raw_time)
                print(f"🕯️ Found Candles: {data['candles']}")

            havdalah_search = re.search(r'צאת השבת.*?(\d{1,2}:\d{2})', clean_text)
            if havdalah_search:
                raw_time = havdalah_search.group(1)
                data["havdalah"] = to_24h(raw_time)
                print(f"✨ Found Havdalah: {data['havdalah']}")

            data["source"] = "Itim LaBina (Fixed)"

        except Exception as e:
            print(f"❌ Error: {e}")
            page.screenshot(path="error_view.png")
        finally:
            page.screenshot(path="debug_view.png", full_page=True)
            browser.close()

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scrape_times()