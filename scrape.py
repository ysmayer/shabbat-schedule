import json
import re
import requests
import urllib.parse
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

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
    text = re.sub(r'\[\d+\]', '', text) # Remove [1]
    return text.strip()

def flatten_text_list(data_he):
    """Recursive function to get all text segments into a single flat list"""
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
                    # 1. Flatten all available comments into one list
                    all_segments = flatten_text_list(data['he'])
                    
                    print(f"Found {len(all_segments)} segments. Searching for the perfect length...")
                    
                    best_segment = ""
                    min_len = 10000
                    
                    # 2. Search for a "Goldilocks" segment (150 < chars < 550)
                    for segment in all_segments:
                        clean = strip_html(segment)
                        length = len(clean)
                        
                        # Filter out garbage (too short)
                        if length < 100: continue 
                        
                        # Perfect size found? Return immediately.
                        if 150 < length < 550:
                            print(f"✅ Found perfect short segment: {length} chars")
                            return clean
                        
                        # Keep track of the shortest valid one just in case
                        if length < min_len:
                            min_len = length
                            best_segment = clean
                    
                    # 3. Fallback: If no perfect size, return the shortest one found
                    if best_segment:
                         print(f"⚠️ No perfect size. Returning shortest found: {min_len} chars")
                         return best_segment
                    
                    # 4. Absolute Fallback: Just take the first one and cut it
                    return strip_html(all_segments[0])

        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
    
    return None

def scrape_times():
    friday_iso = get_next_friday_date()
    friday_itin = get_friday_fmt_itin()
    
    data = {
        "parsha": "שבת שלום",
        "description": "", 
        "candles": "16:00",
        "havdalah": "17:00",
        "dvar_to