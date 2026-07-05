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
# Keep quoted se'ifim short and readable.
ARUKH_MIN_LEN = 250
ARUKH_MAX_LEN = 750

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

# Simanim to skip when picking randomly.
ARUKH_EXCLUDED_SIMANIM = {280}

# Max characters for a se'if so the halakha stays short and readable.
ARUKH_MAX_LEN = 750
ARUKH_MIN_LEN = 250

# Curated Hebrew topic headings for Orach Chaim, Hilchot Shabbat (242-344).
# Sefaria stores no per-siman title, so these are a static map used only for
# the "מקור" context line. Any siman missing here simply shows no heading.
SIMAN_TITLES = {
    242: "הכנת צרכי שבת וכבודה",
    243: "נתינת מלאכה לאינו יהודי",
    244: "עשיית מלאכה על ידי אינו יהודי",
    245: "ישראל ואינו יהודי שהם שותפים",
    246: "השאלה והשכרה לאינו יהודי",
    247: "שילוח אגרת ביד אינו יהודי",
    248: "היוצא בשיירא ובספינה",
    249: "דברים האסורים בערב שבת",
    250: "הכנת צרכי סעודה לשבת",
    251: "עשיית מלאכה בערב שבת",
    252: "מלאכות המותרות להתחיל בערב שבת",
    253: "שהיית וחזרת התבשיל על הכירה",
    254: "צליה ואפיה סמוך לחשכה",
    255: "הדלקת אש והטמנה סמוך לחשכה",
    256: "זמן איסור מלאכה בערב שבת",
    257: "דיני הטמנה",
    258: "הטמנה על גבי דבר שאין מוסיף הבל",
    259: "הטמנה בדבר המוסיף הבל",
    260: "דברים שצריך לעשות בערב שבת",
    261: "בין השמשות ותוספת שבת",
    262: "כבוד שבת במלבושים ובהצעת המיטות",
    263: "על מי חלה חובת הדלקת נר שבת",
    264: "הפתילות והשמנים הכשרים לנר שבת",
    265: "דינים שונים בהדלקת הנר",
    266: "מי שקדש עליו היום בדרך",
    267: "סדר תפילת ליל שבת",
    268: "דיני תפילת שבת",
    269: "מנהג הקידוש בבית הכנסת",
    270: "אמירת במה מדליקין",
    271: "קידוש היום על היין",
    272: "על איזה יין מקדשים",
    273: "שאין קידוש אלא במקום סעודה",
    274: "בציעת הפת בשבת",
    275: "מה שאסור לעשות לאור הנר",
    276: "הנאה מנר שהדליקו אינו יהודי",
    277: "שלא לטלטל את הנר",
    278: "כיבוי הנר מפני החולה",
    279: "טלטול הנר בשבת",
    281: "סדר תפילת שחרית של שבת",
    282: "קריאת התורה בשבת",
    283: "תפילת מוסף של שבת",
    284: "הפטרה וברכותיה",
    285: "שנים מקרא ואחד תרגום",
    286: "זמן תפילת מוסף",
    287: "ניחום אבלים וביקור חולים בשבת",
    288: "איסור תענית בשבת",
    289: "סדר הקידוש והסעודה ביום",
    290: "לעסוק בתורה ובסעודה ביום השבת",
    291: "דין סעודה שלישית",
    292: "תפילת מנחה בשבת",
    293: "תפילת ערבית במוצאי שבת",
    294: "הבדלה בתפילה",
    295: "שאין מבדילין קודם צאת הכוכבים",
    296: "סדר הבדלה על הכוס",
    297: "דיני בשמים בהבדלה",
    298: "דיני נר של הבדלה",
    299: "דברים האסורים עד שיבדיל",
    300: "סעודת מלווה מלכה",
    301: "באיזה דברים מותר לצאת בשבת",
    302: "דין נקיון וקיפול הבגדים בשבת",
    303: "במה אשה יוצאה",
    304: "דין העבד בשבת",
    305: "דין בהמתו בשבת",
    306: "חפצים ודברי חול האסורים בשבת",
    307: "דיני ממצוא חפצך ודבר דבר",
    308: "דיני טלטול מוקצה",
    309: "טלטול מוקצה על ידי דבר אחר",
    310: "המשך דיני מוקצה",
    311: "טלטול מת ומוקצה לצורך",
    312: "דיני בית הכסא בשבת",
    313: "החזרת ופתיחת דלתות וכלים בשבת",
    314: "סתירה ובנין בכלים",
    315: "עשיית אהל עראי בשבת",
    316: "דין צידה בשבת",
    317: "דין קשירה בשבת",
    318: "דין מבשל בשבת",
    319: "דין בורר בשבת",
    320: "דין סוחט ומפרק בשבת",
    321: "דין טוחן ולש בשבת",
    322: "מוקצה במאכלים וביצה שנולדה",
    323: "הדחת כלים בשבת",
    324: "הכנת מאכל לבהמה בשבת",
    325: "הנאה ממעשה אינו יהודי בשבת",
    326: "דיני רחיצה בשבת",
    327: "דין סיכה בשבת",
    328: "דיני חולה בשבת",
    329: "הצלת נפשות בשבת",
    330: "דיני יולדת בשבת",
    331: "דיני מילה בשבת",
    332: "סיוע לבהמה ביום השבת",
    333: "טלטול לצורך ופינוי המחסן בשבת",
    334: "דיני הצלה מפני הדליקה",
    335: "דינים שונים בשבת",
    336: "דין עליה באילן ושימוש במחובר",
    337: "כיבוד הבית ודברים המותרים בשבת",
    338: "דין השמעת קול וכלי שיר בשבת",
    339: "דברים האסורים בשבת משום שבות",
    340: "תולדות מלאכות האסורות בשבת",
    341: "עניני ממון ומת בשבת",
    342: "דין בין השמשות של מוצאי שבת",
    343: "דיני חינוך קטן בשבת",
    344: "אמירת דבר תורה במקום שאינו נקי",
}

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
    lo, hi = ARUKH_SIMAN_RANGE
    pool = [n for n in range(lo, hi + 1) if n not in ARUKH_EXCLUDED_SIMANIM]
    random.shuffle(pool)
    for siman in pool[:8]:
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
                if ARUKH_MIN_LEN < len(clean) < ARUKH_MAX_LEN:
                    candidates.append((i, clean))
            if not candidates: continue
            idx, text = random.choice(candidates)
            title = SIMAN_TITLES.get(siman)
            ref_with_title = f"{he_ref} ({title})" if title else he_ref
            source = f"מקור: {ref_with_title}, סעיף {to_hebrew_numeral(idx + 1)}"
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
