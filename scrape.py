import json
import re
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

def get_next_friday_date():
    today = date.today()
    days_ahead = (4 - today.weekday() + 7) % 7
    if days_ahead == 0: days_ahead = 0
    next_friday = today + timedelta(days=days_ahead)
    # Format: "Fri, 21 Nov 2025 00:00:00 GMT"
    return next_friday.strftime("%a, %d %b %Y 00:00:00 GMT")

def scrape_times():
    # Use the specific date and location
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
        page = browser.new_page()
        
        try:
            page.goto(full_url, timeout=60000)
            
            # 1. Wait for the main table to load
            page.wait_for_selector("table", timeout=30000)
            
            # 2. Take a Debug Screenshot (Crucial!)
            page.screenshot(path="debug_view.png", full_page=True)
            print("📸 Screenshot saved as debug_view.png")

            # 3. Get the full text of the page to analyze structure
            text_content = page.inner_text("body")
            
            # --- IMPROVED PARSHA FINDER ---
            # Find "Parsha" but IGNORE "Parshat HaShavua" (Header)
            # We look for lines starting with "פרשת" that have more text
            parsha_matches = re.findall(r'פרשת\s+([\u0590-\u05FF]+(?:[\s\-][\u0590-\u05FF]+)?)', text_content)
            for match in parsha_matches:
                if "השבוע" not in match and "החודש" not in match:
                    data["parsha"] = match.strip()
                    break # Stop at the first real parsha name

            # --- IMPROVED TIME FINDER ---
            # Instead of random regex, we look for the specific structure
            # Pattern: "Candles" followed closely by a Time (XX:XX)
            
            # Find Candle Lighting (Looks for 16:XX or 15:XX or 17:XX etc)
            candles_search = re.search(r'הדלקת נרות[^\d]*(\d{1,2}:\d{2})', text_content)
            if candles_search:
                data["candles"] = candles_search.group(1)

            # Find Havdalah (Looks for 17:XX or 18:XX)
            havdalah_search = re.search(r'צאת השבת[^\d]*(\d{1,2}:\d{2})', text_content)
            if havdalah_search:
                data["havdalah"] = havdalah_search.group(1)

            data["source"] = "Itim LaBina (Smart Scrape)"
            
            print(f"✅ RESULT: {data}")

        except Exception as e:
            print(f"❌ Error: {e}")
            page.screenshot(path="error_view.png")
        finally:
            browser.close()

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scrape_times()