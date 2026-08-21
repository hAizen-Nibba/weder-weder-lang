import sys
import os
import json
import unittest

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from fastapi.testclient import TestClient
from server import app
from core.engine import PowerForecastEngine
from core.ph_locations import PhilippineLocationResolver

class LocalIntegrationTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_heat_index_math(self):
        print("\n[TEST 1] Verifying NOAA Rothfusz Heat Index Mathematical Engine...")
        # 33.5C, 72% RH (from information.md benchmark)
        res = PowerForecastEngine.calculate_heat_index(33.5, 72.0)
        self.assertAlmostEqual(res["heat_index_c"], 44.7, delta=1.5)
        self.assertIn(res["risk_level"], ["Extreme Caution", "Danger"])
        print(f"  ✓ 33.5 C @ 72% RH -> Heat Index: {res['heat_index_c']} C ({res['heat_index_f']} F) [{res['risk_level']}]")

        # Inverter AC adaptive calculation
        sharp_watts = PowerForecastEngine.estimate_adaptive_ac_power(1100.0, res["heat_index_c"])
        self.assertGreaterEqual(sharp_watts, 1100.0)
        print(f"  ✓ SHARP 1100W Inverter AC modulated power draw: {sharp_watts} W")

    def test_02_philippines_locations(self):
        print("\n[TEST 2] Verifying Philippine Location Registry & Primary Target...")
        primary = PhilippineLocationResolver.get_primary_target()
        self.assertEqual(primary["name"], "San Jose del Monte City")
        self.assertEqual(primary["province"], "Bulacan")
        print(f"  ✓ Primary Target: {primary['name']}, {primary['province']} (Lat {primary['coordinates']['lat']}, Lon {primary['coordinates']['lon']})")

        all_locs = PhilippineLocationResolver.get_all_locations()
        self.assertGreaterEqual(len(all_locs), 40)
        print(f"  ✓ Nationwide Coverage: {len(all_locs)} predefined cities across NCR, Luzon, Visayas, Mindanao")

    def test_03_data_files_integrity(self):
        print("\n[TEST 3] Verifying Generated Data Files Integrity...")
        sjdm_path = os.path.join("data", "san_jose_del_monte.json")
        ph_path = os.path.join("data", "philippines_latest.json")
        csv_path = os.path.join("data", "philippines_summary.csv")

        self.assertTrue(os.path.exists(sjdm_path), "Missing data/san_jose_del_monte.json")
        self.assertTrue(os.path.exists(ph_path), "Missing data/philippines_latest.json")
        self.assertTrue(os.path.exists(csv_path), "Missing data/philippines_summary.csv")

        with open(sjdm_path, "r", encoding="utf-8") as f:
            sjdm = json.load(f)
            self.assertIn("weather_snapshot", sjdm)
            self.assertIn("heat_index_evaluation", sjdm)
            self.assertIn("hourly_forecast", sjdm)
            print(f"  ✓ San Jose del Monte Dataset: {sjdm['location']}, Temp: {sjdm['weather_snapshot']['temperature_c']} C, HI: {sjdm['heat_index_evaluation']['heat_index_c']} C")

        with open(ph_path, "r", encoding="utf-8") as f:
            ph = json.load(f)
            self.assertGreaterEqual(len(ph), 40)
            print(f"  ✓ Nationwide Dataset: {len(ph)} Philippine cities loaded")

    def test_04_api_version_endpoint(self):
        print("\n[TEST 4] Testing GET /api/version ...")
        resp = self.client.get("/api/version")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("version"), "1.0.3v")
        print(f"  ✓ Version: {data.get('version')}")

    def test_05_api_sanjose_endpoint(self):
        print("\n[TEST 5] Testing GET /api/weather/sanjose ...")
        resp = self.client.get("/api/weather/sanjose")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("San Jose del Monte", data["location"])
        print(f"  ✓ Location: {data['location']}, RealFeel: {data['weather_snapshot'].get('real_feel_c')} C")

    def test_06_api_philippines_endpoint(self):
        print("\n[TEST 6] Testing GET /api/weather/philippines ...")
        resp = self.client.get("/api/weather/philippines")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(len(data), 40)
        print(f"  ✓ Retrieved {len(data)} Philippine city records")

    def test_07_api_search_endpoint(self):
        print("\n[TEST 7] Testing GET /api/weather/search?q=Cebu ...")
        resp = self.client.get("/api/weather/search?q=Cebu")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("Cebu", data["location"])
        print(f"  ✓ Search Resolved: {data['location']} ({data['province']})")

    def test_08_api_forecast_calculate(self):
        print("\n[TEST 8] Testing POST /api/forecast/calculate ...")
        payload = {
            "temperature_c": 32.0,
            "humidity_pct": 75.0,
            "effective_tariff_rate": 14.82
        }
        resp = self.client.post("/api/forecast/calculate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        hi = data["heat_index_evaluation"]
        cost = data["schedule_cost_summary"]
        self.assertGreater(hi["heat_index_c"], 35.0)
        self.assertGreater(cost["projected_daily_cost_php"], 0)
        print(f"  ✓ Calculated HI: {hi['heat_index_c']} C, Daily Bill: PHP {cost['projected_daily_cost_php']}, Monthly: PHP {cost['projected_monthly_cost_php']}")

    def test_09_frontend_index_serving(self):
        print("\n[TEST 9] Testing GET / (Web Dashboard Index Serving)...")
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("PowerForecast", resp.text)
        self.assertIn("1.0.3v", resp.text)
        print("  ✓ Web dashboard HTML served successfully with 1.0.3v version badge")

    def test_10_api_suggest_endpoint(self):
        print("\n[TEST 10] Testing GET /api/weather/suggest?q=San ...")
        resp = self.client.get("/api/weather/suggest?q=San")
        self.assertEqual(resp.status_code, 200)
        suggestions = resp.json()
        self.assertGreater(len(suggestions), 0)
        names = [s["name"] for s in suggestions]
        self.assertTrue(any("San Jose del Monte" in n or "San Fernando" in n for n in names))
        print(f"  ✓ Returned {len(suggestions)} suggestions: {names[:3]}")

if __name__ == "__main__":
    print("=" * 70)
    print(" PowerForecast Local Integration & API Test Suite")
    print(" Version: 1.0.0v")
    print("=" * 70)
    unittest.main()
