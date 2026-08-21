import os
import json
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional

from core.engine import PowerForecastEngine
from core.ph_locations import PhilippineLocationResolver
from scraper.fast_scraper import AccuWeatherFastScraper
from scraper.open_meteo_fallback import OpenMeteoFallbackEngine

class PowerForecastPipeline:
    """
    Unified Ingestion & Analytics Pipeline.
    Integrates live weather scraping with PowerForecast heat index calculations.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs("database", exist_ok=True)
        self.fast_scraper = AccuWeatherFastScraper()

    def process_location(self, location_info: Dict[str, Any], include_hourly: bool = True) -> Dict[str, Any]:
        """
        Scrapes and computes heat index metrics for a single location.
        """
        # 1. Scrape live data from AccuWeather
        scraped = self.fast_scraper.scrape_single_location(location_info)
        snapshot = scraped.get("weather_snapshot", {})
        coords = scraped.get("coordinates") or location_info.get("coordinates", {"lat": 14.8137, "lon": 121.0453})

        # Check if we have valid temp and humidity
        temp_c = snapshot.get("temperature_c")
        hum_pct = snapshot.get("humidity_pct")
        hourly_forecast = []

        # 2. Extract live AccuWeather hourly if available
        hourly_forecast = scraped.get("hourly_forecast", [])

        # 3. Validate and enrich with Open-Meteo fallback for remaining 24 hours or if missing
        is_baguio = "baguio" in str(location_info.get("id", "")).lower()
        min_valid_temp = 14.0 if is_baguio else 18.0
        is_invalid_temp = temp_c is None or temp_c < min_valid_temp or temp_c > 48.0
        is_invalid_hum = hum_pct is None or hum_pct < 20.0 or hum_pct > 100.0

        if len(hourly_forecast) < 24 or is_invalid_temp or is_invalid_hum:
            enriched = OpenMeteoFallbackEngine.fetch_weather_and_hourly(coords["lat"], coords["lon"])
            if enriched:
                if is_invalid_temp:
                    temp_c = enriched.get("temperature_c")
                    snapshot["temperature_c"] = temp_c
                if is_invalid_hum:
                    hum_pct = enriched.get("humidity_pct")
                    snapshot["humidity_pct"] = hum_pct
                if snapshot.get("real_feel_c") is None:
                    snapshot["real_feel_c"] = enriched.get("real_feel_c")
                if snapshot.get("wind_speed_kmh") is None:
                    snapshot["wind_speed_kmh"] = enriched.get("wind_speed_kmh")
                if snapshot.get("wind_direction") is None:
                    snapshot["wind_direction"] = enriched.get("wind_direction")
                if snapshot.get("precipitation_prob_pct") is None:
                    snapshot["precipitation_prob_pct"] = enriched.get("precipitation_prob_pct")
                
                om_hourly = enriched.get("hourly_forecast", [])
                
                if not hourly_forecast:
                    # Calibrate Open-Meteo curve to match live ground reading at current hour
                    delta_temp = (temp_c - om_hourly[0]["temp_c"]) if om_hourly and temp_c else 0.0
                    calibrated_hourly = []
                    for h in om_hourly:
                        calibrated_hourly.append({
                            **h,
                            "temp_c": round(h["temp_c"] + delta_temp, 1),
                            "humidity_pct": h["humidity_pct"]
                        })
                    hourly_forecast = calibrated_hourly
                else:
                    # Merge AccuWeather live hours with remaining Open-Meteo hours
                    existing_hours = {h["hour_24"] for h in hourly_forecast}
                    for h in om_hourly:
                        if h["hour_24"] not in existing_hours and len(hourly_forecast) < 24:
                            hourly_forecast.append(h)
                            existing_hours.add(h["hour_24"])

        # Default fallbacks if both third parties had partial drops
        temp_c = float(temp_c) if temp_c is not None else 31.5
        hum_pct = float(hum_pct) if hum_pct is not None else 72.0
        snapshot["temperature_c"] = round(temp_c, 1)
        snapshot["humidity_pct"] = round(hum_pct, 1)

        # Synchronize first hourly entry with current live snapshot
        if hourly_forecast and len(hourly_forecast) > 0:
            hourly_forecast[0]["temp_c"] = snapshot["temperature_c"]
            hourly_forecast[0]["humidity_pct"] = snapshot["humidity_pct"]
            if snapshot.get("real_feel_c"):
                hourly_forecast[0]["real_feel_c"] = snapshot["real_feel_c"]
            if snapshot.get("precipitation_prob_pct") is not None:
                hourly_forecast[0]["precip_prob_pct"] = snapshot["precipitation_prob_pct"]

        # 3. Calculate NOAA Rothfusz Heat Index
        hi_eval = PowerForecastEngine.calculate_heat_index(temp_c, hum_pct)
        hi_c = hi_eval["heat_index_c"]

        # 4. Adaptive HVAC Power Calculations
        sharp_ac_watts = PowerForecastEngine.estimate_adaptive_ac_power(1100.0, hi_c)
        jhokim_ac_watts = PowerForecastEngine.estimate_adaptive_ac_power(820.0, hi_c)
        hi_eval["adaptive_ac_power_1100w"] = sharp_ac_watts
        hi_eval["adaptive_ac_power_820w"] = jhokim_ac_watts

        # 5. Compute 24-Hour Load Profile Curve
        load_profile = []
        if hourly_forecast:
            load_profile = PowerForecastEngine.compute_hourly_load_profile(hourly_forecast)

        # 6. Assemble complete JSON object according to information.md Schema
        result = {
            "location_id": location_info.get("id"),
            "location": location_info.get("name"),
            "province": location_info.get("province"),
            "region": location_info.get("region"),
            "island_group": location_info.get("island_group"),
            "coordinates": coords,
            "source_url": location_info.get("accuweather_url"),
            "timestamp": datetime.now().isoformat(),
            "weather_snapshot": snapshot,
            "heat_index_evaluation": hi_eval,
            "hourly_forecast": hourly_forecast[:24],
            "load_profile_curve": load_profile
        }

        return result

    def run_san_jose_del_monte(self) -> Dict[str, Any]:
        """
        Executes dedicated deep ingestion for San Jose del Monte City, Bulacan.
        """
        print("\n[Pipeline] Processing primary target: San Jose del Monte City, Bulacan...")
        loc = PhilippineLocationResolver.get_primary_target()
        data = self.process_location(loc, include_hourly=True)
        
        filepath = os.path.join(self.data_dir, "san_jose_del_monte.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[Pipeline] Saved San Jose del Monte dataset to {filepath}")
        return data

    def run_nationwide_philippines(self, max_workers: int = 10) -> List[Dict[str, Any]]:
        """
        Executes nationwide batch ingestion across all Philippine regions.
        """
        print("\n[Pipeline] Ingesting nationwide Philippine locations...")
        locations = PhilippineLocationResolver.get_all_locations()
        all_data = []

        for loc in locations:
            try:
                # Include hourly curve for primary cities, fast snapshot for others
                include_hourly = loc.get("is_primary_target", False) or loc.get("id") in [
                    "manila", "quezon_city", "cebu_city", "davao_city", "baguio", "iloilo_city", "cagayan_de_oro"
                ]
                d = self.process_location(loc, include_hourly=include_hourly)
                all_data.append(d)
                print(f"  [OK] {d['location']} ({d['province']}): {d['weather_snapshot']['temperature_c']} C, HI: {d['heat_index_evaluation']['heat_index_c']} C [{d['heat_index_evaluation']['risk_level']}]")
            except Exception as e:
                print(f"  [ERR] Error processing {loc.get('name')}: {e}")

        # Save comprehensive JSON dataset
        ph_filepath = os.path.join(self.data_dir, "philippines_latest.json")
        with open(ph_filepath, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2)
        print(f"[Pipeline] Saved {len(all_data)} Philippine locations to {ph_filepath}")

        # Save CSV summary
        csv_filepath = os.path.join(self.data_dir, "philippines_summary.csv")
        self._export_csv(all_data, csv_filepath)
        print(f"[Pipeline] Saved CSV summary to {csv_filepath}")

        return all_data

    def _export_csv(self, dataset: List[Dict[str, Any]], filepath: str):
        headers = [
            "Location", "Province", "Region", "Island Group",
            "Air Temp (°C)", "Humidity (%)", "RealFeel (°C)",
            "Heat Index (°C)", "Heat Index (°F)", "Risk Level",
            "Adaptive AC 1100W (Watts)", "Precipitation Prob (%)", "Timestamp"
        ]
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for item in dataset:
                snap = item.get("weather_snapshot", {})
                hi = item.get("heat_index_evaluation", {})
                writer.writerow([
                    item.get("location"),
                    item.get("province"),
                    item.get("region"),
                    item.get("island_group"),
                    snap.get("temperature_c"),
                    snap.get("humidity_pct"),
                    snap.get("real_feel_c"),
                    hi.get("heat_index_c"),
                    hi.get("heat_index_f"),
                    hi.get("risk_level"),
                    hi.get("adaptive_ac_power_1100w"),
                    snap.get("precipitation_prob_pct"),
                    item.get("timestamp")
                ])
