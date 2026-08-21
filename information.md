# Heat Index & Appliance Energy Consumption System Documentation
**Project:** PowerForecast (Meralco Energy Intel & Smart Scheduler)  
**Location Context:** San Jose del Monte City, Bulacan, Philippines

---

## 1. System Overview & Architecture

**PowerForecast** is an intelligent energy analytics and scheduling platform designed to:
1. Fetch and process localized weather metrics (temperature, humidity, solar exposure).
2. Calculate empirical **Weather Heat Index (Apparent Temperature)** and physiological risk tiers.
3. Dynamically adjust **Appliance Power & HVAC Cooling Loads** based on thermal gradients.
4. Forecast a **24-Hour Load Profile (Watts)**, highlight peak pricing windows, and recommend optimal off-peak scheduling to minimize electricity bills.

---

## 2. Weather Data Ingestion (AccuWeather Integration)

### 2.1 Extracted Data Points & System Mapping

Target Source: `https://www.accuweather.com/en/ph/san-jose-del-monte-city/3-262458_1_al/weather-today/3-262458_1_al`  
Coordinates for API fallback (Open-Meteo): Latitude `14.8137`, Longitude `121.0453`.

| Scraped / Ingested Parameter | Unit | Location / Context | Application in PowerForecast Engine |
| :--- | :--- | :--- | :--- |
| **Current Air Temperature ($T$)** | °C / °F | Main banner & current card | Core variable for computing baseline Heat Index and room heat gain. |
| **Relative Humidity ($RH$)** | % | Weather details badge | Evaluates evaporative cooling inhibition in the 9-term Heat Index equation. |
| **24-Hour Hourly Forecast ($T$, $RH$)** | Hourly series | Hourly forecast tab | Drives the dynamic **24-Hour Hourly Power Load Curve** on the calendar modal. |
| **UV Index & Solar Radiation** | 0 – 11+ | Weather detail badge | Acts as an ambient multiplier for building envelope thermal transfer. |
| **Precipitation & Rain Probability** | mm, % | Rain radar / summary cards | Modulates cooling urgency and ambient outdoor temperature adjustments. |

### 2.2 Ingestion Data Schema (JSON)

```json
{
  "location": "San Jose del Monte City, Bulacan, Philippines",
  "coordinates": { "lat": 14.8137, "lon": 121.0453 },
  "weather_snapshot": {
    "temperature_c": 32.5,
    "humidity_pct": 70.0,
    "uv_index": 8,
    "precipitation_prob_pct": 20
  },
  "hourly_forecast": [
    { "hour": "11:00", "temp_c": 33.0, "humidity_pct": 68 },
    { "hour": "14:00", "temp_c": 34.5, "humidity_pct": 65 },
    { "hour": "18:00", "temp_c": 29.0, "humidity_pct": 80 }
  ]
}
```

---

## 3. Weather Heat Index Mathematical Model

The **Heat Index (HI)** quantifies human heat stress by combining dry-bulb air temperature with relative humidity ($RH$). High humidity slows the evaporation of sweat, making the perceived temperature significantly higher.

### 3.1 Mathematical Formulation (NOAA / Rothfusz Regression)

#### Step 1: Unit Conversion (Celsius to Fahrenheit)
Empirical regression coefficients are calibrated in Fahrenheit ($^\circ\text{F}$):

$$T_F = (T_C \times 1.8) + 32$$

#### Step 2: Preliminary Steadman Approximation
For mild conditions, a preliminary linear estimate is computed:

$$\text{HI}_{\text{prelim}} = 0.5 \times \left( T_F + 61.0 + \left[(T_F - 68.0) \times 1.2\right] + (RH \times 0.094) \right)$$

If the arithmetic mean of $\text{HI}_{\text{prelim}}$ and $T_F$ is strictly below $80^\circ\text{F}$ ($26.7^\circ\text{C}$), $\text{HI}_{\text{prelim}}$ is used directly.

#### Step 3: Full 9-Term Rothfusz Polynomial
When $T_F \ge 80^\circ\text{F}$ ($26.7^\circ\text{C}$) and $RH \ge 40\%$, the full polynomial is evaluated:

$$\begin{aligned}
\text{HI} = &-42.379 + 2.04901523 \, T_F + 10.14333127 \, RH - 0.22475541 \, T_F \cdot RH \\
&- 6.83783 \times 10^{-3} \, T_F^2 - 5.481717 \times 10^{-2} \, RH^2 + 1.22874 \times 10^{-3} \, T_F^2 \cdot RH \\
&+ 8.5282 \times 10^{-4} \, T_F \cdot RH^2 - 1.99 \times 10^{-6} \, T_F^2 \cdot RH^2
\end{aligned}$$

#### Step 4: Edge Adjustments (Low & High Relative Humidity)
1. **Low Humidity Adjustment:** If $RH < 13\%$ and $80^\circ\text{F} \le T_F \le 112^\circ\text{F}$:
   $$\text{Adjustment}_{\text{low}} = -\left[ \frac{13 - RH}{4} \right] \times \sqrt{\frac{17 - |T_F - 95|}{17}}$$
   $$\text{HI}_{\text{final}} = \text{HI} + \text{Adjustment}_{\text{low}}$$

