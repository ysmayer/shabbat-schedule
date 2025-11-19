import json
import re
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

def get_next_friday_date():
    today = date.today()
    # Calculate next Friday (4 = Friday)
    days_ahead = (4 - today.weekday() + 7) % 7
    if days_ahead == 0: days_ahead = 0
    next_friday = today + timedelta(days=days_ahead)
    # Format exactly like the URL: "Fri, 21 Nov 2025 00:00:00 GMT"
    return next_friday.strftime("%a, %d %b %Y 00:00:00 GMT")

def scrape_times():
    target_date = get_next_friday_date()
    
    # This is the URL with your specific coordinates
    base_url = "https://itimlabina.co.il/calendar/weekly"
    full_url = f"{base_url}?address=Jerusalem&lat=31.7198189&lng=35.2306758&date={target_date}"
    
    print(f"🌍 Connecting to: {full_url}")

    data = {
        "parsha": "שבת קודש",
        "candles": "16:00",
        "havdalah": "17:00",
        "source": "Default (Scrape Failed)"
    }

    with sync_playwright() as p:
        # Launch invisible browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(full_url, timeout=60000)
            # Wait for the text "הדלקת נרות" to appear on screen
            page.wait_for_selector("text=הדלקת נרות", timeout=20000)
            
            # Get all text from the page
            content = page.content() 
            
            # --- Regex Magic ---
            # Looking for time (XX:XX) near "הדלקת נרות"
            # This regex looks for the pattern in the raw HTML which is often cleaner
            candles_match = re.search(r'הדלקת נרות.*?(\d{1,2}:\d{2})', content)
            havdalah_match = re.search(r'צאת השבת.*?(\d{1,2}:\d{2})', content)
            parsha_match = re.search(r'פרשת ([\u0590-\u05FF\- ]+)', content)

            if candles_match:
                data["candles"] = candles_match.group(1)
                print(f"✅ Found Candles: {data['candles']}")
            
            if havdalah_match:
                data["havdalah"] = havdalah_match.group(1)
                print(f"✅ Found Havdalah: {data['havdalah']}")

            if parsha_match:
                # Clean up the parsha name (remove extra HTML junk if any)
                raw_parsha = parsha_match.group(1).split('<')[0].strip()
                data["parsha"] = raw_parsha
                print(f"✅ Found Parsha: {data['parsha']}")
                
            data["source"] = "Itim LaBina (Live)"

        except Exception as e:
            print(f"❌ Error: {e}")
            # Take a screenshot if it fails (helper for debugging in future)
            # page.screenshot(path="error.png") 
        finally:
            browser.close()

    # Save to JSON
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("💾 Saved data.json")

if __name__ == "__main__":
    scrape_times()