"""Score candidate sites. Every component is in [0, 1] and documented."""

import numpy as np
import pandas as pd

from .config import (
    FREEWAY_RANGE_KM,
    GENERATION_RADIUS_KM,
    HIGH_VOLTAGE_V,
    SUBSTATION_RANGE_KM,
    TIER_PERCENTILES,
    WEIGHTS,
)
from .geo import nearest, within_radius


def linear_decay(distance_km, range_km):
    """1.0 at the site, falling linearly to 0.0 at range_km and beyond."""
    return np.clip(1.0 - np.asarray(distance_km) / range_km, 0.0, 1.0)


def voltage_score(voltage_v):
    """Higher transmission voltage usually means more capacity to tap."""
    v = np.nan_to_num(np.asarray(voltage_v, dtype=float), nan=0.0)
    return np.select(
        [v >= 345_000, v >= 230_000, v >= HIGH_VOLTAGE_V],
        [1.0, 0.8, 0.5],
        default=0.0,
    )


def generation_score(capacity_mw):
    """Log-scaled so one huge plant doesn't swamp everything (1 GW -> 1.0)."""
    mw = np.nan_to_num(np.asarray(capacity_mw, dtype=float), nan=0.0)
    return np.clip(np.log10(1 + mw) / np.log10(1 + 1000), 0.0, 1.0)


def assign_tiers(scores: pd.Series) -> pd.Series:
    """Percentile bands: top 10% A, next 25% B, next 35% C, rest D."""
    pct = scores.rank(pct=True, method="max")
    return pd.Series(
        np.select(
            [pct > TIER_PERCENTILES["A"], pct > TIER_PERCENTILES["B"], pct > TIER_PERCENTILES["C"]],
            ["A", "B", "C"],
            default="D",
        ),
        index=scores.index,
    )


def score_sites(sites, substations, plants, exits) -> pd.DataFrame:
    sites = sites.copy()
    hv = substations[substations["max_voltage_v"].fillna(0) >= HIGH_VOLTAGE_V].reset_index(drop=True)
    if hv.empty:
        raise ValueError("No high-voltage substations found in this region")

    sub_idx, sub_km = nearest(sites["lat"], sites["lon"], hv["lat"], hv["lon"])
    sites["nearest_hv_substation"] = hv.loc[sub_idx, "name"].fillna("(unnamed)").values
    sites["nearest_hv_osm_id"] = hv.loc[sub_idx, "osm_id"].values
    sites["nearest_hv_voltage_kv"] = hv.loc[sub_idx, "max_voltage_v"].values / 1000
    sites["hv_substation_km"] = sub_km

    if exits.empty:
        sites["freeway_exit_km"] = np.inf
    else:
        _, exit_km = nearest(sites["lat"], sites["lon"], exits["lat"], exits["lon"])
        sites["freeway_exit_km"] = exit_km

    rated = plants.dropna(subset=["capacity_mw"])
    if rated.empty:
        sites["generation_mw_10mi"] = 0.0
    else:
        mask = within_radius(sites["lat"], sites["lon"], rated["lat"], rated["lon"], GENERATION_RADIUS_KM)
        sites["generation_mw_10mi"] = mask @ rated["capacity_mw"].to_numpy()

    components = {
        "substation_distance": linear_decay(sites["hv_substation_km"], SUBSTATION_RANGE_KM),
        "voltage_class": voltage_score(sites["nearest_hv_voltage_kv"] * 1000),
        "freeway_access": linear_decay(sites["freeway_exit_km"], FREEWAY_RANGE_KM),
        "local_generation": generation_score(sites["generation_mw_10mi"]),
    }
    total = np.zeros(len(sites))
    for name, values in components.items():
        sites[f"c_{name}"] = np.round(values, 3)
        total += WEIGHTS[name] * values
    sites["score"] = np.round(100 * total, 1)
    sites["tier"] = assign_tiers(sites["score"])
    return sites.sort_values("score", ascending=False).reset_index(drop=True)
