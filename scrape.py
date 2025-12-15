import json
import re
import requests
import urllib.parse
from datetime import date, timedelta
from playwright.sync_api import sync_playwright
from pyluach import dates

# --- CONFIGURATION: Parsha to Book Mapping ---
PARSHA_MAP = {
    # GENESIS
    "Bereshit": "Genesis", "Noach": "Genesis", "Lech-Lecha": "Genesis", "Vayera": "Genesis", 
    "Chayei Sara": "Genesis", "Toldot": "Genesis", "Vayetzei": "Genesis", "Vayishlach": "Genesis", 
    "Vayeshev": "Genesis", "Miketz": "Genesis", "Vayigash": "Genesis", "Vayechi": "Genesis",
    # EXODUS
    "Shemot": "Exodus", "Vaera": "Exodus", "Bo": "Exodus", "Beshalach": "Exodus", 
    "Yitro": "Exodus", "Mishpatim": "Exodus", "Terumah": "Exodus", "Tetzaveh": "Exodus", 
    "Ki Tisa": "Exodus", "Vayakhel": "Exodus", "Pekudei": "Exodus",
    # LEVITICUS
    "Vayikra": "Leviticus", "Tzav": "Leviticus", "Shmini": "Leviticus", "Tazria": "Leviticus", 
    "Metzora": "Leviticus", "Achrei Mot": "Leviticus", "Kedoshim": "Leviticus", "Emor": "Leviticus", 
    "Behar": "Leviticus", "Bechukotai": "Leviticus",
    # NUMBERS
    "Bamidbar": "Numbers", "Nasso": "Numbers", "Beha'alotcha": "Numbers", "Sh'lach": "Numbers", 
    "Korach": "Numbers", "Chukat": "Numbers", "Balak": "Numbers", "Pinchas": "Numbers", 
    "Matot": "Numbers", "Masei": "Numbers",
    # DEUTERONOMY
    "Devarim": "Deuteronomy", "Vaetchanan": "Deuteronomy", "Eikev": "Deuteronomy", "Re'eh": "Deuteronomy", 
    "Shoftim": "Deuteronomy", "Ki Teitzei": "Deuteronomy", "Ki Tavo": "Deuteronomy", "Nitzavim": "Deuteronomy", 
    "Vayeilech": "Deuteronomy", "Ha'Azinu": "Deuteronomy", "Vezot Haberakhah": "Deuteronomy"
}

def get_next_friday_date():
    today = date.today()
    days_ahead = (4 - today.weekday() + 7) % 7
    if days_ahead == 0: days_ahead = 0
    next_friday = today + timedelta(days=days_ahead)
    return next_friday.strftime("%Y-%m-%d")

def get_next_shabbat_date_obj():
    today = date.today()
    days_ahead = (5 - today.weekday() + 7) % 7
    if days_ahead == 0: days_ahead = 7
    return today + timedelta(days=days_ahead)

def get_friday_fmt_itin():
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
    if not isinstance(text, str): return ""
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    text = re.sub(r'\[\d+\]', '', text)
    return text.strip()

def flatten_text_list(data_he):
    texts = []
    if isinstance(data_he, list):
        for item in data_he:
            texts.extend(flatten_text_list(item))
    elif isinstance(data_he, str):
        texts.append(data_he)
    return texts

def fetch_sefaria_text(parsha_name):
    book = PARSHA_MAP.get(parsha_name)
    variations = []
    if book: variations.append(f"Sefat_Emet,_{book},_{parsha_name}")
    variations.append(f"Sefat_Emet,_{parsha_name}")
    variations.append(f"Sefat_Emet,_Parashat_{parsha_name}")

    for ref in variations:
        safe_ref = ref.replace(" ", "_")
        encoded_ref = urllib.parse.quote(safe_ref)
        url = f"https://www.sefaria.org/api/texts/{encoded_ref}?lang=he"
        print(f"Trying Sefaria URL: {url}")
        
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if 'he' in data and data['he']:
                    all_segments = flatten_text_list(data['he'])
                    best_segment = ""
                    min_len = 10000
                    for segment in all_segments:
                        clean = strip_html(segment)
                        length = len(clean)
                        if length < 100: continue 
                        if 150 < length < 550:
                            return clean
                        if length < min_len:
                            min_len = length
                            best_segment = clean
                    if best_segment: return best_segment
                    return strip_html(all_segments[0])
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
    return None

