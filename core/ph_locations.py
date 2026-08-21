import json
from typing import List, Dict, Any, Optional
from curl_cffi import requests

# Comprehensive verified list of major Philippine Cities, Municipalities & Provincial Capitals
PHILIPPINES_REGIONS_DATA: List[Dict[str, Any]] = [
    # --- TARGET REGION: CENTRAL LUZON (REGION III) ---
    {
        "id": "san_jose_del_monte",
        "name": "San Jose del Monte City",
        "province": "Bulacan",
        "region": "Central Luzon (Region III)",
        "island_group": "Luzon",
        "coordinates": {"lat": 14.8137, "lon": 121.0453},
        "accuweather_url": "https://www.accuweather.com/en/ph/san-jose-del-monte-city/3-262458_1_al/weather-today/3-262458_1_al",
        "accuweather_key": "3-262458_1_al",
        "slug": "san-jose-del-monte-city",
        "is_primary_target": True
    },
    {
        "id": "malolos",
        "name": "Malolos City",
        "province": "Bulacan",
        "region": "Central Luzon (Region III)",
        "island_group": "Luzon",
        "coordinates": {"lat": 14.8527, "lon": 120.8160},
        "accuweather_url": "https://www.accuweather.com/en/ph/malolos/262456/weather-today/262456",
        "accuweather_key": "262456",
        "slug": "malolos"
    },
    {
        "id": "angeles",
        "name": "Angeles City",
        "province": "Pampanga",
        "region": "Central Luzon (Region III)",
        "island_group": "Luzon",
        "coordinates": {"lat": 15.1450, "lon": 120.5887},
        "accuweather_url": "https://www.accuweather.com/en/ph/angeles-city/265384/weather-today/265384",
        "accuweather_key": "265384",
        "slug": "angeles-city"
    },
    {
        "id": "san_fernando_pampanga",
        "name": "San Fernando City",
        "province": "Pampanga",
        "region": "Central Luzon (Region III)",
        "island_group": "Luzon",
        "coordinates": {"lat": 15.0311, "lon": 120.6853},
        "accuweather_url": "https://www.accuweather.com/en/ph/san-fernando/265387/weather-today/265387",
        "accuweather_key": "265387",
        "slug": "san-fernando"
    },
    {
        "id": "cabanatuan",
        "name": "Cabanatuan City",
        "province": "Nueva Ecija",
        "region": "Central Luzon (Region III)",
        "island_group": "Luzon",
        "coordinates": {"lat": 15.4859, "lon": 120.9669},
        "accuweather_url": "https://www.accuweather.com/en/ph/cabanatuan-city/265005/weather-today/265005",
        "accuweather_key": "265005",
        "slug": "cabanatuan-city"
    },
    {
        "id": "tarlac_city",
        "name": "Tarlac City",
        "province": "Tarlac",
        "region": "Central Luzon (Region III)",
        "island_group": "Luzon",
        "coordinates": {"lat": 15.4802, "lon": 120.5979},
        "accuweather_url": "https://www.accuweather.com/en/ph/tarlac-city/266005/weather-today/266005",
        "accuweather_key": "266005",
        "slug": "tarlac-city"
    },
    {
        "id": "olongapo",
        "name": "Olongapo City",
        "province": "Zambales",
        "region": "Central Luzon (Region III)",
        "island_group": "Luzon",
        "coordinates": {"lat": 14.8386, "lon": 120.2842},
        "accuweather_url": "https://www.accuweather.com/en/ph/olongapo/266395/weather-today/266395",
        "accuweather_key": "266395",
        "slug": "olongapo"
    },

    # --- NATIONAL CAPITAL REGION (NCR / METRO MANILA) ---
    {
        "id": "manila",
        "name": "City of Manila",
        "province": "Metro Manila",
        "region": "National Capital Region (NCR)",
        "island_group": "Luzon",
        "coordinates": {"lat": 14.5995, "lon": 120.9842},
        "accuweather_url": "https://www.accuweather.com/en/ph/manila/264885/weather-today/264885",
        "accuweather_key": "264885",
        "slug": "manila"
    },
    {
        "id": "quezon_city",
        "name": "Quezon City",
        "province": "Metro Manila",
        "region": "National Capital Region (NCR)",
        "island_group": "Luzon",
        "coordinates": {"lat": 14.6760, "lon": 121.0437},
        "accuweather_url": "https://www.accuweather.com/en/ph/quezon-city/264888/weather-today/264888",
        "accuweather_key": "264888",
        "slug": "quezon-city"
    },
    {
        "id": "makati",
        "name": "Makati City",
        "province": "Metro Manila",
        "region": "National Capital Region (NCR)",
        "island_group": "Luzon",
        "coordinates": {"lat": 14.5547, "lon": 121.0244},
        "accuweather_url": "https://www.accuweather.com/en/ph/makati/264884/weather-today/264884",
        "accuweather_key": "264884",
        "slug": "makati"
    },
    {
        "id": "taguig",
        "name": "Taguig City (BGC)",
        "province": "Metro Manila",
        "region": "National Capital Region (NCR)",
        "island_group": "Luzon",
        "coordinates": {"lat": 14.5176, "lon": 121.0509},
        "accuweather_url": "https://www.accuweather.com/en/ph/taguig/264893/weather-today/264893",
        "accuweather_key": "264893",
        "slug": "taguig"
    },
    {
        "id": "pasig",
        "name": "Pasig City",
        "province": "Metro Manila",
        "region": "National Capital Region (NCR)",
        "island_group": "Luzon",
        "coordinates": {"lat": 14.5764, "lon": 121.0851},
        "accuweather_url": "https://www.accuweather.com/en/ph/pasig/264889/weather-today/264889",
        "accuweather_key": "264889",
        "slug": "pasig"
    },
    {
        "id": "caloocan",
        "name": "Caloocan City",
        "province": "Metro Manila",
        "region": "National Capital Region (NCR)",
        "island_group": "Luzon",
        "coordinates": {"lat": 14.6514, "lon": 120.9753},
        "accuweather_url": "https://www.accuweather.com/en/ph/caloocan/264880/weather-today/264880",
        "accuweather_key": "264880",
        "slug": "caloocan"
    },
    {
        "id": "paranaque",
        "name": "Parañaque City",
        "province": "Metro Manila",
        "region": "National Capital Region (NCR)",
        "island_group": "Luzon",
        "coordinates": {"lat": 14.4793, "lon": 121.0198},
        "accuweather_url": "https://www.accuweather.com/en/ph/paranaque/264887/weather-today/264887",
        "accuweather_key": "264887",
        "slug": "paranaque"
    },
    {
        "id": "pasay",
        "name": "Pasay City",
        "province": "Metro Manila",
        "region": "National Capital Region (NCR)",
        "island_group": "Luzon",
        "coordinates": {"lat": 14.5378, "lon": 120.9997},
        "accuweather_url": "https://www.accuweather.com/en/ph/pasay/264886/weather-today/264886",
        "accuweather_key": "264886",
        "slug": "pasay"
    },

    # --- CALABARZON (REGION IV-A) ---
    {
        "id": "antipolo",
        "name": "Antipolo City",
        "province": "Rizal",
        "region": "CALABARZON (Region IV-A)",
        "island_group": "Luzon",
        "coordinates": {"lat": 14.6258, "lon": 121.1225},
        "accuweather_url": "https://www.accuweather.com/en/ph/antipolo/265507/weather-today/265507",
        "accuweather_key": "265507",
        "slug": "antipolo"
    },
    {
        "id": "calamba",
        "name": "Calamba City",
        "province": "Laguna",
        "region": "CALABARZON (Region IV-A)",
        "island_group": "Luzon",
        "coordinates": {"lat": 14.2117, "lon": 121.1653},
        "accuweather_url": "https://www.accuweather.com/en/ph/calamba/264177/weather-today/264177",
        "accuweather_key": "264177",
        "slug": "calamba"
    },
    {
        "id": "santa_rosa",
        "name": "Santa Rosa City",
        "province": "Laguna",
        "region": "CALABARZON (Region IV-A)",
        "island_group": "Luzon",
        "coordinates": {"lat": 14.3122, "lon": 121.1114},
        "accuweather_url": "https://www.accuweather.com/en/ph/santa-rosa/264201/weather-today/264201",
        "accuweather_key": "264201",
        "slug": "santa-rosa"
    },
    {
        "id": "batangas_city",
        "name": "Batangas City",
        "province": "Batangas",
        "region": "CALABARZON (Region IV-A)",
        "island_group": "Luzon",
        "coordinates": {"lat": 13.7565, "lon": 121.0583},
        "accuweather_url": "https://www.accuweather.com/en/ph/batangas/262293/weather-today/262293",
        "accuweather_key": "262293",
        "slug": "batangas"
    },
    {
        "id": "lipa",
        "name": "Lipa City",
        "province": "Batangas",
        "region": "CALABARZON (Region IV-A)",
        "island_group": "Luzon",
        "coordinates": {"lat": 13.9411, "lon": 121.1631},
        "accuweather_url": "https://www.accuweather.com/en/ph/lipa/262313/weather-today/262313",
        "accuweather_key": "262313",
        "slug": "lipa"
    },
    {
        "id": "tagaytay",
        "name": "Tagaytay City",
        "province": "Cavite",
        "region": "CALABARZON (Region IV-A)",
        "island_group": "Luzon",
        "coordinates": {"lat": 14.1153, "lon": 120.9621},
        "accuweather_url": "https://www.accuweather.com/en/ph/tagaytay/262747/weather-today/262747",
        "accuweather_key": "262747",
        "slug": "tagaytay"
    },
    {
        "id": "dasmarinas",
        "name": "Dasmariñas City",
        "province": "Cavite",
        "region": "CALABARZON (Region IV-A)",
        "island_group": "Luzon",
        "coordinates": {"lat": 14.3294, "lon": 120.9367},
        "accuweather_url": "https://www.accuweather.com/en/ph/dasmarinas/262734/weather-today/262734",
        "accuweather_key": "262734",
        "slug": "dasmarinas"
    },
    {
        "id": "lucena",
        "name": "Lucena City",
        "province": "Quezon",
        "region": "CALABARZON (Region IV-A)",
        "island_group": "Luzon",
        "coordinates": {"lat": 13.9314, "lon": 121.6172},
        "accuweather_url": "https://www.accuweather.com/en/ph/lucena/265430/weather-today/265430",
        "accuweather_key": "265430",
        "slug": "lucena"
    },

    # --- NORTHERN LUZON & CORDILLERA ---
    {
        "id": "baguio",
        "name": "Baguio City",
        "province": "Benguet",
        "region": "Cordillera Administrative Region (CAR)",
        "island_group": "Luzon",
        "coordinates": {"lat": 16.4023, "lon": 120.5960},
        "accuweather_url": "https://www.accuweather.com/en/ph/baguio/262335/weather-today/262335",
        "accuweather_key": "262335",
        "slug": "baguio"
    },
    {
        "id": "laoag",
        "name": "Laoag City",
        "province": "Ilocos Norte",
        "region": "Ilocos Region (Region I)",
        "island_group": "Luzon",
        "coordinates": {"lat": 18.1960, "lon": 120.5927},
        "accuweather_url": "https://www.accuweather.com/en/ph/laoag/263884/weather-today/263884",
        "accuweather_key": "263884",
        "slug": "laoag"
    },
    {
        "id": "vigan",
        "name": "Vigan City",
        "province": "Ilocos Sur",
        "region": "Ilocos Region (Region I)",
        "island_group": "Luzon",
        "coordinates": {"lat": 17.5747, "lon": 120.3869},
        "accuweather_url": "https://www.accuweather.com/en/ph/vigan/263914/weather-today/263914",
        "accuweather_key": "263914",
        "slug": "vigan"
    },
    {
        "id": "dagupan",
        "name": "Dagupan City",
        "province": "Pangasinan",
        "region": "Ilocos Region (Region I)",
        "island_group": "Luzon",
        "coordinates": {"lat": 16.0433, "lon": 120.3341},
        "accuweather_url": "https://www.accuweather.com/en/ph/dagupan/265324/weather-today/265324",
        "accuweather_key": "265324",
        "slug": "dagupan"
    },
    {
        "id": "tuguegarao",
        "name": "Tuguegarao City",
        "province": "Cagayan",
        "region": "Cagayan Valley (Region II)",
        "island_group": "Luzon",
        "coordinates": {"lat": 17.6132, "lon": 121.7270},
        "accuweather_url": "https://www.accuweather.com/en/ph/tuguegarao/262590/weather-today/262590",
        "accuweather_key": "262590",
        "slug": "tuguegarao"
    },

    # --- BICOL & MIMAROPA ---
    {
        "id": "legazpi",
        "name": "Legazpi City",
        "province": "Albay",
        "region": "Bicol Region (Region V)",
        "island_group": "Luzon",
        "coordinates": {"lat": 13.1412, "lon": 123.7407},
        "accuweather_url": "https://www.accuweather.com/en/ph/legazpi/262174/weather-today/262174",
        "accuweather_key": "262174",
        "slug": "legazpi"
    },
    {
        "id": "naga",
        "name": "Naga City",
        "province": "Camarines Sur",
        "region": "Bicol Region (Region V)",
        "island_group": "Luzon",
        "coordinates": {"lat": 13.6192, "lon": 123.1814},
        "accuweather_url": "https://www.accuweather.com/en/ph/naga/262529/weather-today/262529",
        "accuweather_key": "262529",
        "slug": "naga"
    },
    {
        "id": "puerto_princesa",
        "name": "Puerto Princesa City",
        "province": "Palawan",
        "region": "MIMAROPA (Region IV-B)",
        "island_group": "Luzon",
        "coordinates": {"lat": 9.7392, "lon": 118.7353},
        "accuweather_url": "https://www.accuweather.com/en/ph/puerto-princesa/265261/weather-today/265261",
        "accuweather_key": "265261",
        "slug": "puerto-princesa"
    },

    # --- VISAYAS ---
    {
        "id": "cebu_city",
        "name": "Cebu City",
        "province": "Cebu",
        "region": "Central Visayas (Region VII)",
        "island_group": "Visayas",
        "coordinates": {"lat": 10.3157, "lon": 123.8854},
        "accuweather_url": "https://www.accuweather.com/en/ph/cebu-city/262768/weather-today/262768",
        "accuweather_key": "262768",
        "slug": "cebu-city"
    },
    {
        "id": "mandaue",
        "name": "Mandaue City",
        "province": "Cebu",
        "region": "Central Visayas (Region VII)",
        "island_group": "Visayas",
        "coordinates": {"lat": 10.3333, "lon": 123.9333},
        "accuweather_url": "https://www.accuweather.com/en/ph/mandaue/262791/weather-today/262791",
        "accuweather_key": "262791",
        "slug": "mandaue"
    },
    {
        "id": "iloilo_city",
        "name": "Iloilo City",
        "province": "Iloilo",
        "region": "Western Visayas (Region VI)",
        "island_group": "Visayas",
        "coordinates": {"lat": 10.7202, "lon": 122.5621},
        "accuweather_url": "https://www.accuweather.com/en/ph/iloilo-city/263990/weather-today/263990",
        "accuweather_key": "263990",
        "slug": "iloilo-city"
    },
    {
        "id": "bacolod",
        "name": "Bacolod City",
        "province": "Negros Occidental",
        "region": "Negros Island Region",
        "island_group": "Visayas",
        "coordinates": {"lat": 10.6766, "lon": 122.9509},
        "accuweather_url": "https://www.accuweather.com/en/ph/bacolod/264907/weather-today/264907",
        "accuweather_key": "264907",
        "slug": "bacolod"
    },
    {
        "id": "dumaguete",
        "name": "Dumaguete City",
        "province": "Negros Oriental",
        "region": "Negros Island Region",
        "island_group": "Visayas",
        "coordinates": {"lat": 9.3072, "lon": 123.3026},
        "accuweather_url": "https://www.accuweather.com/en/ph/dumaguete/264947/weather-today/264947",
        "accuweather_key": "264947",
        "slug": "dumaguete"
    },
    {
        "id": "tacloban",
        "name": "Tacloban City",
        "province": "Leyte",
        "region": "Eastern Visayas (Region VIII)",
        "island_group": "Visayas",
        "coordinates": {"lat": 11.2433, "lon": 125.0047},
        "accuweather_url": "https://www.accuweather.com/en/ph/tacloban/264426/weather-today/264426",
        "accuweather_key": "264426",
        "slug": "tacloban"
    },
    {
        "id": "tagbilaran",
        "name": "Tagbilaran City",
        "province": "Bohol",
        "region": "Central Visayas (Region VII)",
        "island_group": "Visayas",
        "coordinates": {"lat": 9.6444, "lon": 123.8569},
        "accuweather_url": "https://www.accuweather.com/en/ph/tagbilaran/262402/weather-today/262402",
        "accuweather_key": "262402",
        "slug": "tagbilaran"
    },
    {
        "id": "roxas_city",
        "name": "Roxas City",
        "province": "Capiz",
        "region": "Western Visayas (Region VI)",
        "island_group": "Visayas",
        "coordinates": {"lat": 11.5853, "lon": 122.7511},
        "accuweather_url": "https://www.accuweather.com/en/ph/roxas-city/262557/weather-today/262557",
        "accuweather_key": "262557",
        "slug": "roxas-city"
    },

    # --- MINDANAO ---
    {
        "id": "davao_city",
        "name": "Davao City",
        "province": "Davao del Sur",
        "region": "Davao Region (Region XI)",
        "island_group": "Mindanao",
        "coordinates": {"lat": 7.1907, "lon": 125.4578},
        "accuweather_url": "https://www.accuweather.com/en/ph/davao-city/262923/weather-today/262923",
        "accuweather_key": "262923",
        "slug": "davao-city"
    },
    {
        "id": "cagayan_de_oro",
        "name": "Cagayan de Oro City",
        "province": "Misamis Oriental",
        "region": "Northern Mindanao (Region X)",
        "island_group": "Mindanao",
        "coordinates": {"lat": 8.4542, "lon": 124.6319},
        "accuweather_url": "https://www.accuweather.com/en/ph/cagayan-de-oro/264770/weather-today/264770",
        "accuweather_key": "264770",
        "slug": "cagayan-de-oro"
    },
    {
        "id": "zamboanga_city",
        "name": "Zamboanga City",
        "province": "Zamboanga del Sur",
        "region": "Zamboanga Peninsula (Region IX)",
        "island_group": "Mindanao",
        "coordinates": {"lat": 6.9214, "lon": 122.0790},
        "accuweather_url": "https://www.accuweather.com/en/ph/zamboanga/266447/weather-today/266447",
        "accuweather_key": "266447",
        "slug": "zamboanga"
    },
    {
        "id": "general_santos",
        "name": "General Santos City",
        "province": "South Cotabato",
        "region": "SOCCSKSARGEN (Region XII)",
        "island_group": "Mindanao",
        "coordinates": {"lat": 6.1164, "lon": 125.1716},
        "accuweather_url": "https://www.accuweather.com/en/ph/general-santos/265814/weather-today/265814",
        "accuweather_key": "265814",
        "slug": "general-santos"
    },
    {
        "id": "butuan",
        "name": "Butuan City",
        "province": "Agusan del Norte",
        "region": "Caraga (Region XIII)",
        "island_group": "Mindanao",
        "coordinates": {"lat": 8.9492, "lon": 125.5436},
        "accuweather_url": "https://www.accuweather.com/en/ph/butuan/262078/weather-today/262078",
        "accuweather_key": "262078",
        "slug": "butuan"
    },
    {
        "id": "iligan",
        "name": "Iligan City",
        "province": "Lanao del Norte",
        "region": "Northern Mindanao (Region X)",
        "island_group": "Mindanao",
        "coordinates": {"lat": 8.2280, "lon": 124.2452},
        "accuweather_url": "https://www.accuweather.com/en/ph/iligan/264350/weather-today/264350",
        "accuweather_key": "264350",
        "slug": "iligan"
    },
    {
        "id": "cotabato_city",
        "name": "Cotabato City",
        "province": "Maguindanao del Norte",
        "region": "BARMM",
        "island_group": "Mindanao",
        "coordinates": {"lat": 7.2236, "lon": 124.2464},
        "accuweather_url": "https://www.accuweather.com/en/ph/cotabato/264560/weather-today/264560",
        "accuweather_key": "264560",
        "slug": "cotabato"
    }
]

