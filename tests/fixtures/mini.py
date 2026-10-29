"""Tiny hand-made Overpass responses used by the tests (no network needed)."""


def overpass(elements):
    return {"elements": elements}


SUBSTATIONS = overpass([
    {"type": "way", "id": 1, "center": {"lat": 37.30, "lon": -121.90},
     "tags": {"power": "substation", "name": "Metcalf", "voltage": "500000;230000;115000"}},
    {"type": "way", "id": 2, "center": {"lat": 37.40, "lon": -121.95},
     "tags": {"power": "substation", "name": "Small Dist", "voltage": "12 kV"}},
    {"type": "node", "id": 3, "lat": 37.50, "lon": -122.00,
     "tags": {"power": "substation", "name": "No Voltage"}},
])

PLANTS = overpass([
    {"type": "way", "id": 10, "center": {"lat": 37.31, "lon": -121.91},
     "tags": {"power": "plant", "plant:output:electricity": "600 MW", "plant:source": "gas"}},
    {"type": "way", "id": 11, "center": {"lat": 38.50, "lon": -121.00},
     "tags": {"power": "plant", "plant:output:electricity": "yes"}},
])

INDUSTRIAL = overpass([
    {"type": "way", "id": 20, "center": {"lat": 37.305, "lon": -121.905},
     "bounds": {"minlat": 37.303, "minlon": -121.907, "maxlat": 37.307, "maxlon": -121.903},
     "tags": {"landuse": "industrial", "name": "Near Grid Park"}},
    {"type": "way", "id": 21, "center": {"lat": 37.45, "lon": -122.20},
     "bounds": {"minlat": 37.448, "minlon": -122.202, "maxlat": 37.452, "maxlon": -122.198},
     "tags": {"landuse": "industrial", "name": "Far Lot"}},
    {"type": "way", "id": 22, "center": {"lat": 37.35, "lon": -121.92},
     "bounds": {"minlat": 37.3499, "minlon": -121.9201, "maxlat": 37.3501, "maxlon": -121.9199},
     "tags": {"landuse": "industrial", "name": "Too Small"}},
])

EXITS = overpass([
    {"type": "node", "id": 30, "lat": 37.306, "lon": -121.906, "tags": {"highway": "motorway_junction"}},
])
