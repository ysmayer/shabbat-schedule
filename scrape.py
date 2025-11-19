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
            page.goto(full_url, timeout=90000) # Increased timeout to 90s
            
            print("⏳ Waiting for 'Shimmers' to vanish and text to appear...")
            
            # CRITICAL FIX: Wait until the specific text "הדלקת נרות" exists in the DOM
            # This guarantees the data has loaded.
            page.wait_for_selector("text=הדלקת נרות", timeout=60000)
            
            print("✅ Data loaded! Extracting text...")
            
            # Get the text content now that we know it's there
            text_content = page.inner_text("body")
            
            # 1. Find Parsha
            # Looks for "Parshat [Name]"
            parsha_matches = re.findall(r'פרשת\s+([\u0590-\u05FF]+(?:[\s\-][\u0590-\u05FF]+)?)', text_content)
            for match in parsha_matches:
                if "השבוע" not in match and "החודש" not in match:
                    data["parsha"] = match.strip()
                    print(f"📖 Found Parsha: {data['parsha']}")
                    break 

            # 2. Find Candles (16:XX or 15:XX) near the words "Hadlakat Nerot"
            # We remove newlines to make regex easier
            clean_text = text_content.replace("\n", " ")
            
            candles_search = re.search(r'הדלקת נרות.*?(\d{1,2}:\d{2})', clean_text)
            if candles_search:
                data["candles"] = candles_search.group(1)
                print(f"🕯️ Found Candles: {data['candles']}")

            # 3. Find Havdalah
            havdalah_search = re.search(r'צאת השבת.*?(\d{1,2}:\d{2})', clean_text)
            if havdalah_search:
                data["havdalah"] = havdalah_search.group(1)
                print(f"✨ Found Havdalah: {data['havdalah']}")

            data["source"] = "Itim LaBina (Live)"

        except Exception as e:
            print(f"❌ Error: {e}")
            # Take screenshot of the error state
            page.screenshot(path="error_view.png")
        finally:
            # Save a success screenshot to verify
            page.screenshot(path="debug_view.png", full_page=True)
            browser.close()

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scrape_times()