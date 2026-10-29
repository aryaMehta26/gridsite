"""Turn raw Overpass JSON into tidy, validated DataFrames."""

import json
import math
import re
from pathlib import Path

import pandas as pd

from .config import EXCLUDED_INDUSTRIAL, MIN_SITE_AREA_M2

EARTH_RADIUS_M = 6_371_000


def parse_max_voltage(value) -> float | None:
    """Return the highest voltage in volts from an OSM voltage tag.

    OSM stores multiple levels separated by ';' (e.g. "500000;230000"),
    and some mappers write kV ("115 kV") instead of volts.
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    levels = []
    for part in str(value).split(";"):
        part = part.strip().lower()
        match = re.match(r"^([\d.]+)\s*(kv)?$", part)
        if not match:
            continue
        number = float(match.group(1))
        levels.append(number * 1000 if match.group(2) else number)
    return max(levels) if levels else None


def parse_capacity_mw(value) -> float | None:
    """Parse plant:output:electricity values such as '50 MW' or '1.2 GW'."""
    if not value:
        return None
    match = re.match(r"^\s*([\d.]+)\s*(kw|mw|gw)?\s*$", str(value).lower())
    if not match:
        return None
    number = float(match.group(1))
    unit = match.group(2) or "mw"
    return number * {"kw": 0.001, "mw": 1.0, "gw": 1000.0}[unit]


def bounds_area_m2(bounds: dict | None) -> float | None:
    """Approximate an area from its bounding box (good enough for filtering)."""
    if not bounds:
        return None
    lat_mid = math.radians((bounds["minlat"] + bounds["maxlat"]) / 2)
    height = math.radians(bounds["maxlat"] - bounds["minlat"]) * EARTH_RADIUS_M
    width = math.radians(bounds["maxlon"] - bounds["minlon"]) * EARTH_RADIUS_M * math.cos(lat_mid)
    return abs(height * width)


def elements_to_frame(raw: dict) -> pd.DataFrame:
    """Flatten Overpass elements into one row per feature with a point."""
    rows = []
    for el in raw.get("elements", []):
        if "lat" in el:
            lat, lon = el["lat"], el["lon"]
        elif "center" in el:
            lat, lon = el["center"]["lat"], el["center"]["lon"]
        elif "bounds" in el:
            # With "out center bb", Overpass returns only the bounding box for ways.
            b = el["bounds"]
            lat, lon = (b["minlat"] + b["maxlat"]) / 2, (b["minlon"] + b["maxlon"]) / 2
        else:
            continue
        tags = el.get("tags", {})
        rows.append(
            {
                "osm_id": f"{el['type']}/{el['id']}",
                "lat": lat,
                "lon": lon,
                "name": tags.get("name"),
                "tags": tags,
                "area_m2": bounds_area_m2(el.get("bounds")),
            }
        )
    frame = pd.DataFrame(rows, columns=["osm_id", "lat", "lon", "name", "tags", "area_m2"])
    return frame.drop_duplicates(subset="osm_id").reset_index(drop=True)


def load_raw(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def clean_substations(raw: dict) -> pd.DataFrame:
    df = elements_to_frame(raw)
    df["max_voltage_v"] = df["tags"].apply(lambda t: parse_max_voltage(t.get("voltage")))
    df["operator"] = df["tags"].apply(lambda t: t.get("operator"))
    return df.drop(columns="tags")


def clean_plants(raw: dict) -> pd.DataFrame:
    df = elements_to_frame(raw)
    df["capacity_mw"] = df["tags"].apply(lambda t: parse_capacity_mw(t.get("plant:output:electricity")))
    df["source"] = df["tags"].apply(lambda t: t.get("plant:source"))
    return df.drop(columns="tags")


def is_usable_site(tags: dict) -> bool:
    """Skip power plants/substations mapped as industrial land, and hazardous uses."""
    if "power" in tags:
        return False
    return tags.get("industrial") not in EXCLUDED_INDUSTRIAL


def clean_sites(raw: dict) -> pd.DataFrame:
    df = elements_to_frame(raw)
    df = df[df["tags"].apply(is_usable_site)]
    df = df[df["area_m2"].fillna(0) >= MIN_SITE_AREA_M2]
    return df.drop(columns="tags").reset_index(drop=True)


def clean_points(raw: dict) -> pd.DataFrame:
    return elements_to_frame(raw).drop(columns="tags")