2. **High Humidity Adjustment:** If $RH > 85\%$ and $80^\circ\text{F} \le T_F \le 87^\circ\text{F}$:
   $$\text{Adjustment}_{\text{high}} = +\left[ \frac{RH - 85}{10} \right] \times \left[ \frac{87 - T_F}{5} \right]$$
   $$\text{HI}_{\text{final}} = \text{HI} + \text{Adjustment}_{\text{high}}$$

#### Step 5: Convert Back to Celsius
$$\text{HI}_C = (\text{HI}_{\text{final}} - 32) \times \frac{5}{9}$$

---

### 3.2 Heat Index Risk Levels (PAGASA / NOAA Standard)

| Heat Index Range (°C) | Heat Index Range (°F) | Risk Level | Physiological Effects | System Scheduling Advisory |
| :--- | :--- | :--- | :--- | :--- |
| **27°C – 32°C** | 80°F – 90°F | **Caution** | Fatigue possible with prolonged exposure. | Standard AC operation; standard cooling load. |
| **33°C – 41°C** | 91°F – 103°F | **Extreme Caution** | Heat cramps and exhaustion possible. | Pre-cool rooms prior to peak window hours. |
| **42°C – 51°C** | 104°F – 125°F | **Danger** | Heat cramps/exhaustion likely; heat stroke probable. | AC duty cycle elevated; defer non-cooling heavy loads. |
| **≥ 52°C** | ≥ 126°F | **Extreme Danger** | Heat stroke imminent. Medical emergency risk. | Maximum cooling priority; halt heavy non-essential appliances. |

---

## 4. Appliance Energy & Smart Scheduling Computation

### 4.1 Electrical Formulas

1. **Active Real Power ($P$ in Watts):**
   $$P = V \times I \times \text{PF}$$
   *(where $V = 220\text{V}-230\text{V}$ nominal, $I$ = current in Amps, and $\text{PF}$ = Power Factor: $1.0$ for resistive loads, $0.70-0.90$ for inductive motor/compressor loads).*

2. **Daily Consumption (kWh):**
   $$\text{Daily kWh} = \frac{\text{Rated Power (Watts)} \times \text{Hours Used per Day}}{1000}$$

3. **Monthly Consumption & Meralco Billing Estimate:**
   $$\text{Monthly kWh} = \text{Daily kWh} \times \text{Days (e.g., 30)}$$
   $$\text{Estimated Cost (PHP)} = \text{Monthly kWh} \times \text{Effective Tariff Rate (₱/kWh)}$$

### 4.2 Weather-Driven Adaptive HVAC Load Model

Inverter air conditioners (e.g., `SHARP AH-XP15YMF 1100W` and `jhokim aircon 820W`) modulate their compressor draw based on the temperature delta $\Delta T$:

$$\Delta T = \text{Outdoor Heat Index } (\text{HI}_C) - \text{Thermostat Setpoint } (T_{\text{set}}, \text{default } 24^\circ\text{C})$$
$$\text{Dynamic Load (Watts)} = P_{\text{rated}} \times \text{Clamp}\left(0.40 + 0.05 \times \Delta T, \; 0.35, \; 1.05\right)$$

- **Low Outdoor HI ($\le 28^\circ	ext{C}$):** Compressor runs at economic idle ($pprox 35\%	ext{--}45\%$ of rated power).
- **High Outdoor HI ($\ge 42^\circ	ext{C}$):** Compressor runs continuously near maximum boost ($pprox 90\%	ext{--}105\%$ rated power).

---

### 4.3 Peak Load Window Shifting Logic

PowerForecast monitors designated peak demand windows (e.g., **11:00 AM – 4:00 PM** and **6:00 PM – 9:00 PM**):

1. **Total Active Demand:**
   $$P_{\text{active}}(t) = \sum_{i \in \text{Active Sessions}} P_i(t)$$
2. **Peak Window Warning Condition:**
   $$\text{If } t \in \text{Peak Window} \quad \text{AND} \quad P_{\text{active}}(t) > P_{\text{threshold}} \; (\text{e.g., } 1800\text{W}) \implies \textbf{Trigger Peak Alert}$$
3. **Automated Recommendation:**
   - Defer discretionary high-wattage resistive loads (flat irons, laundry dryers, water pumps) to the **Optimal Off-Peak Window (after 9:00 PM or before 11:00 AM)**.

---

## 5. Complete Python Implementation Module

