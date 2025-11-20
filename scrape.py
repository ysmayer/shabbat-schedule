import json
import re
import requests
import urllib.parse
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

# --- CONFIGURATION: Parsha to Book Mapping ---
# This ensures we generate the correct Sefaria URL (e.g. "Sefat_Emet,_Genesis,_Chayei_Sara")
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
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    # Remove footnotes [1], [2]
    text = re.sub(r'\[\d+\]', '', text)
    return text.strip()

def fetch_sefaria_text(parsha_name):
    """
    Constructs the correct URL using the Book Name.
    Example: "Sefat_Emet,_Genesis,_Chayei_Sara"
    """
    book = PARSHA_MAP.get(parsha_name)
    
    # Prepare variations to try
    variations = []
    
    # Option 1: The correct structure (Book, Parsha)
    if book:
        variations.append(f"Sefat_Emet,_{book},_{parsha_name}")
    
    # Option 2: Direct Parsha (Fallback)
    variations.append(f"Sefat_Emet,_{parsha_name}")
    
    # Option 3: "Parashat" prefix
    variations.append(f"Sefat_Emet,_Parashat_{parsha_name}")

    for ref in variations:
        # Replace spaces with underscores for URL
        safe_ref = ref.replace(" ", "_")