class PhilippineLocationResolver:
    """Helper to resolve, query, and discover Philippine locations for AccuWeather scraping."""

    @staticmethod
    def get_all_locations() -> List[Dict[str, Any]]:
        return PHILIPPINES_REGIONS_DATA

    @staticmethod
    def get_primary_target() -> Dict[str, Any]:
        for loc in PHILIPPINES_REGIONS_DATA:
            if loc.get("is_primary_target"):
                return loc
        return PHILIPPINES_REGIONS_DATA[0]

    @staticmethod
    def filter_by_island_group(group: str) -> List[Dict[str, Any]]:
        return [loc for loc in PHILIPPINES_REGIONS_DATA if loc.get("island_group", "").lower() == group.lower()]

    @staticmethod
    def search_predefined(query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        return [
            loc for loc in PHILIPPINES_REGIONS_DATA
            if q in loc["name"].lower() or q in loc["province"].lower() or q in loc.get("region", "").lower()
        ]

    @staticmethod
    def query_accuweather_autocomplete(query: str) -> List[Dict[str, Any]]:
        url = f"https://www.accuweather.com/web-api/autocomplete?query={query}&language=en-us"
        try:
            session = requests.Session(impersonate="chrome124")
            resp = session.get(url, headers={"Referer": "https://www.accuweather.com/"}, timeout=10)
            if resp.status_code == 200:
                results = resp.json()
                ph_results = []
                for item in results:
                    key = item.get("key", "")
                    country = item.get("country", "")
                    long_name = item.get("longName", "")
                    if "country=PH" in key or " PH" in long_name or country == "PH":
                        lat = item.get("lat")
                        lon = item.get("lon")
                        name = item.get("name") or long_name
                        slug = name.lower().replace(" ", "-").replace(",", "").replace(".", "")
                        ph_results.append({
                            "id": slug,
                            "name": name,
                            "province": item.get("administrativeArea") or long_name,
                            "region": "Philippines",
                            "island_group": "Philippines",
                            "coordinates": {"lat": lat, "lon": lon},
                            "accuweather_url": f"https://www.accuweather.com/en/ph/{slug}/{key}/weather-today/{key}",
                            "accuweather_key": key,
                            "slug": slug,
                            "raw": item
                        })
                return ph_results
        except Exception as e:
            print(f"[LocationResolver] Autocomplete error for '{query}': {e}")
        return []
