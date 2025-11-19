import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import date, timedelta

def get_next_friday():
    today = date.today()
    # 4 = Friday (Monday is 0)
    days_ahead = (4 - today.weekday() + 7) % 7
    if days_ahead == 0: 
        days_ahead = 0 # If today is Friday, get today
    next_friday = today + timedelta(days=days_ahead)
    return next_friday.strftime("%a, %d %b %Y 00:00:00 GMT")

def scrape_times():
    # 1. Generate URL for this Friday
    date_str = get_next_friday()
    base_url = "https://itimlabina.co.il/calendar/weekly"
    params = {
        "address": "עמנואל זיסמן, ירושלים",
        "lat": "31.7198189",
        "lng": "35.2306758",
        "date": date_str
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"Fetching URL: {base_url} with params {params}")
    response = requests.get(base_url, params=params, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 2. Extract Times using text search (Robust method)
    # We look for the specific Hebrew terms in the page
    text_content = soup.get_text()
    
    # Find Candle Lighting (looks for "הדלקת נרות" followed by a time)
    candles_match = re.search(r'הדלקת נרות.*?(\d{1,2}:\d{2})', text_content)
    havdalah_match = re.search(r'צאת השבת.*?(\d{1,2}:\d{2})', text_content)
    parsha_match = re.search(r'פרשת ([\u0590-\u05FF\- ]+)', text_content)

    data = {
        "parsha": parsha_match.group(1).strip() if parsha_match else "שבת קודש",
        "candles": candles_match.group(1) if candles_match else "16:00",
        "havdalah": havdalah_match.group(1) if havdalah_match else "17:00",
        "source": "Itim LaBina"
    }
    
    print("Scraped Data:", data)

    # 3. Save to JSON
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scrape_times()