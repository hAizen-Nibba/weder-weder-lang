import os
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.engine import PowerForecastEngine
from core.ph_locations import PhilippineLocationResolver
from scraper.pipeline import PowerForecastPipeline

app = FastAPI(
    title="PowerForecast Philippines Weather & Heat Index API",
    description="Live AccuWeather Scraper and Heat Index Analytics for the Philippines",
    version="1.0.1v"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = PowerForecastPipeline(data_dir="data")

# Serve Web Frontend Static Files
os.makedirs("web", exist_ok=True)
app.mount("/static", StaticFiles(directory="web"), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join("web", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "PowerForecast API is running. Access /docs for API documentation.", "version": "1.0.1v"}

@app.get("/api/version")
def get_version_info():
    changelog_path = os.path.join("database", "changelog.json")
    if os.path.exists(changelog_path):
        with open(changelog_path, "r", encoding="utf-8") as f:
            changelog = json.load(f)
    else:
        changelog = []
    return {
        "version": "1.0.1v",
        "app_name": "PowerForecast (Meralco Energy Intel & Smart Scheduler)",
        "primary_location": "San Jose del Monte City, Bulacan, Philippines",
        "changelog": changelog
    }

@app.get("/api/weather/sanjose")
def get_san_jose_weather(refresh: bool = False):
    filepath = os.path.join("data", "san_jose_del_monte.json")
    if not refresh and os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return pipeline.run_san_jose_del_monte()

@app.get("/api/weather/philippines")
def get_all_philippines_weather(refresh: bool = False):
    filepath = os.path.join("data", "philippines_latest.json")
    if not refresh and os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return pipeline.run_nationwide_philippines()

@app.get("/api/weather/search")
def search_and_scrape_philippines_city(q: str = Query(..., description="Philippine city/municipality name")):
    q_clean = q.strip()
    # 1. Check if it matches predefined
    predefined = PhilippineLocationResolver.search_predefined(q_clean)
    if predefined:
        target = predefined[0]
        return pipeline.process_location(target, include_hourly=True)

    # 2. Try live AccuWeather autocomplete
    live_results = PhilippineLocationResolver.query_accuweather_autocomplete(q_clean)
    if live_results:
        target = live_results[0]
        return pipeline.process_location(target, include_hourly=True)

    return JSONResponse(status_code=404, content={"error": f"No Philippine location found matching '{q}'"})

class ApplianceTask(BaseModel):
    name: str
    watts: float
    hours_active: float

class SimulationRequest(BaseModel):
    temperature_c: float
    humidity_pct: float
    effective_tariff_rate: float = 14.82
    appliances: Optional[List[ApplianceTask]] = None

@app.post("/api/forecast/calculate")
def calculate_forecast(req: SimulationRequest):
    hi_eval = PowerForecastEngine.calculate_heat_index(req.temperature_c, req.humidity_pct)
    hi_c = hi_eval["heat_index_c"]

    # Compute dynamic power for AC units
    sharp_watts = PowerForecastEngine.estimate_adaptive_ac_power(1100.0, hi_c)
    jhokim_watts = PowerForecastEngine.estimate_adaptive_ac_power(820.0, hi_c)
    hi_eval["adaptive_ac_power_1100w"] = sharp_watts
    hi_eval["adaptive_ac_power_820w"] = jhokim_watts

    # Appliance tasks
    if req.appliances:
        tasks = [t.model_dump() for t in req.appliances]
    else:
        tasks = [
            {"name": "SHARP AH-XP15YMF (Adaptive)", "watts": sharp_watts, "hours_active": 8.0},
            {"name": "jhokim aircon (Adaptive)", "watts": jhokim_watts, "hours_active": 6.0},
            {"name": "Base Home Load (Ref, Lights, WiFi)", "watts": 350.0, "hours_active": 24.0}
        ]

    cost_eval = PowerForecastEngine.calculate_daily_schedule_cost(tasks, effective_tariff_rate=req.effective_tariff_rate)

    return {
        "heat_index_evaluation": hi_eval,
        "schedule_cost_summary": cost_eval,
        "active_tasks": tasks
    }

def find_free_port(start_port: int = 8000) -> int:
    import socket
    for port in [start_port, 8080, 5000, 3000, 8888]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port

if __name__ == "__main__":
    import uvicorn
    import sys
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    else:
        port = find_free_port(8000)
    print(f"Starting PowerForecast Server on http://127.0.0.1:{port} ...")
    uvicorn.run("server:app", host="127.0.0.1", port=port, reload=False)
