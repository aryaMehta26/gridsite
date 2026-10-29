"""Data-quality gates. The pipeline stops if any of these fail."""

import pandas as pd


class DataQualityError(Exception):
    pass


def check_points(df: pd.DataFrame, name: str, bbox: tuple | None = None, min_rows: int = 1) -> list[str]:
    problems = []
    if len(df) < min_rows:
        problems.append(f"{name}: expected at least {min_rows} rows, got {len(df)}")
    if df[["lat", "lon"]].isna().any().any():
        problems.append(f"{name}: null coordinates")
    if not df["lat"].between(-90, 90).all() or not df["lon"].between(-180, 180).all():
        problems.append(f"{name}: coordinates outside WGS84 range")
    if df["osm_id"].duplicated().any():
        problems.append(f"{name}: duplicate osm_id values")
    if bbox is not None and len(df):
        south, west, north, east = bbox
        pad = 0.05  # areas can straddle the box edge; their centers may sit just outside
        inside = df["lat"].between(south - pad, north + pad) & df["lon"].between(west - pad, east + pad)
        if not inside.all():
            problems.append(f"{name}: {int((~inside).sum())} points fall outside the region")
    return problems


def check_scores(df: pd.DataFrame) -> list[str]:
    problems = []
    if not df["score"].between(0, 100).all():
        problems.append("scores outside [0, 100]")
    if df["hv_substation_km"].lt(0).any():
        problems.append("negative distances")
    return problems


def enforce(problems: list[str]) -> None:
    if problems:
        raise DataQualityError("; ".join(problems))
