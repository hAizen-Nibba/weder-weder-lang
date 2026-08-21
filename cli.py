import sys
import os
import json

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from core.engine import PowerForecastEngine
from core.ph_locations import PhilippineLocationResolver
from scraper.pipeline import PowerForecastPipeline

def print_banner():
    print("""
================================================================================
   ____                           ______                                _   
  / __ \____ _      _____  _____ / ____/___  ________  _________ ______/ /_ 
 / /_/ / __ \ | /| / / _ \/ ___// /_  / __ \/ ___/ _ \/ ___/ __ `/ ___/ __/ 
/ ____/ /_/ / |/ |/ /  __/ /   / __/ / /_/ / /  /  __/ /__/ /_/ (__  ) /_   
/_/    \____/|__/|__/\___/_/   /_/    \____/_/   \___/\___/\__,_/____/\__/    
                 AccuWeather Scraper & Heat Index Engine
            San Jose del Monte City, Bulacan & Whole Philippines
                               Version: 1.0.0v
================================================================================
    """)

def display_city_card(data: dict):
    snap = data.get("weather_snapshot", {})
    hi = data.get("heat_index_evaluation", {})
    coords = data.get("coordinates", {})
    
    print("\n" + "=" * 65)
    print(f" LOCATION: {data.get('location')} ({data.get('province')})")
    print(f" Region: {data.get('region')} | Island Group: {data.get('island_group')}")
    print(f" Coordinates: Lat {coords.get('lat')}, Lon {coords.get('lon')}")
    print("-" * 65)
    print(f" Air Temperature      : {snap.get('temperature_c')} C")
    print(f" Relative Humidity    : {snap.get('humidity_pct')}%")
    print(f" Perceived RealFeel   : {snap.get('real_feel_c', 'N/A')} C")
    print(f" Weather Condition    : {snap.get('phrase', 'N/A')}")
    print(f" Wind                 : {snap.get('wind_speed_kmh', 'N/A')} km/h {snap.get('wind_direction', '')}")
    print(f" Rain Probability     : {snap.get('precipitation_prob_pct', 'N/A')}%")
    print("-" * 65)
    print(f" NOAA HEAT INDEX      : {hi.get('heat_index_c')} C ({hi.get('heat_index_f')} F)")
    print(f" PAGASA RISK TIER     : [{hi.get('risk_level')}]")
    print(f" Thermal Advisory     : {hi.get('advisory')}")
    print("-" * 65)
    print(f" Dynamic AC Draw (SHARP 1100W Inverter) : {hi.get('adaptive_ac_power_1100w')} W")
    print(f" Dynamic AC Draw (jhokim 820W Inverter) : {hi.get('adaptive_ac_power_820w')} W")
    print("=" * 65)

def run_appliance_simulation(heat_index_c: float = 37.0):
    print("\n--- PowerForecast Appliance & Smart Scheduling Simulator ---")
    print(f"Current Outdoor Heat Index Baseline: {heat_index_c} C")
    
    sharp_watts = PowerForecastEngine.estimate_adaptive_ac_power(1100.0, heat_index_c)
    jhokim_watts = PowerForecastEngine.estimate_adaptive_ac_power(820.0, heat_index_c)
    
    tasks = [
        {"name": "SHARP AH-XP15YMF Inverter AC (1100W)", "watts": sharp_watts, "hours_active": 8.0},
        {"name": "jhokim aircon (820W)", "watts": jhokim_watts, "hours_active": 6.0},
        {"name": "Inverter Refrigerator (200W)", "watts": 140.0, "hours_active": 24.0},
        {"name": "Lighting & Home Electronics", "watts": 180.0, "hours_active": 12.0},
        {"name": "Electric Flat Iron (Discretionary)", "watts": 1000.0, "hours_active": 1.5}
    ]

    rate = 14.82  # Meralco effective tariff PHP / kWh
    res = PowerForecastEngine.calculate_daily_schedule_cost(tasks, effective_tariff_rate=rate)

    print("\nScheduled Home Load Sessions:")
    for t in tasks:
        kwh = (t["watts"] * t["hours_active"]) / 1000.0
        cost = kwh * rate
        print(f" • {t['name']:<42}: {t['watts']:>6.1f} W x {t['hours_active']:>4.1f} hrs = {kwh:>6.2f} kWh (PHP {cost:>6.2f}/day)")

    print("-" * 65)
    print(f" Total Daily Consumption : {res['scheduled_energy_kwh']} kWh")
    print(f" Total Monthly Est. (30d): {res['monthly_energy_kwh']} kWh")
    print(f" Projected Daily Cost    : PHP {res['projected_daily_cost_php']}")
    print(f" Projected Monthly Bill  : PHP {res['projected_monthly_cost_php']} (at PHP {rate}/kWh)")
    print("-" * 65)
    print(" Smart Scheduling Advisory:")
    print("  * Peak Window Warning: 11:00 AM - 4:00 PM and 6:00 PM - 9:00 PM.")
    print("  * Pre-cool rooms at 10:00 AM before extreme afternoon heat index peaks.")
    print("  * Defer discretionary 1000W flat iron to off-peak hours (after 9:00 PM).")