def load_manual_data():
    try:
        with open('manual_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ manual_data.json not found, using defaults.")
        return {}
    except Exception as e:
        print(f"❌ Error reading manual_data.json: {e}")
        return {}

def scrape_times():
    friday_iso = get_next_friday_date()
    friday_itin = get_friday_fmt_itin()
    manual_config = load_manual_data()
    
    data = {
        "parsha": "שבת שלום",
        "description": "", 
        "molad": "", 
        "candles": "16:00",
        "havdalah": "17:00",
        "dvar_torah": "",
        "dvar_source": "",
        # FIX: Default to "הלכות שבת" if manual data is missing
        "shiur_topic": manual_config.get("shiur_topic", "הלכות שבת"), 
        "kidush": manual_config.get("kidush", ""),
        "messages": manual_config.get("messages", ""), 
        "source": "Hybrid Data"
    }

    english_parsha = ""
    hebrew_parsha_name = ""
    is_mevarchim = False

    # 1. METADATA & MEVARCHIM
    print("🤖 Step 1: Hebcal Metadata...")
    try:
        shabbat_date = get_next_shabbat_date_obj()
        heb_date = dates.HebrewDate.from_pydate(shabbat_date)
        
        if 23 <= heb_date.day <= 29:
            is_mevarchim = True
            data["description"] = "שבת מברכין"
            print("🌙 Status: Mevarchim Detected")

        h_url = f"https://www.hebcal.com/shabbat?cfg=json&geonameid=281184&M=on&date={friday_iso}"
        h_data = requests.get(h_url).json()
        
        parsha_item = next((x for x in h_data['items'] if x['category'] == 'parashat'), None)
        if parsha_item:
            data["parsha"] = parsha_item['hebrew'].replace("פרשת", "").strip()
            hebrew_parsha_name = data["parsha"]
            english_parsha = parsha_item['title'].replace("Parashat ", "").strip()
            print(f"📖 Parsha: {data['parsha']}")

    except Exception as e:
        print(f"❌ Metadata Error: {e}")

    # 2. SEFAT EMET
    if english_parsha:
        print(f"📚 Step 2: Fetching Sefat Emet...")
        text = fetch_sefaria_text(english_parsha)
        if text:
            data["dvar_source"] = f"מקור: שפת אמת, {hebrew_parsha_name}"
            limit = 600
            if len(text) > limit:
                cut_index = text.rfind('.', 0, limit)
                data["dvar_torah"] = text[:cut_index+1] + "..." if cut_index > 100 else text[:limit] + "..."
            else:
                data["dvar_torah"] = text
            print("✅ Sefat Emet Found!")

    # 3. ITIM LABINA
    print("🌍 Step 3: Scraping Times...")
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

            candles_search = re.search(r'הדלקת נרות.*?(\d{1,2}:\d{2})', clean_text)
            if candles_search: data["candles"] = to_24h(candles_search.group(1))

            havdalah_search = re.search(r'צאת השבת.*?(\d{1,2}:\d{2})', clean_text)
            if havdalah_search: data["havdalah"] = to_24h(havdalah_search.group(1))

            if is_mevarchim:
                molad_match = re.search(r'(המולד.*?)(?:\.|\n|$)', text_content)
                if molad_match:
                    raw_molad = molad_match.group(1).strip()
                    data["molad"] = re.sub(r'\s+', ' ', raw_molad)
                    print(f"🌑 Molad: {data['molad']}")

        except Exception as e:
            print(f"❌ Scrape Error: {e}")
        finally:
            browser.close()

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scrape_times()