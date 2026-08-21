from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class Coordinates(BaseModel):
    lat: float
    lon: float

class WeatherSnapshot(BaseModel):
    temperature_c: float
    humidity_pct: float
    real_feel_c: Optional[float] = None
    uv_index: Optional[int] = None
    precipitation_prob_pct: Optional[int] = None
    precipitation_mm: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    wind_direction: Optional[str] = None
    wind_gusts_kmh: Optional[float] = None
    dew_point_c: Optional[float] = None
    cloud_cover_pct: Optional[float] = None
    pressure_mb: Optional[float] = None
    visibility_km: Optional[float] = None
    phrase: Optional[str] = None

class HourlyForecastItem(BaseModel):
    hour: str
    hour_24: int
    temp_c: float
    humidity_pct: float
    real_feel_c: Optional[float] = None
    precip_prob_pct: Optional[int] = None
    heat_index_c: Optional[float] = None
    heat_index_f: Optional[float] = None
    risk_level: Optional[str] = None
    badge: Optional[str] = None
    is_peak_window: Optional[bool] = False
    phrase: Optional[str] = None
    adaptive_ac_watts: Optional[float] = None

class HeatIndexEvaluation(BaseModel):
    ambient_temp_c: float
    relative_humidity_pct: float
    heat_index_c: float
    heat_index_f: float
    risk_level: str
    badge: str
    advisory: str
    adaptive_ac_power_1100w: float
    adaptive_ac_power_820w: float

class LocationWeatherForecast(BaseModel):
    location_id: str
    location: str
    province: str
    region: str
    island_group: str
    coordinates: Coordinates
    source_url: str
    timestamp: str
    weather_snapshot: WeatherSnapshot
    heat_index_evaluation: HeatIndexEvaluation
    hourly_forecast: List[HourlyForecastItem] = []
    load_profile_curve: List[Dict[str, Any]] = []