def main():
    pipeline = PowerForecastPipeline()
    print_banner()

    while True:
        print("\n=== Main Menu ===")
        print("1. Scrape San Jose del Monte City, Bulacan (Primary Target)")
        print("2. Scrape & Update Whole Philippines (All 17 Regions, 46+ Cities)")
        print("3. Filter & View by Island Group (NCR, Luzon, Visayas, Mindanao)")
        print("4. Dynamic Search: Lookup & Scrape Any Philippine Municipality")
        print("5. Run Smart Appliance Scheduler & Meralco Billing Simulation")
        print("6. View Version & Changelog Audit (1.0.0v)")
        print("7. Exit")
        
        choice = input("\nEnter choice (1-7): ").strip()

        if choice == "1":
            data = pipeline.run_san_jose_del_monte()
            display_city_card(data)
        elif choice == "2":
            dataset = pipeline.run_nationwide_philippines()
            print(f"\n[Completed] Processed {len(dataset)} Philippine cities.")
        elif choice == "3":
            print("\nSelect Island Group:")
            print("a. National Capital Region (NCR)")
            print("b. Luzon")
            print("c. Visayas")
            print("d. Mindanao")
            g = input("Choice (a-d): ").strip().lower()
            group_map = {"a": "Luzon", "b": "Luzon", "c": "Visayas", "d": "Mindanao"}
            target_group = group_map.get(g, "Luzon")
            
            locs = PhilippineLocationResolver.filter_by_island_group(target_group)
            print(f"\nIngesting {len(locs)} locations for {target_group}...")
            for loc in locs[:10]:
                d = pipeline.process_location(loc, include_hourly=False)
                display_city_card(d)
        elif choice == "4":
            query = input("\nEnter Philippine city or municipality name (e.g. Malolos, Baguio, Cebu, Marilao): ").strip()
            print(f"Searching AccuWeather autocomplete for '{query}'...")
            results = PhilippineLocationResolver.query_accuweather_autocomplete(query)
            if not results:
                # Try predefined
                results = PhilippineLocationResolver.search_predefined(query)
            
            if results:
                print(f"Found {len(results)} matching location(s):")
                for i, r in enumerate(results[:5]):
                    print(f" [{i+1}] {r['name']} ({r['province']})")
                sel = input("Select location (1-5) or Enter for first: ").strip()
                idx = int(sel) - 1 if sel.isdigit() and 1 <= int(sel) <= len(results) else 0
                chosen = results[idx]
                print(f"\nIngesting live weather for {chosen['name']}...")
                d = pipeline.process_location(chosen, include_hourly=True)
                display_city_card(d)
            else:
                print("No matching Philippine location found.")
        elif choice == "5":
            # Load San Jose del Monte heat index or default
            sjdm_path = os.path.join("data", "san_jose_del_monte.json")
            hi = 37.0
            if os.path.exists(sjdm_path):
                with open(sjdm_path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    hi = d.get("heat_index_evaluation", {}).get("heat_index_c", 37.0)
            run_appliance_simulation(hi)
        elif choice == "6":
            cl_path = os.path.join("database", "changelog.json")
            if os.path.exists(cl_path):
                with open(cl_path, "r", encoding="utf-8") as f:
                    cl = json.load(f)
                    print("\n" + json.dumps(cl, indent=2))
            else:
                print("Version: 1.0.0v")
        elif choice == "7":
            print("Exiting PowerForecast CLI. Goodbye!")
            break
        else:
            print("Invalid selection. Please choose 1-7.")

if __name__ == "__main__":
    main()
