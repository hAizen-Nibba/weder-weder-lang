import unittest
from core.engine import PowerForecastEngine
from core.ph_locations import PhilippineLocationResolver
from core.models import LocationWeatherForecast

class TestPowerForecastEngine(unittest.TestCase):
    def test_heat_index_normal(self):
        # 24C, 50% RH -> mild / normal
        res = PowerForecastEngine.calculate_heat_index(24.0, 50.0)
        self.assertLess(res["heat_index_c"], 27.0)
        self.assertEqual(res["risk_level"], "Normal / Safe")

    def test_heat_index_extreme_caution(self):
        # 33.5C, 72% RH (from information.md test execution)
        res = PowerForecastEngine.calculate_heat_index(33.5, 72.0)
        self.assertGreaterEqual(res["heat_index_c"], 33.0)
        self.assertEqual(res["risk_level"], "Extreme Caution" if res["heat_index_c"] < 42.0 else "Danger")

    def test_heat_index_danger(self):
        # 38C, 80% RH -> Danger
        res = PowerForecastEngine.calculate_heat_index(38.0, 80.0)
        self.assertGreaterEqual(res["heat_index_c"], 42.0)
        self.assertIn(res["risk_level"], ["Danger", "Extreme Danger"])

    def test_adaptive_ac_power(self):
        # Baseline setpoint 24C. At HI = 37.4C, delta T = 13.4C. Duty factor = 0.40 + 0.05*13.4 = 1.07 -> clamped to 1.05
        # 1100 * 1.05 = 1155.0 W
        watts = PowerForecastEngine.estimate_adaptive_ac_power(1100.0, 37.4, 24.0)
        self.assertEqual(watts, 1155.0)

        # Mild day: HI = 25C, delta T = 1.0C -> Duty factor = 0.45 -> 1100 * 0.45 = 495 W
        mild_watts = PowerForecastEngine.estimate_adaptive_ac_power(1100.0, 25.0, 24.0)
        self.assertEqual(mild_watts, 495.0)

    def test_daily_cost_calculation(self):
        tasks = [
            {"name": "SHARP AC", "watts": 1155.0, "hours_active": 8.0},
            {"name": "jhokim AC", "watts": 861.0, "hours_active": 6.0}
        ]
        res = PowerForecastEngine.calculate_daily_schedule_cost(tasks, effective_tariff_rate=14.82)
        expected_kwh = (1155.0 * 8.0 + 861.0 * 6.0) / 1000.0
        self.assertAlmostEqual(res["scheduled_energy_kwh"], expected_kwh, places=2)
        self.assertAlmostEqual(res["projected_daily_cost_php"], round(expected_kwh * 14.82, 2), places=1)

    def test_philippine_locations_count(self):
        locs = PhilippineLocationResolver.get_all_locations()
        self.assertGreaterEqual(len(locs), 40)
        primary = PhilippineLocationResolver.get_primary_target()
        self.assertEqual(primary["name"], "San Jose del Monte City")

if __name__ == "__main__":
    unittest.main()