```python
import math
from typing import Dict, Any, List

class PowerForecastEngine:
    """
    Integrated calculation engine for PowerForecast.
    Handles Heat Index computation, adaptive HVAC loading, and cost estimation.
    """

    @staticmethod
    def calculate_heat_index(temp_celsius: float, humidity_percent: float) -> Dict[str, Any]:
        """Calculates apparent temperature (Heat Index) using NOAA Rothfusz formula."""
        if not (0 <= humidity_percent <= 100):
            raise ValueError("Humidity must be between 0% and 100%.")

        tf = (temp_celsius * 1.8) + 32.0
        rh = humidity_percent

        hi_prelim = 0.5 * (tf + 61.0 + ((tf - 68.0) * 1.2) + (rh * 0.094))

        if (hi_prelim + tf) / 2.0 >= 80.0:
            hi = (-42.379
                  + 2.04901523 * tf
                  + 10.14333127 * rh
                  - 0.22475541 * tf * rh
                  - 0.00683783 * (tf ** 2)
                  - 0.05481717 * (rh ** 2)
                  + 0.00122874 * (tf ** 2) * rh
                  + 0.00085282 * tf * (rh ** 2)
                  - 0.00000199 * (tf ** 2) * (rh ** 2))

            if rh < 13.0 and 80.0 <= tf <= 112.0:
                adj_low = ((13.0 - rh) / 4.0) * math.sqrt(max(0.0, (17.0 - abs(tf - 95.0)) / 17.0))
                hi -= adj_low
            elif rh > 85.0 and 80.0 <= tf <= 87.0:
                adj_high = ((rh - 85.0) / 10.0) * ((87.0 - tf) / 5.0)
                hi += adj_high
        else:
            hi = hi_prelim

        hi_celsius = (hi - 32.0) / 1.8

        if hi_celsius < 27.0:
            category = "Normal / Safe"
            advisory = "Comfortable thermal conditions. Regular AC operation."
        elif 27.0 <= hi_celsius < 33.0:
            category = "Caution"
            advisory = "Moderate warmth. Maintain standard cooling schedule."
        elif 33.0 <= hi_celsius < 42.0:
            category = "Extreme Caution"
            advisory = "Elevated heat. Pre-cool rooms prior to afternoon peak windows."
        elif 42.0 <= hi_celsius < 52.0:
            category = "Danger"
            advisory = "High heat stress. Prioritize AC; defer high-wattage appliances."
        else:
            category = "Extreme Danger"
            advisory = "Emergency heat levels. Maintain continuous cooling."

        return {
            "ambient_temp_c": round(temp_celsius, 2),
            "relative_humidity_pct": round(humidity_percent, 1),
            "heat_index_c": round(hi_celsius, 2),
            "heat_index_f": round(hi, 2),
            "risk_level": category,
            "advisory": advisory
        }

    @staticmethod
    def estimate_adaptive_ac_power(rated_watts: float, heat_index_c: float, setpoint_c: float = 24.0) -> float:
        """Estimates actual AC power draw modulated by outdoor Heat Index."""
        delta_t = max(0.0, heat_index_c - setpoint_c)
        duty_factor = max(0.35, min(1.05, 0.40 + (0.05 * delta_t)))
        return round(rated_watts * duty_factor, 2)

    @staticmethod
    def calculate_daily_schedule_cost(
        tasks: List[Dict[str, Any]],
        effective_tariff_rate: float
    ) -> Dict[str, Any]:
        """
        Computes total daily kWh and bill cost from scheduled sessions.
        :param tasks: List of dicts with keys: 'name', 'watts', 'hours_active'
        :param effective_tariff_rate: Rate in PHP/kWh (e.g. 14.4759)
        """
        total_kwh = sum((t["watts"] * t["hours_active"]) / 1000.0 for t in tasks)
        total_cost = total_kwh * effective_tariff_rate

        return {
            "scheduled_energy_kwh": round(total_kwh, 3),
            "projected_cost_php": round(total_cost, 2),
            "effective_rate": effective_tariff_rate,
            "task_count": len(tasks)
        }


# --- Example Execution ---
if __name__ == "__main__":
    # 1. Calculate Weather Heat Index for San Jose del Monte
    weather_eval = PowerForecastEngine.calculate_heat_index(temp_celsius=33.5, humidity_percent=72.0)
    print("=== Weather Heat Index ===")
    for k, v in weather_eval.items():
        print(f"  {k}: {v}")

    # 2. Dynamic AC Power Adjustment
    sharp_ac_rated = 1100.0  # SHARP AH-XP15YMF
    actual_power = PowerForecastEngine.estimate_adaptive_ac_power(sharp_ac_rated, weather_eval["heat_index_c"])
    print(f"\nAdaptive AC Draw (Sharp 1100W): {actual_power} W at {weather_eval['heat_index_c']}°C HI")

    # 3. Daily Scheduling Cost Evaluation
    active_sessions = [
        {"name": "SHARP AH-XP15YMF", "watts": actual_power, "hours_active": 8.0},
        {"name": "jhokim aircon", "watts": 820.0, "hours_active": 6.0},
        {"name": "General Home Base Load", "watts": 350.0, "hours_active": 24.0}
    ]
    daily_summary = PowerForecastEngine.calculate_daily_schedule_cost(active_sessions, effective_tariff_rate=14.82)
    print("\n=== Daily Schedule Summary ===")
    for k, v in daily_summary.items():
        print(f"  {k}: {v}")
```
