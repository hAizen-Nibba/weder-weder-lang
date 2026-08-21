// PowerForecast Web Application Logic
// Version: 1.0.0v

let currentCityData = null;
let allCitiesData = [];
let hourlyChartInstance = null;

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  initClock();
  initVersionBadge();
  loadSanJoseDelMonte();
  loadAllPhilippines();
  initEventListeners();
});

// 1. Philippine Live Clock (UTC+8)
function initClock() {
  const clockEl = document.getElementById("phTimeDisplay");
  function update() {
    const now = new Date();
    const phTime = new Intl.DateTimeFormat("en-US", {
      timeZone: "Asia/Manila",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true
    }).format(now);
    if (clockEl) clockEl.textContent = phTime;
  }
  update();
  setInterval(update, 1000);
}

// 2. Fetch and Sync Version Badge
async function initVersionBadge() {
  try {
    const resp = await fetch("/api/version");
    if (resp.ok) {
      const data = await resp.json();
      const verEl = document.getElementById("uiVersionDisplay");
      if (verEl && data.version) {
        verEl.textContent = data.version;
      }
    }
  } catch (err) {
    console.warn("Using default version badge 1.0.0v", err);
  }
}

// 3. Load Primary Location: San Jose del Monte City
async function loadSanJoseDelMonte(refresh = false) {
  const refreshBtn = document.getElementById("refreshBtn");
  if (refreshBtn) refreshBtn.classList.add("spinning");

  try {
    const url = refresh ? "/api/weather/sanjose?refresh=true" : "/api/weather/sanjose";
    const resp = await fetch(url);
    if (resp.ok) {
      const data = await resp.json();
      currentCityData = data;
      renderFeaturedCity(data);
      renderHourlyChart(data);
      updateApplianceBilling();
    }
  } catch (err) {
    console.error("Error loading San Jose del Monte data:", err);
  } finally {
    if (refreshBtn) refreshBtn.classList.remove("spinning");
  }
}

// 4. Load Nationwide Philippines Data
async function loadAllPhilippines(refresh = false) {
  try {
    const url = refresh ? "/api/weather/philippines?refresh=true" : "/api/weather/philippines";
    const resp = await fetch(url);
    if (resp.ok) {
      allCitiesData = await resp.json();
      renderCitiesGrid(allCitiesData, "all");
    }
  } catch (err) {
    console.error("Error loading nationwide Philippines data:", err);
  }
}

// 5. Render Featured City Details
function renderFeaturedCity(data) {
  const snap = data.weather_snapshot || {};
  const hi = data.heat_index_evaluation || {};
  const coords = data.coordinates || {};

  // Text Elements
  document.getElementById("currentLocationName").textContent = `${data.location} (${data.province || "Bulacan"})`;
  document.getElementById("cardRegionBadge").textContent = `${data.region || "Central Luzon"} • ${data.island_group || "Luzon"}`;
  document.getElementById("cardCityTitle").textContent = data.location;
  document.getElementById("cardCoordsText").textContent = `Lat ${coords.lat || "14.81"}, Lon ${coords.lon || "121.05"} • ${data.province || "Bulacan"}, Philippines`;
  document.getElementById("weatherPhraseBadge").textContent = snap.phrase || "Cloudy";

  // Temperature & Weather Metrics
  document.getElementById("tempVal").textContent = snap.temperature_c ?? 30;
  document.getElementById("realFeelVal").textContent = `${snap.real_feel_c ?? snap.temperature_c}°C`;
  document.getElementById("humidityVal").textContent = `${snap.humidity_pct ?? 75}%`;
  document.getElementById("precipVal").textContent = `${snap.precipitation_prob_pct ?? 20}%`;
  document.getElementById("windVal").textContent = `${snap.wind_speed_kmh ?? 10} km/h ${snap.wind_direction ?? ""}`;
  document.getElementById("windGustVal").textContent = `${snap.wind_gusts_kmh ?? 25} km/h`;
  document.getElementById("dewPointVal").textContent = `${snap.dew_point_c ?? 25}°C`;
  document.getElementById("cloudCoverVal").textContent = `${snap.cloud_cover_pct ?? 70}%`;
  document.getElementById("pressureVal").textContent = `${snap.pressure_mb ?? 1010} mb`;
  document.getElementById("visibilityVal").textContent = `${snap.visibility_km ?? 10} km`;

  // Heat Index & Risk Badge
  const hiC = hi.heat_index_c ?? 37.4;
  const hiF = hi.heat_index_f ?? 99.3;
  document.getElementById("hiValC").textContent = hiC.toFixed(1);
  document.getElementById("hiValF").textContent = `(${hiF.toFixed(1)}°F)`;

  const riskBadge = document.getElementById("riskBadge");
  riskBadge.textContent = hi.risk_level || "Extreme Caution";
  riskBadge.className = `risk-badge ${hi.badge || "warning"}`;

  // Meter Indicator position (20°C to 55°C scale)
  const meterPercent = Math.min(100, Math.max(0, ((hiC - 20) / (55 - 20)) * 100));
  const indicator = document.getElementById("meterIndicator");
  if (indicator) indicator.style.left = `${meterPercent}%`;

  // Advisory Text
  document.getElementById("advisoryText").textContent = hi.advisory || "Elevated heat. Pre-cool rooms prior to afternoon peak windows.";

  // Adaptive HVAC Power
  const sharpWatts = hi.adaptive_ac_power_1100w ?? 1155.0;
  const jhokimWatts = hi.adaptive_ac_power_820w ?? 861.0;
  document.getElementById("sharpWattsVal").textContent = `${sharpWatts.toFixed(1)} W`;
  document.getElementById("jhokimWattsVal").textContent = `${jhokimWatts.toFixed(1)} W`;
  document.getElementById("tableSharpWatts").textContent = `${Math.round(sharpWatts)} W`;
  document.getElementById("tableJhokimWatts").textContent = `${Math.round(jhokimWatts)} W`;
}

