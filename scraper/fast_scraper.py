import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from curl_cffi import requests

class AccuWeatherFastScraper:
    """
    High-performance, resilient scraper using browser TLS impersonation.
    Capable of batch scraping 50+ Philippine locations concurrently.
    """

    def __init__(self, impersonate: str = "chrome124", timeout: int = 15):
        self.impersonate = impersonate
        self.timeout = timeout

    def _get_session(self) -> requests.Session:
        return requests.Session(impersonate=self.impersonate)

    def scrape_single_location(self, location_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scrapes current weather and details for a single Philippine location.
        """
        target_url = location_info.get("accuweather_url", "")
        # Convert to current-weather URL for deep metrics
        current_url = target_url.replace("/weather-today/", "/current-weather/").replace("/weather-forecast/", "/current-weather/")
        
        session = self._get_session()
        result = {
            "location_id": location_info.get("id"),
            "location": location_info.get("name"),
            "province": location_info.get("province"),
            "region": location_info.get("region"),
            "island_group": location_info.get("island_group"),
            "coordinates": location_info.get("coordinates"),
            "source_url": current_url,
            "weather_snapshot": {},
            "raw_details": {}
        }

        try:
            resp = session.get(current_url, headers={"Referer": "https://www.accuweather.com/"}, timeout=self.timeout)
            if resp.status_code == 200:
                parsed = self._parse_html(resp.text)
                if parsed.get("location"):
                    result["location_accuweather"] = parsed["location"]
                if parsed.get("coordinates"):
                    result["coordinates"] = parsed["coordinates"]
                result["weather_snapshot"] = parsed.get("snapshot", {})
                result["raw_details"] = parsed.get("raw_details", {})
            else:
                print(f"[FastScraper] Non-200 status {resp.status_code} for {location_info.get('name')}")
        except Exception as e:
            print(f"[FastScraper] Error fetching {location_info.get('name')}: {e}")

        return result

    def scrape_batch(self, locations: List[Dict[str, Any]], max_workers: int = 8) -> List[Dict[str, Any]]:
        """
        Scrapes a batch of locations concurrently.
        """
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_loc = {executor.submit(self.scrape_single_location, loc): loc for loc in locations}
            for future in as_completed(future_to_loc):
                loc = future_to_loc[future]
                try:
                    data = future.result()
                    results.append(data)
                except Exception as e:
                    print(f"[FastScraper] Exception for {loc.get('name')}: {e}")
        return results

    def _parse_html(self, html: str) -> Dict[str, Any]:
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
                "temperature_c": temp_c,
                "humidity_pct": humidity_pct,
                "real_feel_c": real_feel_c,
                "phrase": phrase,
                "dew_point_c": dew_point_c,
                "wind_speed_kmh": wind_speed_kmh,
                "wind_direction": wind_dir,
                "wind_gusts_kmh": wind_gusts_kmh,
                "uv_index": uv_index,
                "cloud_cover_pct": cloud_cover_pct,
                "pressure_mb": pressure_mb,
                "visibility_km": visibility_km,
                "precipitation_prob_pct": precip_prob_pct,
                "precipitation_mm": rain_amount_mm
            },
            "raw_details": details
        }
