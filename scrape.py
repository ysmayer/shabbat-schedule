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
    """Converts 4:01 -> 16:01, but leaves 11:00 as 11:00"""
    if not time_str: return "00:00"
    
    parts = time_str.split(':')
    hour = int(parts[0])
    minute = parts[1]
    
    # Candle/Havdalah are always in the afternoon/evening.
    # If the hour is small (e.g., 1, 2, 3, 4, 5...), add 12.
    if hour < 11:
        hour += 12
        
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
        
        # TRICK 1: Set a HUGE viewport height so we see Friday & Saturday
        page = browser.new_page(viewport={'width': 1280, 'height': 3000})
        
        try:
            page.goto(full_url, timeout=90000)
            
            print("⏳ Waiting for text...")
            page.wait_for_selector("text=הדלקת נרות", timeout=60000)
            
            # TRICK 2: Scroll to bottom just to be safe
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # Get all text
            text_content = page.inner_text("body")
            clean_text = text_content.replace("\n", " ")

            # --- 1. FIND PARSHA ---
            # Now that Saturday is visible, we look for "Parshat X"
            # We ignore "Parshat HaShavua" or "Parshat HaChodesh"
            parsha_matches = re.findall(r'פרשת\s+([\u0590-\u05FF]+(?:[\s\-][\u0590-\u05FF]+)?)', text_content)
            for match in parsha_matches:
                if "השבוע" not in match and "החודש" not in match and "דרכים" not in match:
                    data["parsha"] = match.strip()
                    print(f"📖 Found Parsha: {data['parsha']}")
                    break 

            # --- 2. FIND TIMES & CONVERT TO 24H ---
            
            # Find Candle Lighting
            candles_search = re.search(r'הדלקת נרות.*?(\d{1,2}:\d{2})', clean_text)
            if candles_search:
                raw_time = candles_search.group(1)
                data["candles"] = to_24h(raw_time) # Convert 4:01 -> 16:01
                print(f"🕯️ Found Candles: {raw_time} -> {data['candles']}")

            # Find Havdalah
            havdalah_search = re.search(r'צאת השבת.*?(\d{1,2}:\d{2})', clean_text)
            if havdalah_search:
                raw_time = havdalah_search.group(1)
                data["havdalah"] = to_24h(raw_time) # Convert 5:15 -> 17:15
                print(f"✨ Found Havdalah: {raw_time} -> {data['havdalah']}")

            data["source"] = "Itim LaBina (Full View)"

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