// 6. Render 24-Hour Load Profile & Peak Window Chart
function renderHourlyChart(data) {
  const curve = data.load_profile_curve || [];
  const hourly = data.hourly_forecast || [];

  const labels = [];
  const loadWatts = [];
  const heatIndex = [];
  const temps = [];
  const peakFlags = [];

  const sourceData = curve.length > 0 ? curve : hourly;

  sourceData.slice(0, 24).forEach((item) => {
    labels.push(item.hour || `${item.hour_24}:00`);
    loadWatts.push(item.total_load_watts ?? 1200);
    heatIndex.push(item.heat_index_c ?? item.temp_c);
    temps.push(item.temp_c);
    peakFlags.push(item.is_peak_window || false);
  });

  // Render mini cards scroll
  const scrollContainer = document.getElementById("hourlyCardsScroll");
  if (scrollContainer) {
    scrollContainer.innerHTML = "";
    sourceData.slice(0, 24).forEach((item) => {
      const card = document.createElement("div");
      card.className = `hourly-mini-card ${item.is_peak_window ? "peak" : ""}`;
      card.innerHTML = `
        <span class="hourly-time">${item.hour}</span>
        <span class="hourly-temp">${item.temp_c}°C</span>
        <span class="hourly-hi">HI ${Math.round(item.heat_index_c || item.temp_c)}°C</span>
        <span class="hourly-precip">💧 ${item.precip_prob_pct || 0}%</span>
      `;
      scrollContainer.appendChild(card);
    });
  }

  const ctx = document.getElementById("hourlyLoadChart").getContext("2d");
  if (hourlyChartInstance) {
    hourlyChartInstance.destroy();
  }

  hourlyChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Total Power Load (Watts)",
          data: loadWatts,
          borderColor: "#38bdf8",
          backgroundColor: "rgba(56, 189, 248, 0.12)",
          fill: true,
          tension: 0.4,
          borderWidth: 3,
          pointRadius: 4,
          pointBackgroundColor: "#38bdf8",
          yAxisID: "yWatts"
        },
        {
          label: "Heat Index (°C Apparent)",
          data: heatIndex,
          borderColor: "#f97316",
          backgroundColor: "transparent",
          borderDash: [5, 5],
          tension: 0.4,
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: "#f97316",
          yAxisID: "yTemp"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: "rgba(15, 23, 42, 0.95)",
          titleColor: "#fff",
          bodyColor: "#cbd5e1",
          borderColor: "rgba(56, 189, 248, 0.3)",
          borderWidth: 1,
          padding: 12,
          callbacks: {
            footer: (tooltipItems) => {
              const idx = tooltipItems[0].dataIndex;
              return peakFlags[idx] ? "⚡ PEAK DEMAND PRICING WINDOW" : "✓ Off-Peak Economic Window";
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            color: "rgba(255, 255, 255, 0.05)"
          },
          ticks: {
            color: "#94a3b8",
            font: { size: 11 }
          }
        },
        yWatts: {
          type: "linear",
          position: "left",
          grid: {
            color: "rgba(255, 255, 255, 0.05)"
          },
          ticks: {
            color: "#38bdf8",
            callback: (val) => `${val} W`
          }
        },
        yTemp: {
          type: "linear",
          position: "right",
          grid: {
            drawOnChartArea: false
          },
          ticks: {
            color: "#f97316",
            callback: (val) => `${val}°C`
          }
        }
      }
    }
  });
}

