import math
from typing import Dict, Any, List, Optional

class PowerForecastEngine:
    """
    Integrated calculation engine for PowerForecast.
    Handles Heat Index computation (NOAA/Rothfusz), PAGASA risk tiers,
    adaptive HVAC power modulation, 24-hour load forecasting, and Meralco tariff cost estimation.
    """

    # PAGASA / NOAA Risk Thresholds in Celsius
    RISK_LEVELS = [
        {"max_c": 27.0, "level": "Normal / Safe", "badge": "safe", "advisory": "Comfortable thermal conditions. Regular AC operation."},
        {"max_c": 33.0, "level": "Caution", "badge": "caution", "advisory": "Moderate warmth. Maintain standard cooling schedule."},
        {"max_c": 42.0, "level": "Extreme Caution", "badge": "warning", "advisory": "Elevated heat. Pre-cool rooms prior to afternoon peak windows."},
        {"max_c": 52.0, "level": "Danger", "badge": "danger", "advisory": "High heat stress. Prioritize AC; defer high-wattage appliances."},
        {"max_c": float("inf"), "level": "Extreme Danger", "badge": "extreme", "advisory": "Emergency heat levels. Maintain continuous cooling."}
    ]

    # Standard Peak Windows for Philippine Electricity Grids (e.g. Meralco)
    PEAK_WINDOWS = [
        {"start_hour": 11, "end_hour": 16, "name": "Afternoon Peak"},
        {"start_hour": 18, "end_hour": 21, "name": "Evening Peak"}
    ]

    @staticmethod
    def calculate_heat_index(temp_celsius: float, humidity_percent: float) -> Dict[str, Any]:
        """
        Calculates apparent temperature (Heat Index) using NOAA Rothfusz regression with edge adjustments.
        
        Formula:
        1. Convert Celsius to Fahrenheit: Tf = (Tc * 1.8) + 32
        2. Steadman preliminary approximation:
           HI_prelim = 0.5 * (Tf + 61.0 + ((Tf - 68.0) * 1.2) + (RH * 0.094))
        3. If (HI_prelim + Tf)/2 >= 80°F:
           Full 9-term polynomial + low/high humidity edge adjustments.
        4. Convert result back to Celsius: (HI - 32) / 1.8
        """
        if not (0 <= humidity_percent <= 100):
            raise ValueError(f"Humidity must be between 0% and 100%, got {humidity_percent}%")

        tf = (temp_celsius * 1.8) + 32.0
        rh = humidity_percent

        hi_prelim = 0.5 * (tf + 61.0 + ((tf - 68.0) * 1.2) + (rh * 0.094))

        if (hi_prelim + tf) / 2.0 >= 80.0:
            # Full 9-Term Polynomial
            hi = (-42.379
                  + 2.04901523 * tf
                  + 10.14333127 * rh
                  - 0.22475541 * tf * rh
                  - 0.00683783 * (tf ** 2)
                  - 0.05481717 * (rh ** 2)
                  + 0.00122874 * (tf ** 2) * rh
                  + 0.00085282 * tf * (rh ** 2)
                  - 0.00000199 * (tf ** 2) * (rh ** 2))

            # Edge adjustment 1: Low Humidity (RH < 13% and 80 <= Tf <= 112)
            if rh < 13.0 and 80.0 <= tf <= 112.0:
                adj_low = ((13.0 - rh) / 4.0) * math.sqrt(max(0.0, (17.0 - abs(tf - 95.0)) / 17.0))
                hi -= adj_low
            # Edge adjustment 2: High Humidity (RH > 85% and 80 <= Tf <= 87)
            elif rh > 85.0 and 80.0 <= tf <= 87.0:
                adj_high = ((rh - 85.0) / 10.0) * ((87.0 - tf) / 5.0)
                hi += adj_high
        else:
            hi = hi_prelim

        hi_celsius = (hi - 32.0) / 1.8

        # Determine Risk Level and Advisory
        category = "Normal / Safe"
        badge = "safe"
        advisory = "Comfortable thermal conditions. Regular AC operation."
        for tier in PowerForecastEngine.RISK_LEVELS:
            if hi_celsius < tier["max_c"]:
                category = tier["level"]
                badge = tier["badge"]
                advisory = tier["advisory"]
                break

        return {
            "ambient_temp_c": round(temp_celsius, 2),
            "relative_humidity_pct": round(humidity_percent, 1),
            "heat_index_c": round(hi_celsius, 2),
            "heat_index_f": round(hi, 2),
            "risk_level": category,
            "badge": badge,
            "advisory": advisory
        }

    @staticmethod
    def estimate_adaptive_ac_power(
        rated_watts: float,
        heat_index_c: float,
        setpoint_c: float = 24.0
    ) -> float:
        """
        Estimates actual AC power draw modulated by outdoor Heat Index.
        Formula:
        ΔT = max(0.0, HI_c - T_set)
        Duty Factor = Clamp(0.40 + 0.05 * ΔT, 0.35, 1.05)
        Dynamic Watts = Rated Watts * Duty Factor
        """
        delta_t = max(0.0, heat_index_c - setpoint_c)
        duty_factor = max(0.35, min(1.05, 0.40 + (0.05 * delta_t)))
        return round(rated_watts * duty_factor, 2)

    @staticmethod
    def is_peak_hour(hour_24: int) -> bool:
        """Checks if a given 24h hour falls into designated peak demand windows."""
        for window in PowerForecastEngine.PEAK_WINDOWS:
            if window["start_hour"] <= hour_24 < window["end_hour"]:
                return True
        return False

    @staticmethod
    def calculate_daily_schedule_cost(
        tasks: List[Dict[str, Any]],
        effective_tariff_rate: float = 14.82
    ) -> Dict[str, Any]:
        """
        Computes total daily kWh and bill cost from scheduled sessions.
        :param tasks: List of dicts with keys: 'name', 'watts', 'hours_active'
        :param effective_tariff_rate: Rate in PHP/kWh (e.g. 14.82)
        """
        total_kwh = sum((t["watts"] * t["hours_active"]) / 1000.0 for t in tasks)
        monthly_kwh = total_kwh * 30.0
        daily_cost = total_kwh * effective_tariff_rate
        monthly_cost = monthly_kwh * effective_tariff_rate

        return {
            "scheduled_energy_kwh": round(total_kwh, 3),
            "monthly_energy_kwh": round(monthly_kwh, 2),
            "projected_daily_cost_php": round(daily_cost, 2),
            "projected_monthly_cost_php": round(monthly_cost, 2),
            "effective_rate": effective_tariff_rate,
            "task_count": len(tasks)
        }

    @staticmethod
    def compute_hourly_load_profile(
        hourly_forecast: List[Dict[str, Any]],
        appliances: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculates 24-hour dynamic load profile curve based on hourly Heat Index and active appliances.
        """
        if appliances is None:
            appliances = [
                {"name": "SHARP AH-XP15YMF Inverter AC", "rated_watts": 1100.0, "is_hvac": True, "active_hours": list(range(10, 24))},
                {"name": "jhokim aircon", "rated_watts": 820.0, "is_hvac": True, "active_hours": list(range(12, 18))},
                {"name": "Base Home Load (Ref, Lights, Router)", "rated_watts": 350.0, "is_hvac": False, "active_hours": list(range(0, 24))}
            ]

        profile = []
        for entry in hourly_forecast:
            hour_str = str(entry.get("hour", "00:00"))
            # Parse hour integer
            hour_int = 0
            if ":" in hour_str:
                try:
                    hour_int = int(hour_str.split(":")[0])
                except:
                    pass
            elif "AM" in hour_str or "PM" in hour_str:
                try:
                    parts = hour_str.replace(" ", "")
                    if "PM" in parts:
                        h = int(parts.replace("PM", ""))
                        hour_int = h + 12 if h != 12 else 12
                    else:
                        h = int(parts.replace("AM", ""))
                        hour_int = h if h != 12 else 0
                except:
                    pass

            temp_c = float(entry.get("temp_c", 30.0))
            humidity_pct = float(entry.get("humidity_pct", 70.0))
            
            # Compute Heat Index for this hour
            hi_res = PowerForecastEngine.calculate_heat_index(temp_c, humidity_pct)
            hi_c = hi_res["heat_index_c"]
            is_peak = PowerForecastEngine.is_peak_hour(hour_int)

            # Calculate total power load for this hour
            total_watts = 0.0
            appliance_breakdown = []
            for app in appliances:
                if hour_int in app.get("active_hours", []):
                    if app.get("is_hvac", False):
                        act_watts = PowerForecastEngine.estimate_adaptive_ac_power(app["rated_watts"], hi_c)
                    else:
                        act_watts = float(app.get("rated_watts", 100.0))
                    total_watts += act_watts
                    appliance_breakdown.append({
                        "name": app["name"],
                        "watts": act_watts
                    })

            profile.append({
                "hour": hour_str,
                "hour_24": hour_int,
                "temp_c": temp_c,
                "humidity_pct": humidity_pct,
                "heat_index_c": hi_c,
                "heat_index_f": hi_res["heat_index_f"],
                "risk_level": hi_res["risk_level"],
                "badge": hi_res["badge"],
                "is_peak_window": is_peak,
                "total_load_watts": round(total_watts, 1),
                "appliances": appliance_breakdown
            })

        return profile
