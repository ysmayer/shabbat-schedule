import json
import re
import requests
from datetime import date, timedelta
from playwright.sync_api import sync_playwright
from pyluach import dates  # Local Hebrew Date Converter

def get_next_shabbat_date():
    """Returns the Python date object for next Saturday"""
    today = date.today()
    # 5 = Saturday
    days_ahead = (5 - today.weekday() + 7) % 7
    if days_ahead == 0: days_ahead = 7 # If today is Sat, get next Sat
    return today + timedelta(days=days_ahead)

def get_friday_for_url():
    """Returns format for Itim LaBina URL: Fri, 21 Nov 2025"""
    today = date.today()
    # 4 = Friday
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

def strip_html(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def scrape_times():
    data = {
        "parsha": "שבת שלום",
        "description": "", 
        "candles": "16:00",
        "havdalah": "17:00",
        "dvar_torah": "",
        "source": "Combined Data"
    }

    # --- 1. CALCULATE MEVARCHIM LOCALLY ---
    # No API needed. We just check the Hebrew date of Shabbat.
    shabbat_date_gregorian = get_next_shabbat_date()
    shabbat_hebrew = dates.HebrewDate.from_pydate(shabbat_date_gregorian)
    
    print(f"📅 Upcoming Shabbat is: {shabbat_hebrew.day} in {shabbat_hebrew.month_name(hebrew=True)}")

    # Logic: If the day is 23 or more (and less than 30), it is Mevarchim
    if 23 <= shabbat_hebrew.day <= 29:
        # Get name of *next* month
        # (This is a simple hack: valid for all months except Adar/Leap edge cases, usually fine)
        data["description"] = "שבת מברכין החודש"
        print("🌙 Status: Mevarchim detected!")

    # --- 2. SCRAPE ITIM LABINA ---
    print("🌍 Scraping Times & Parsha...")
    target_date_str = get_friday_for_url()
    base_url = "https://itimlabina.co.il/calendar/weekly"
    full_url = f"{base_url}?address=Jerusalem&lat=31.7198189&lng=35.2306758&date={target_date_str}"
    
    parsha_hebrew_name = ""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 3000})
        
        try:
            page.goto(full_url, timeout=60000)
            page.keyboard.press("Escape")
            page.wait_for_selector("text=הדלקת נרות", timeout=60000)
            
            text_content = page.inner_text("body")
            clean_text = text_content.replace("\n", " ")

            # Find Parsha
            parsha_matches = re.findall(r'פרשת[:\s]+([\u0590-\u05FF]+(?:[\s\-][\u0590-\u05FF]+)?)', text_content)
            for match in parsha_matches:
                if "השבוע" not in match and "החודש" not in match and "דרכים" not in match:
                    # FIX: Remove "Haftara" if it stuck to the name
                    clean_name = match.split("הפטרה")[0].strip()
                    data["parsha"] = clean_name
                    parsha_hebrew_name = clean_name
                    print(f"📖 Found Parsha: {data['parsha']}")
                    break 

            # Find Times
            candles_search = re.search(r'הדלקת נרות.*?(\d{1,2}:\d{2})', clean_text)
            if candles_search:
                data["candles"] = to_24h(candles_search.group(1))

            havdalah_search = re.search(r'צאת השבת.*?(\d{1,2}:\d{2})', clean_text)
            if havdalah_search:
                data["havdalah"] = to_24h(havdalah_search.group(1))

        except Exception as e:
            print(f"❌ Scrape Error: {e}")
        finally:
            browser.close()

    # --- 3. FETCH SEFAT EMET (Using Hebrew Name) ---
    if parsha_hebrew_name:
        print(f"📚 Fetching Sefat Emet for: {parsha_hebrew_name}")
        # Replace spaces with underscores for Sefaria
        formatted_name = parsha_hebrew_name.replace(" ", "_")
        sf_url = f"https://www.sefaria.org/api/texts/Sefat_Emet,_פרשת_{formatted_name}?lang=he"
        
        try:
            sf_resp = requests.get(sf_url)
            if sf_resp.status_code == 200:
                sf_json = sf_resp.json()
                if 'he' in sf_json and len(sf_json['he']) > 0:
                    # Get first paragraph
                    raw_text = sf_json['he'][0]
                    if isinstance(raw_text, list): raw_text = raw_text[0]
                    
                    clean_text = strip_html(raw_text)
                    # Limit to ~250 chars so it fits on the page
                    short_text = (clean_text[:250] + '...') if len(clean_text) > 250 else clean_text
                    
                    data["dvar_torah"] = short_text
                    print("✅ Got Sefat Emet!")
                else:
                    print("⚠️ Sefat Emet text empty.")
            else:
                print(f"⚠️ Sefaria Error: {sf_resp.status_code}")
        except Exception as e:
            print(f"❌ Sefaria Exception: {e}")

    # Save
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scrape_times()