// 7. Render Nationwide Cities Grid
function renderCitiesGrid(cities, filterGroup = "all") {
  const grid = document.getElementById("citiesGrid");
  if (!grid) return;
  grid.innerHTML = "";

  const filtered = cities.filter((c) => {
    if (filterGroup === "all") return true;
    if (filterGroup === "NCR") return c.region && c.region.includes("NCR");
    return c.island_group && c.island_group.toLowerCase() === filterGroup.toLowerCase();
  });

  filtered.forEach((city) => {
    const snap = city.weather_snapshot || {};
    const hi = city.heat_index_evaluation || {};
    const isSelected = currentCityData && currentCityData.location_id === city.location_id;

    const card = document.createElement("div");
    card.className = `city-card ${isSelected ? "selected" : ""}`;
    card.innerHTML = `
      <div class="city-card-header">
        <div>
          <h4 class="city-name">${city.location}</h4>
          <span class="city-province">${city.province} • ${city.island_group}</span>
        </div>
      </div>
      <div class="city-card-body">
        <div class="city-temp-row">
          <span class="city-temp-val">${snap.temperature_c ?? 30}</span>
          <span class="city-temp-unit">°C</span>
        </div>
        <div class="city-hi-box">
          <span class="city-hi-label">HEAT INDEX</span>
          <span class="city-hi-val" style="color: var(--${hi.badge || "warning"})">${Math.round(hi.heat_index_c ?? snap.temperature_c)}°C</span>
        </div>
      </div>
      <div class="city-card-footer">
        <span class="city-phrase">${snap.phrase || "Cloudy"} • RH ${snap.humidity_pct || 75}%</span>
        <span class="city-risk-tag ${hi.badge || "warning"}" style="background: var(--${hi.badge || "warning"}-bg); color: var(--${hi.badge || "warning"})">${hi.risk_level || "Caution"}</span>
      </div>
    `;

    card.addEventListener("click", () => {
      currentCityData = city;
      renderFeaturedCity(city);
      renderHourlyChart(city);
      updateApplianceBilling();
      document.querySelectorAll(".city-card").forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      window.scrollTo({ top: 0, behavior: "smooth" });
    });

    grid.appendChild(card);
  });
}

