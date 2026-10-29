"""Download raw OpenStreetMap layers for a region and cache them as JSON."""

import json
from datetime import datetime, timezone
from pathlib import Path

from .overpass import bbox_str, run_query

RAW_DIR = Path("data/raw")

# Each layer is one Overpass filter. "out center" gives a point for areas.
LAYERS = {
    "substations": 'nwr["power"="substation"]',
    "plants": 'nwr["power"="plant"]',
    "industrial": 'way["landuse"="industrial"]',
    "freeway_exits": 'node["highway"="motorway_junction"]',
}


def fetch_layer(region: str, bbox: tuple, layer: str) -> Path:
    selector = LAYERS[layer]
    query = f"[out:json][timeout:180];{selector}({bbox_str(bbox)});out center bb tags;"
    data = run_query(query)
    data["gridsite"] = {
        "region": region,
        "layer": layer,
        "loaded_at": datetime.now(timezone.utc).isoformat(),
    }
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{region}_{layer}.json"
    path.write_text(json.dumps(data))
    return path


def fetch_region(region: str, bbox: tuple) -> dict:
    return {layer: fetch_layer(region, bbox, layer) for layer in LAYERS}
