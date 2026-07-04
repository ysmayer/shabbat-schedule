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
    "Bereshit": "Genesis", "Noach": "Genesis", "Lech-Lecha": "Genesis", "Vayera": "Genesis", 
    "Chayei Sara": "Genesis", "Toldot": "Genesis", "Vayetzei": "Genesis", "Vayishlach": "Genesis", 
    "Vayeshev": "Genesis", "Miketz": "Genesis", "Vayigash": "Genesis", "Vayechi": "Genesis",
    "Shemot": "Exodus", "Vaera": "Exodus", "Bo": "Exodus", "Beshalach": "Exodus", 
    "Yitro": "Exodus", "Mishpatim": "Exodus", "Terumah": "Exodus", "Tetzaveh": "Exodus", 
    "Ki Tisa": "Exodus", "Vayakhel": "Exodus", "Pekudei": "Exodus",
    "Vayikra": "Leviticus", "Tzav": "Leviticus", "Shmini": "Leviticus", "Tazria": "Leviticus", 
    "Metzora": "Leviticus", "Achrei Mot": "Leviticus", "Kedoshim": "Leviticus", "Emor": "Leviticus", 
    "Behar": "Leviticus", "Bechukotai": "Leviticus",
    "Bamidbar": "Numbers", "Nasso": "Numbers", "Beha'alotcha": "Numbers", "Sh'lach": "Numbers", 
    "Korach": "Numbers", "Chukat": "Numbers", "Balak": "Numbers", "Pinchas": "Numbers", 
    "Matot": "Numbers", "Masei": "Numbers",
    "Devarim": "Deuteronomy", "Vaetchanan": "Deuteronomy", "Eikev": "Deuteronomy", "Re'eh": "Deuteronomy", 
    "Shoftim": "Deuteronomy", "Ki Teitzei": "Deuteronomy", "Ki Tavo": "Deuteronomy", "Nitzavim": "Deuteronomy", 
    "Vayeilech": "Deuteronomy", "Ha'Azinu": "Deuteronomy", "Vezot Haberakhah": "Deuteronomy"
}

ARUKH_SIMAN_RANGE = (242, 344)

def get_next_friday_date():
    today = date.today()
    days_ahead = (4 - today.weekday() + 7) % 7
    next_friday = today + timedelta(days=days_ahead)
    return next_friday.strftime("%Y-%m-%d")

def get_friday_fmt_itin():
    d = date.today()
    days_ahead = (4 - d.weekday() + 7) % 7
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

def to_hebrew_numeral(n):
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
    for attempt in range(5):
        siman = random.randint(*ARUKH_SIMAN_RANGE)
        url = f"https://www.sefaria.org/api/texts/Arukh_HaShulchan,_Orach_Chaim.{siman}?lang=he"
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code != 200: continue
            payload = resp.json()
            segments = payload.get('he') or []
            he_ref = payload.get('heRef', f"ערוך השולחן, אורח חיים {to_hebrew_numeral(siman)}")
            candidates = []
            for i, seg in enumerate(segments):
                if isinstance(seg, list): seg = " ".join(str(x) for x in seg)
                clean = strip_html(str(seg))
                if 300 < len(clean) < 1400: candidates.append((i, clean))
            if not candidates: continue
            idx, text = random.choice(candidates)
            source = f"מקור: {he_ref}, סעיף {to_hebrew_numeral(idx + 1)}"
            return text, source
        except Exception: continue
    return None, None

def load_manual_data():
    if os.path.exists('manual_data.json'):
        with open('manual_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def scrape_times():
    friday_iso = get_next_friday_date()
    manual_config = load_manual_data()
    
    data = {
        "parsha": "שבת שלום",
        "description": manual_config.get("description", ""),
        "molad": "",
        "candles": "16:00",
        "havdalah": "17:00",
        "dvar_torah": "",
        "dvar_source": "",
        "shiur_topic": manual_config.get("shiur_topic", "הלכות שבת"),
        "is_summer": True,
        "image": manual_config.get("image", "kotel.jpg"),
        "source": "Hybrid Data"
    }

    # 1. Fetch Torah content
    text, source = fetch_arukh_hashulchan()
    if text:
        data["dvar_torah"] = text
        data["dvar_source"] = source

    # 2. Write JSON securely
    try:
        with open('data.json', 'w', encoding='utf-8') as f:
            # ensure_ascii=False keeps Hebrew legible, json.dump handles all escaping
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ Successfully generated valid data.json")
    except Exception as e:
        print(f"❌ Failed to write JSON: {e}")

if __name__ == "__main__":
    scrape_times()