// 8. Dynamic Appliance Billing Calculator
function updateApplianceBilling() {
  const tariffRate = parseFloat(document.getElementById("tariffRateInput").value) || 14.82;

  // Get hours
  const sharpHours = parseFloat(document.getElementById("sharpHoursSlider").value) || 8;
  const jhokimHours = parseFloat(document.getElementById("jhokimHoursSlider").value) || 6;
  const refHours = parseFloat(document.getElementById("refHoursSlider").value) || 24;
  const ironHours = parseFloat(document.getElementById("ironHoursSlider").value) || 1.5;
  const lightsHours = parseFloat(document.getElementById("lightsHoursSlider").value) || 12;

  // Update slider labels
  document.getElementById("sharpHoursLabel").textContent = sharpHours.toFixed(1);
  document.getElementById("jhokimHoursLabel").textContent = jhokimHours.toFixed(1);
  document.getElementById("refHoursLabel").textContent = refHours.toFixed(1);
  document.getElementById("ironHoursLabel").textContent = ironHours.toFixed(1);
  document.getElementById("lightsHoursLabel").textContent = lightsHours.toFixed(1);

  // Watts
  const hi = currentCityData?.heat_index_evaluation || {};
  const sharpWatts = hi.adaptive_ac_power_1100w || 1155.0;
  const jhokimWatts = hi.adaptive_ac_power_820w || 861.0;
  const refWatts = 160.0;
  const ironWatts = 1000.0;
  const lightsWatts = 250.0;

  // Compute kWh
  const dailyKwh = (
    (sharpWatts * sharpHours) +
    (jhokimWatts * jhokimHours) +
    (refWatts * refHours) +
    (ironWatts * ironHours) +
    (lightsWatts * lightsHours)
  ) / 1000.0;

  const monthlyKwh = dailyKwh * 30.0;
  const dailyCost = dailyKwh * tariffRate;
  const monthlyCost = monthlyKwh * tariffRate;

  // Update Displays
  document.getElementById("dailyKwhDisplay").textContent = `${dailyKwh.toFixed(2)} kWh`;
  document.getElementById("monthlyKwhDisplay").textContent = `${monthlyKwh.toFixed(1)} kWh`;
  document.getElementById("dailyCostDisplay").textContent = `₱ ${dailyCost.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  document.getElementById("monthlyCostDisplay").textContent = `₱ ${monthlyCost.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// 9. Event Listeners & Autocomplete Search Suggestions
function initEventListeners() {
  // Live Scrape Refresh button
  const refreshBtn = document.getElementById("refreshBtn");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      loadSanJoseDelMonte(true);
      loadAllPhilippines(true);
    });
  }

  // City Search & Autocomplete Dropdown
  const searchInput = document.getElementById("citySearchInput");
  const searchBtn = document.getElementById("searchBtn");
  const dropdown = document.getElementById("searchSuggestionsDropdown");

  let debounceTimer = null;
  let activeIndex = -1;
  let currentSuggestions = [];

  async function performSearch(queryOverride = null) {
    const query = (queryOverride || searchInput.value).trim();
    if (!query) return;

    hideDropdown();
    searchBtn.textContent = "Searching...";
    try {
      const resp = await fetch(`/api/weather/search?q=${encodeURIComponent(query)}`);
      if (resp.ok) {
        const data = await resp.json();
        currentCityData = data;
        renderFeaturedCity(data);
        renderHourlyChart(data);
        updateApplianceBilling();
        window.scrollTo({ top: 0, behavior: "smooth" });
      } else {
        alert(`No Philippine city found matching "${query}". Try Malolos, Baguio, Cebu, or Davao.`);
      }
    } catch (err) {
      console.error("Search error:", err);
    } finally {
      searchBtn.textContent = "Search";
    }
  }

  function hideDropdown() {
    if (dropdown) {
      dropdown.classList.remove("open");
      dropdown.innerHTML = "";
    }
    activeIndex = -1;
    currentSuggestions = [];
  }

  function renderSuggestions(items) {
    if (!dropdown) return;
    currentSuggestions = items;
    activeIndex = -1;

    if (!items || items.length === 0) {
      hideDropdown();
      return;
    }

    dropdown.innerHTML = "";
    items.forEach((item, idx) => {
      const div = document.createElement("div");
      div.className = "suggestion-item";
      div.setAttribute("data-index", idx);
      div.innerHTML = `
        <div class="suggestion-left">
          <span class="suggestion-title">${item.name}</span>
          <span class="suggestion-sub">${item.province} • ${item.island_group || "Philippines"}</span>
        </div>
        <span class="suggestion-badge">${item.region.split("(")[0].trim()}</span>
      `;

      div.addEventListener("click", () => {
        searchInput.value = item.name;
        performSearch(item.name);
      });

      dropdown.appendChild(div);
    });

    dropdown.classList.add("open");
  }

  async function fetchSuggestions(query) {
    const q = query.trim();
    if (q.length < 1) {
      hideDropdown();
      return;
    }

    try {
      const resp = await fetch(`/api/weather/suggest?q=${encodeURIComponent(q)}`);
      if (resp.ok) {
        const items = await resp.json();
        renderSuggestions(items);
      }
    } catch (err) {
      console.warn("Suggestions error:", err);
    }
  }

  if (searchInput) {
    // Input listener with debounce
    searchInput.addEventListener("input", (e) => {
      clearTimeout(debounceTimer);
      const val = e.target.value;
      debounceTimer = setTimeout(() => {
        fetchSuggestions(val);
      }, 250);
    });

    // Keyboard navigation (Arrow keys, Enter, Escape)
    searchInput.addEventListener("keydown", (e) => {
      const items = dropdown ? dropdown.querySelectorAll(".suggestion-item") : [];

      if (e.key === "ArrowDown") {
        e.preventDefault();
        if (items.length > 0) {
          activeIndex = (activeIndex + 1) % items.length;
          updateActiveItem(items);
        }
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        if (items.length > 0) {
          activeIndex = (activeIndex - 1 + items.length) % items.length;
          updateActiveItem(items);
        }
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (activeIndex >= 0 && activeIndex < currentSuggestions.length) {
          const chosen = currentSuggestions[activeIndex];
          searchInput.value = chosen.name;
          performSearch(chosen.name);
        } else {
          performSearch();
        }
      } else if (e.key === "Escape") {
        hideDropdown();
      }
    });

    // Focus listener
    searchInput.addEventListener("focus", () => {
      if (searchInput.value.trim().length >= 1) {
        fetchSuggestions(searchInput.value);
      }
    });
  }

  function updateActiveItem(items) {
    items.forEach((it, idx) => {
      if (idx === activeIndex) {
        it.classList.add("active");
        it.scrollIntoView({ block: "nearest" });
        if (currentSuggestions[idx]) {
          searchInput.value = currentSuggestions[idx].name;
        }
      } else {
        it.classList.remove("active");
      }
    });
  }

  // Click outside to close dropdown
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".search-wrapper")) {
      hideDropdown();
    }
  });

  if (searchBtn) searchBtn.addEventListener("click", () => performSearch());

  // Filter Tabs
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const filter = btn.getAttribute("data-filter");
      renderCitiesGrid(allCitiesData, filter);
    });
  });

  // Slider inputs
  const sliders = ["sharpHoursSlider", "jhokimHoursSlider", "refHoursSlider", "ironHoursSlider", "lightsHoursSlider", "tariffRateInput"];
  sliders.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("input", updateApplianceBilling);
  });
}
