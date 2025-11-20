import json
import re
import requests
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

def get_next_friday_date():
    today = date.today()
    days_ahead = (4 - today.weekday() + 7) % 7
    if days_ahead == 0: days_ahead = 0
    next_friday = today + timedelta(days=days_ahead)
    return next_friday.strftime("%Y-%m-%d") # ISO format for Hebcal

def get_friday_fmt_itin():
    # Format for Itim LaBina URL: "Fri, 21 Nov 2025 00:00:00 GMT"
    d = date.today()
    days_ahead = (4 - d.weekday() + 7) % 7
    if days_ahead == 0: days_ahead = 0
    next_friday = d + timedelta(days=days_ahead)
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
    # 1. SETUP DATES
    friday_iso = get_next_friday_date()
    friday_itin = get_friday_fmt_itin()
    
    data = {
        "parsha": "שבת שלום",
        "description": "", 
        "candles": "16:00",
        "havdalah": "17:00",
        "dvar_torah": "",
        "source": "Hybrid Data"
    }

    english_parsha_name = ""

    # --- STEP 1: GET METADATA FROM HEBCAL (Parsha Name & Mevarchim) ---
    print("🤖 Step 1: Fetching Metadata from Hebcal...")
    try:
        # We use Hebcal to get the canonical English name for Sefaria
        h_url = f"https://www.hebcal.com/shabbat?cfg=json&geonameid=281184&M=on&date={friday_iso}"
        h_data = requests.get(h_url).json()
        
        # Find Parsha Item
        parsha_item = next((x for x in h_data['items'] if x['category'] == 'parashat'), None)
        if parsha_item:
            data["parsha"] = parsha_item['hebrew'].replace("פרשת", "").strip()
            # Extract "Chayei Sara" from "Parashat Chayei Sara"
            english_parsha_name = parsha_item['title'].replace("Parashat ", "").strip()
            print(f"📖 Parsha: {data['parsha']} (English: {english_parsha_name})")

        # Find Mevarchim Item
        mevarchim_item = next((x for x in h_data['items'] if x['category'] == 'mevarchim'), None)
        if mevarchim_item:
            data["description"] = mevarchim_item['hebrew'] # "שבת מברכין החודש..."
            print(f"🌙 Status: {data['description']}")

    except Exception as e:
        print(f"❌ Hebcal Error: {e}")

    # --- STEP 2: FETCH SEFAT EMET (Using English Name) ---
    if english_parsha_name:
        print(f"📚 Step 2: Fetching Sefat Emet for: {english_parsha_name}")
        # Sefaria works best with English names (e.g. "Sefat Emet, Chayei Sara")
        sf_name = english_parsha_name.replace(" ", "_")
        sf_url = f"https://www.sefaria.org/api/texts/Sefat_Emet,_{sf_name}?lang=he"
        
        try:
            sf_resp = requests.get(sf_url)
            if sf_resp.status_code == 200:
                sf_json = sf_resp.json()
                # Sefaria returns a list of comments. We take the first one.
                if 'he' in sf_json and len(sf_json['he']) > 0:
                    raw_text = sf_json['he'][0]
                    # Sometimes it's nested lists
                    if isinstance(raw_text, list): raw_text = raw_text[0]
                    
                    clean_text = strip_html(raw_text)
                    # Limit length
                    short_text = (clean_text[:260] + '...') if len(clean_text) > 260 else clean_text
                    data["dvar_torah"] = short_text
                    print("✅ Got Sefat Emet!")
                else:
                    print("⚠️ Sefat Emet text empty.")
            else:
                print(f"⚠️ Sefaria Not Found (404) for: {sf_name}")
        except Exception as e:
            print(f"❌ Sefaria Error: {e}")

    # --- STEP 3: SCRAPE TIMES FROM ITIM LABINA ---
    print("🌍 Step 3: Scraping Exact Times from Itim LaBina...")
    base_url = "https://itimlabina.co.il/calendar/weekly"
    full_url = f"{base_url}?address=Jerusalem&lat=31.7198189&lng=35.2306758&date={friday_itin}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 3000})
        
        try:
            page.goto(full_url, timeout=60000)
            page.keyboard.press("Escape")
            page.wait_for_selector("text=הדלקת נרות", timeout=60000)
            
            text_content = page.inner_text("body")
            clean_text = text_content.replace("\n", " ")

            # We only grab times here, not the Parsha name (since Hebcal gave us a better one)
            candles_search = re.search(r'הדלקת נרות.*?(\d{1,2}:\d{2})', clean_text)
            if candles_search:
                data["candles"] = to_24h(candles_search.group(1))
                print(f"🕯️ Candles: {data['candles']}")

            havdalah_search = re.search(r'צאת השבת.*?(\d{1,2}:\d{2})', clean_text)
            if havdalah_search:
                data["havdalah"] = to_24h(havdalah_search.group(1))
                print(f"✨ Havdalah: {data['havdalah']}")

        except Exception as e:
            print(f"❌ Scrape Error: {e}")
        finally:
            browser.close()

    # SAVE
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scrape_times()