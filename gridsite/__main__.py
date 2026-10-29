"""Command line: python -m gridsite run --regions bay_area stockton"""

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import checks
from .clean import clean_plants, clean_points, clean_sites, clean_substations, load_raw
from .config import HIGH_VOLTAGE_V, REGIONS
from .ingest import LAYERS, RAW_DIR, fetch_layer
from .report import build_charts, build_map, write_summary
from .score import score_sites

PROCESSED = Path("data/processed")
DOCS = Path("docs")


def load_region(region: str, use_cache: bool):
    bbox = REGIONS[region]
    for layer in LAYERS:
        if not use_cache or not (RAW_DIR / f"{region}_{layer}.json").exists():
            fetch_layer(region, bbox, layer)
    raw = lambda layer: load_raw(RAW_DIR / f"{region}_{layer}.json")  # noqa: E731
    subs = clean_substations(raw("substations"))
    plants = clean_plants(raw("plants"))
    sites = clean_sites(raw("industrial"))
    exits = clean_points(raw("freeway_exits"))
    problems = (
        checks.check_points(subs, f"{region}/substations", bbox, min_rows=5)
        + checks.check_points(sites, f"{region}/sites", bbox, min_rows=5)
        + checks.check_points(exits, f"{region}/exits", bbox, min_rows=1)
    )
    checks.enforce(problems)
    for df in (subs, plants, sites, exits):
        df["region"] = region
    return subs, plants, sites, exits


def run(regions: list[str], use_cache: bool) -> dict:
    parts = [load_region(r, use_cache) for r in regions]
    subs, plants, sites, exits = (pd.concat(p, ignore_index=True) for p in zip(*parts))
    subs, plants, sites, exits = (df.drop_duplicates(subset="osm_id") for df in (subs, plants, sites, exits))

    scored = score_sites(sites, subs, plants, exits)
    checks.enforce(checks.check_scores(scored))

    PROCESSED.mkdir(parents=True, exist_ok=True)
    scored.to_csv(PROCESSED / "sites_scored.csv", index=False)
    hv = subs[subs["max_voltage_v"].fillna(0) >= HIGH_VOLTAGE_V]
    hv.to_csv(PROCESSED / "hv_substations.csv", index=False)

    center = [scored["lat"].mean(), scored["lon"].mean()]
    build_map(scored, hv, center, DOCS / "index.html")
    build_charts(scored, subs, DOCS / "img")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "regions": regions,
        "substations": int(len(subs)),
        "hv_substations_115kv_plus": int(len(hv)),
        "power_plants": int(len(plants)),
        "plants_with_capacity": int(plants["capacity_mw"].notna().sum()),
        "candidate_sites": int(len(scored)),
        "freeway_exits": int(len(exits)),
        "tier_counts": scored["tier"].value_counts().sort_index().to_dict(),
        "median_km_to_hv_substation": round(float(scored["hv_substation_km"].median()), 2),
        "top_10": scored.head(10)[
            ["osm_id", "name", "region", "score", "tier", "hv_substation_km", "nearest_hv_substation",
             "nearest_hv_voltage_kv", "freeway_exit_km"]
        ].astype(object).where(scored.head(10).notna(), None).to_dict(orient="records"),
    }
    write_summary(summary, PROCESSED / "summary.json")
    return summary


def main():
    parser = argparse.ArgumentParser(prog="gridsite")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run", help="ingest, score, and publish")
    run_p.add_argument("--regions", nargs="+", default=list(REGIONS), choices=list(REGIONS))
    run_p.add_argument("--use-cache", action="store_true", help="reuse files already in data/raw; only download missing layers")
    args = parser.parse_args()
    summary = run(args.regions, args.use_cache)
    print(f"Scored {summary['candidate_sites']} sites against {summary['hv_substations_115kv_plus']} "
          f"high-voltage substations. Tiers: {summary['tier_counts']}")


if __name__ == "__main__":
    main()
