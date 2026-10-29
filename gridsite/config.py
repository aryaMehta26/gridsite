"""All tunable settings live here so the scoring is easy to audit."""

# Bounding boxes as (south, west, north, east).
REGIONS = {
    "bay_area": (37.10, -122.55, 38.05, -121.55),
    "stockton": (37.70, -121.55, 38.15, -121.05),
}

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
USER_AGENT = "gridsite/0.1 (open-source student project)"

# A substation counts as "high voltage" at or above this level (volts).
HIGH_VOLTAGE_V = 115_000

# Candidate sites smaller than this are skipped (a truck depot needs room).
MIN_SITE_AREA_M2 = 8_000  # roughly 2 acres

# Industrial land that is not a realistic truck-depot site.
EXCLUDED_INDUSTRIAL = {"refinery", "oil", "natural_gas", "shipyard", "water", "communication"}

# Tiers are percentile bands of the final score, so each tier stays meaningful.
TIER_PERCENTILES = {"A": 0.90, "B": 0.65, "C": 0.30}  # top 10% A, next 25% B, next 35% C, rest D

# Distances beyond these contribute zero to their score component (km).
SUBSTATION_RANGE_KM = 10.0
FREEWAY_RANGE_KM = 5.0
GENERATION_RADIUS_KM = 16.0  # ~10 miles

# Component weights. They sum to 1.0 so the final score stays in [0, 100].
WEIGHTS = {
    "substation_distance": 0.40,
    "voltage_class": 0.20,
    "freeway_access": 0.25,
    "local_generation": 0.15,
}
