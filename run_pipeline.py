import sys
import os
import json

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from scraper.pipeline import PowerForecastPipeline

def main():
    print("=" * 70)
    print(" PowerForecast AccuWeather Ingestion & Heat Index Pipeline")
    print(" Primary Focus: San Jose del Monte City, Bulacan & Nationwide Philippines")
    print(" Version: 1.0.0v")
    print("=" * 70)

    pipeline = PowerForecastPipeline(data_dir="data")

    # 1. Run San Jose del Monte City
    sjdm_data = pipeline.run_san_jose_del_monte()
    snap = sjdm_data["weather_snapshot"]
    hi = sjdm_data["heat_index_evaluation"]

    print("\n" + "=" * 50)
    print(" SAN JOSE DEL MONTE CITY - LIVE REPORT")
    print("=" * 50)
    print(f" Location: {sjdm_data['location']} ({sjdm_data['province']})")
    print(f" Coordinates: Lat {sjdm_data['coordinates']['lat']}, Lon {sjdm_data['coordinates']['lon']}")
    print(f" Air Temperature: {snap['temperature_c']} C")
    print(f" Relative Humidity: {snap['humidity_pct']}%")
    print(f" Perceived RealFeel: {snap.get('real_feel_c', 'N/A')} C")
    print(f" Wind: {snap.get('wind_speed_kmh', 'N/A')} km/h {snap.get('wind_direction', '')}")
    print(f" Precipitation Chance: {snap.get('precipitation_prob_pct', 'N/A')}%")
    print(f" NOAA Heat Index: {hi['heat_index_c']} C ({hi['heat_index_f']} F)")
    print(f" PAGASA Risk Level: [{hi['risk_level']}]")
    print(f" Advisory: {hi['advisory']}")
    print(f" Adaptive AC Power (Sharp 1100W Inverter): {hi['adaptive_ac_power_1100w']} Watts")
    print(f" Adaptive AC Power (jhokim 820W): {hi['adaptive_ac_power_820w']} Watts")
    print("=" * 50)

    # 2. Run Nationwide Ingestion
    print("\nRunning nationwide Philippine regional ingestion...")
    all_locations = pipeline.run_nationwide_philippines()
    print(f"\n[Success] Processed {len(all_locations)} Philippine cities and provinces.")
    print("Outputs saved in /data directory:")
    print(" - data/san_jose_del_monte.json")
    print(" - data/philippines_latest.json")
    print(" - data/philippines_summary.csv")

if __name__ == "__main__":
    main()
