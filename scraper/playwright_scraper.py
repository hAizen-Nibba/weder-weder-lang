import asyncio
import re
import json
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

class AccuWeatherPlaywrightScraper:
    """
    Playwright-based scraper for AccuWeather pages.
    Navigates to weather-today, current-weather, and hourly-weather-forecast pages.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless

    async def scrape_location_url(self, target_url: str, location_name: str = "") -> Dict[str, Any]:
        """
        Scrapes an AccuWeather page using Playwright.
        """
        # Ensure target is current-weather or today
        current_url = target_url.replace("/weather-today/", "/current-weather/").replace("/weather-forecast/", "/current-weather/")
        hourly_url = target_url.replace("/weather-today/", "/hourly-weather-forecast/").replace("/current-weather/", "/hourly-weather-forecast/").replace("/weather-forecast/", "/hourly-weather-forecast/")
        
        async with async_playwright() as p:
            # Launch Firefox or Chromium
            try:
                browser = await p.firefox.launch(headless=self.headless)
            except Exception:
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=['--disable-http2', '--disable-blink-features=AutomationControlled', '--no-sandbox']
                )

            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
                viewport={'width': 1280, 'height': 800},
                locale='en-US',
                timezone_id='Asia/Manila'
            )
            page = await context.new_page()

            result = {
                "location": location_name or "Philippines",
                "source_url": target_url,
                "weather_snapshot": {},
                "hourly_forecast": [],
                "raw_details": {}
            }

            try:
                # 1. Scrape Current Weather Page
                print(f"[Playwright] Navigating to current weather: {current_url}")
                await page.goto(current_url, wait_until="domcontentloaded", timeout=25000)
                await page.wait_for_timeout(2000)
                content = await page.content()
                
                parsed_current = self._parse_current_html(content)
                result["location"] = parsed_current.get("location") or result["location"]
                result["coordinates"] = parsed_current.get("coordinates")
                result["weather_snapshot"] = parsed_current.get("snapshot", {})
                result["raw_details"] = parsed_current.get("raw_details", {})

                # 2. Scrape Hourly Forecast Page
                print(f"[Playwright] Navigating to hourly forecast: {hourly_url}")
                await page.goto(hourly_url, wait_until="domcontentloaded", timeout=25000)
                await page.wait_for_timeout(2000)
                hourly_content = await page.content()
                
                parsed_hourly = self._parse_hourly_html(hourly_content)
                result["hourly_forecast"] = parsed_hourly

            except Exception as e:
                print(f"[Playwright] Error during scrape: {e}")
            finally:
                await browser.close()

            return result

    def _parse_current_html(self, html: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "lxml")
        
        # 1. Geo info from JSON-LD
        location_name = None
        lat, lon = None, None
        for s in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(s.string)
                if data.get("@type") == "Place":
                    location_name = data.get("name")
                    geo = data.get("geo", {})
                    lat = float(geo.get("latitude", 0))
                    lon = float(geo.get("longitude", 0))
            except:
                pass

        # 2. Main Card
        temp_c = None
        real_feel_c = None
        phrase = None

        temp_elem = soup.select_one(".current-weather-card .temp, .cur-con-weather-card__body .temp, .header-temp, .temp")
        if temp_elem:
            m = re.search(r"(-?\d+)", temp_elem.get_text())
            if m:
                temp_c = float(m.group(1))

        rf_elem = soup.select_one(".current-weather-card .real-feel, .real-feel")
        if rf_elem:
            m = re.search(r"(-?\d+)", rf_elem.get_text())
            if m:
                real_feel_c = float(m.group(1))

        phrase_elem = soup.select_one(".current-weather-card .phrase, .phrase, .half-day-card .phrase")
        if phrase_elem:
            phrase = phrase_elem.get_text(strip=True)

        # 3. Details
        details = {}
        for item in soup.select(".current-weather-details .detail-item, .spaced-content, .panel-item"):
            txt = item.get_text(" | ", strip=True)
            parts = [p.strip() for p in txt.split("|") if p.strip()]
            if len(parts) >= 2:
                key = parts[0].lower()
                val = parts[1]
                details[key] = val

        humidity_pct = None
        wind_speed_kmh = None
        wind_dir = None
        wind_gusts_kmh = None
        uv_index = None
        dew_point_c = None
        cloud_cover_pct = None
        pressure_mb = None
        visibility_km = None
        precip_prob_pct = None
        rain_amount_mm = None

        for k, v in details.items():
            if "humidity" in k and "indoor" not in k:
                m = re.search(r"(\d+)%", v)
                if m: humidity_pct = float(m.group(1))
            elif "wind gusts" in k:
                m = re.search(r"(\d+)", v)
                if m: wind_gusts_kmh = float(m.group(1))
            elif "wind" in k and "gusts" not in k:
                m = re.search(r"([A-Z]+)\s+(\d+)", v)
                if m:
                    wind_dir = m.group(1)
                    wind_speed_kmh = float(m.group(2))
            elif "uv index" in k:
                m = re.search(r"(\d+)", v)
                if m: uv_index = int(m.group(1))
            elif "dew point" in k:
                m = re.search(r"(-?\d+)", v)
                if m: dew_point_c = float(m.group(1))
            elif "cloud cover" in k:
                m = re.search(r"(\d+)%", v)
                if m: cloud_cover_pct = float(m.group(1))
            elif "pressure" in k:
                m = re.search(r"([\d\.]+)", v)
                if m: pressure_mb = float(m.group(1))
            elif "visibility" in k:
                m = re.search(r"([\d\.]+)", v)
                if m: visibility_km = float(m.group(1))
            elif "probability of precipitation" in k:
                m = re.search(r"(\d+)%", v)
                if m: precip_prob_pct = int(m.group(1))
            elif "rain amount" in k or "precipitation" in k:
                m = re.search(r"([\d\.]+)", v)
                if m: rain_amount_mm = float(m.group(1))

        return {
            "location": location_name,
            "coordinates": {"lat": lat, "lon": lon} if lat and lon else None,
            "snapshot": {
                "temperature_c": temp_c or 30.0,
                "humidity_pct": humidity_pct or 75.0,
                "real_feel_c": real_feel_c,
                "phrase": phrase or "Clear / Humid",
                "dew_point_c": dew_point_c,
                "wind_speed_kmh": wind_speed_kmh,
                "wind_direction": wind_dir,
                "wind_gusts_kmh": wind_gusts_kmh,
                "uv_index": uv_index or 5,
                "cloud_cover_pct": cloud_cover_pct,
                "pressure_mb": pressure_mb,
                "visibility_km": visibility_km,
                "precipitation_prob_pct": precip_prob_pct or 20,
                "precipitation_mm": rain_amount_mm
            },
            "raw_details": details
        }

    def _parse_hourly_html(self, html: str) -> list:
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select(".hourly-card-nfl, .hourly-wrapper .accordion-item, .hourly-list-item")
        hourly = []

        for card in cards:
            time_elem = card.select_one(".date, .time, .hourly-card-nfl-header .date") or card.select_one("h2")
            temp_elem = card.select_one(".temp, .metric, .hourly-card-nfl-content .temp")
            rf_elem = card.select_one(".real-feel, .realfeel")
            phrase_elem = card.select_one(".phrase, .cond")
            precip_elem = card.select_one(".precip, [data-qa='precip']")

            if time_elem and temp_elem:
                time_str = time_elem.get_text(strip=True)
                temp_str = temp_elem.get_text(strip=True)
                m_temp = re.search(r"(-?\d+)", temp_str)
                temp_val = float(m_temp.group(1)) if m_temp else 30.0

                rf_val = None
                if rf_elem:
                    m_rf = re.search(r"RealFeel.*?(\d+)", rf_elem.get_text())
                    if m_rf:
                        rf_val = float(m_rf.group(1))

                precip_val = None
                if precip_elem:
                    m_p = re.search(r"(\d+)%", precip_elem.get_text())
                    if m_p:
                        precip_val = int(m_p.group(1))

                phrase_val = phrase_elem.get_text(strip=True) if phrase_elem else "Partly Cloudy"

                # Parse hour integer
                hour_24 = 12
                try:
                    if "PM" in time_str:
                        h = int(re.search(r"(\d+)", time_str).group(1))
                        hour_24 = h + 12 if h != 12 else 12
                    elif "AM" in time_str:
                        h = int(re.search(r"(\d+)", time_str).group(1))
                        hour_24 = h if h != 12 else 0
                except:
                    pass

                hourly.append({
                    "hour": time_str,
                    "hour_24": hour_24,
                    "temp_c": temp_val,
                    "humidity_pct": 75.0,  # baseline if inner accordion not opened
                    "real_feel_c": rf_val,
                    "precip_prob_pct": precip_val or 15,
                    "phrase": phrase_val
                })

        return hourly

def run_playwright_scrape_sync(target_url: str, location_name: str = "") -> Dict[str, Any]:
    """Synchronous entry point for Playwright scraper."""
    scraper = AccuWeatherPlaywrightScraper(headless=True)
    return asyncio.run(scraper.scrape_location_url(target_url, location_name))
