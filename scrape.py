import json
import os
import random
import re
import requests
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
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

# --- ARUKH HASHULCHAN FETCHER (Hilchot Shabbat: Orach Chaim 242-344) ---
ARUKH_SIMAN_RANGE = (242, 344)

def to_hebrew_numeral(n):
    """Convert an integer to a Hebrew numeral string (e.g. 242 -> רמ\"ב)."""
    ones = ["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"]
    tens = ["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"]
    hundreds = ["", "ק", "ר", "ש", "ת"]
    result = ""
    h = n // 100
    result += "ת" * (h // 4) + hundreds[h % 4]
    n %= 100
    if n in (15, 16):
        result += "ט" + ("ו" if n == 15 else "ז")
    else:
        result += tens[n // 10] + ones[n % 10]
    if len(result) > 1:
        result = result[:-1] + '"' + result[-1]
    elif result:
        result += "'"
    return result

def fetch_arukh_hashulchan():
    """Pick a random se'if from Arukh HaShulchan, Orach Chaim (Hilchot Shabbat).

    Returns (text, source) or (None, None).
    """
    for attempt in range(5):
        siman = random.randint(*ARUKH_SIMAN_RANGE)
        url = f"https://www.sefaria.org/api/texts/Arukh_HaShulchan,_Orach_Chaim.{siman}?lang=he"
        print(f"Trying Arukh HaShulchan siman {siman}: {url}")
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code != 200:
                continue
            payload = resp.json()
            segments = payload.get('he') or []
            he_ref = payload.get('heRef', f"ערוך השולחן, אורח חיים {to_hebrew_numeral(siman)}")

            # Goldilocks se'ifim: long enough to stand alone, short enough to read
            candidates = []
            for i, seg in enumerate(segments):
                if isinstance(seg, list):
                    seg = " ".join(str(x) for x in seg)
                clean = strip_html(str(seg))
                if 300 < len(clean) < 1400:
                    candidates.append((i, clean))

            if not candidates:
                print(f"⚠️ No fitting se'if in siman {siman}, retrying...")
                continue

            idx, text = random.choice(candidates)
            source = f"מקור: {he_ref}, סעיף {to_hebrew_numeral(idx + 1)}"
            print(f"✅ Found Arukh HaShulchan se'if ({len(text)} chars): {source}")
            return text, source
        except Exception as e:
            print(f"❌ Error fetching Arukh HaShulchan: {e}")

    return None, None

def load_manual_data():
    try:
        with open('manual_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def detect_is_summer(friday_date):
    """Check if Israel is in summer time (DST) on the given Friday."""
    tz = ZoneInfo("Asia/Jerusalem")
    dt = datetime(friday_date.year, friday_date.month, friday_date.day, 12, 0, tzinfo=tz)
    return bool(dt.dst())

def resolve_image(english_parsha, manual_config):
    """Pick the parsha image, with manual override and fallback."""
    manual_image = manual_config.get("image")
    if manual_image:
        return manual_image
    if english_parsha:
        parsha_img = f"images/{english_parsha}.jpg"
        if os.path.exists(parsha_img):
            return parsha_img
    return "kotel.jpg"

def scrape_times():
    friday_iso = get_next_friday_date()
    friday_itin = get_friday_fmt_itin()
    manual_config = load_manual_data()

    # is_summer: manual override takes precedence, otherwise auto-detect from DST
    friday_date = date.fromisoformat(friday_iso)
    manual_summer = manual_config.get("is_summer")
    is_summer = manual_summer if manual_summer is not None else detect_is_summer(friday_date)
    
    data = {
        "parsha": "שבת שלום",
        "description": manual_config.get("description", ""), 
        "molad": "", 
        "candles": "16:00",
        "havdalah": "17:00",
        "dvar_torah": "",
        "dvar_source": "",
        "shiur_topic": manual_config.get("shiur_topic", "הלכות שבת"), 
        "kidush": manual_config.get("kidush", ""),
        "messages": manual_config.get("messages", ""),
        "is_summer": is_summer,
        "image": "kotel.jpg",
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
            if not data["description"]:
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

    # 2. ARUKH HASHULCHAN (Replaced Bat Ayin) — random halakha from Hilchot Shabbat
    print("📚 Step 2: Fetching Arukh HaShulchan (Hilchot Shabbat)...")
    text, source = fetch_arukh_hashulchan()
    if text:
        data["dvar_torah"] = text
        data["dvar_source"] = source
        print("✅ Arukh HaShulchan Found!")
    else:
        print("⚠️ Arukh HaShulchan not found.")

    # Resolve image based on parsha
    data["image"] = resolve_image(english_parsha, manual_config)
    print(f"🖼️ Image: {data['image']}")
    print(f"☀️ Summer: {is_summer}")

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

        except Exception as e:
            print(f"❌ Scrape Error: {e}")
        finally:
            browser.close()

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scrape_times()