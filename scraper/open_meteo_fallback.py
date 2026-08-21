import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

class OpenMeteoFallbackEngine:
    """
    Fallback & Enrichment Engine using Open-Meteo API.
    As documented in information.md Section 2.1:
    'Coordinates for API fallback (Open-Meteo): Latitude 14.8137, Longitude 121.0453'
    """

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    @staticmethod
    def fetch_weather_and_hourly(lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Fetches current weather and 24-hour hourly forecast from Open-Meteo.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation",
                "weather_code",
                "cloud_cover",
                "pressure_msl",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m"
            ],
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation_probability",
                "precipitation",
                "weather_code",
                "direct_radiation"
            ],
            "timezone": "Asia/Manila",
            "forecast_days": 2
        }

        try:
            resp = requests.get(OpenMeteoFallbackEngine.BASE_URL, params=params, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                
                # Parse current weather snapshot
                curr = data.get("current", {})
                temp_c = curr.get("temperature_2m")
                hum_pct = curr.get("relative_humidity_2m")
                real_feel = curr.get("apparent_temperature")
                wind_spd = curr.get("wind_speed_10m")
                wind_gust = curr.get("wind_gusts_10m")
                wind_dir_deg = curr.get("wind_direction_10m")
                cloud_cov = curr.get("cloud_cover")
                pressure = curr.get("pressure_msl")
                precip = curr.get("precipitation")

                # Wind direction text
                wind_dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
                wind_dir_str = "E"
                if wind_dir_deg is not None:
                    idx = int((wind_dir_deg + 11.25) / 22.5) % 16
                    wind_dir_str = wind_dirs[idx]

                # Parse hourly 24 hours
                hourly_raw = data.get("hourly", {})
                times = hourly_raw.get("time", [])
                temps = hourly_raw.get("temperature_2m", [])
                hums = hourly_raw.get("relative_humidity_2m", [])
                app_temps = hourly_raw.get("apparent_temperature", [])
                precip_probs = hourly_raw.get("precipitation_probability", [])

                # Find current hour index
                now_str = datetime.now().strftime("%Y-%m-%dT%H:00")
                start_idx = 0
                for i, t in enumerate(times):
                    if t >= now_str:
                        start_idx = i
                        break

                hourly_list = []
                for i in range(start_idx, min(start_idx + 24, len(times))):
                    t_str = times[i]
                    dt = datetime.fromisoformat(t_str)
                    hour_display = dt.strftime("%I %p").lstrip("0")
                    hour_24 = dt.hour
                    
                    hourly_list.append({
                        "hour": hour_display,
                        "hour_24": hour_24,
                        "time_iso": t_str,
                        "temp_c": round(temps[i], 1) if i < len(temps) else temp_c,
                        "humidity_pct": round(hums[i], 1) if i < len(hums) else hum_pct,
                        "real_feel_c": round(app_temps[i], 1) if i < len(app_temps) else real_feel,
                        "precip_prob_pct": int(precip_probs[i]) if i < len(precip_probs) and precip_probs[i] is not None else 0,
                        "phrase": "Clear/Fair" if hums[i] < 70 else "Humid/Overcast"
                    })

                return {
                    "temperature_c": temp_c,
                    "humidity_pct": hum_pct,
                    "real_feel_c": real_feel,
                    "wind_speed_kmh": wind_spd,
                    "wind_direction": wind_dir_str,
                    "wind_gusts_kmh": wind_gust,
                    "cloud_cover_pct": cloud_cov,
                    "pressure_mb": pressure,
                    "precipitation_mm": precip,
                    "precipitation_prob_pct": hourly_list[0]["precip_prob_pct"] if hourly_list else 20,
                    "hourly_forecast": hourly_list,
                    "source": "Open-Meteo Enriched API"
                }
        except Exception as e:
            print(f"[OpenMeteoFallback] Error fetching coordinates ({lat}, {lon}): {e}")
        return None
