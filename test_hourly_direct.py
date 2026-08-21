from curl_cffi import requests
from bs4 import BeautifulSoup
import re

session = requests.Session(impersonate="chrome124")
url = "https://www.accuweather.com/en/ph/san-jose-del-monte-city/3-262458_1_al/hourly-weather-forecast/3-262458_1_al"
r = session.get(url, headers={"Referer": "https://www.accuweather.com/"}, timeout=10)
soup = BeautifulSoup(r.text, "lxml")

for card in soup.select(".hourly-card-nfl, .hourly-wrapper .accordion-item, .hourly-list-item")[:8]:
    time_elem = card.select_one(".date, .time, h2")
    temp_elem = card.select_one(".temp, .metric")
    rf_elem = card.select_one(".real-feel, .realfeel")
    precip_elem = card.select_one(".precip")
    
    t_text = time_elem.get_text(strip=True) if time_elem else "N/A"
    temp_text = temp_elem.get_text(strip=True) if temp_elem else "N/A"
    rf_text = rf_elem.get_text(" ", strip=True)[:40] if rf_elem else "N/A"
    p_text = precip_elem.get_text(strip=True) if precip_elem else "N/A"
    
    print(f"Time: {t_text} | Temp: {temp_text} | RF: {rf_text} | Precip: {p_text}")
