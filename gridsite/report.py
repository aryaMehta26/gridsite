"""Interactive map, charts, and a JSON summary for the README and Pages."""

import json
from pathlib import Path

import folium
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

TIER_COLORS = {"A": "#1a9850", "B": "#91cf60", "C": "#fee08b", "D": "#d73027"}


TIER_LABELS = {"A": "Tier A (top 10%)", "B": "Tier B", "C": "Tier C", "D": "Tier D"}


def _site_popup(rank: int, row) -> str:
    gmaps = f"https://www.google.com/maps?q={row.lat:.5f},{row.lon:.5f}&t=k"
    return (
        f"<b>#{rank} · score {row.score} · tier {row.tier}</b><br>"
        f"{row.area_m2 / 4047:.1f} acres (bbox estimate)<br>"
        f"{row.hv_substation_km:.2f} km to {row.nearest_hv_substation or 'substation'} "
        f"({row.nearest_hv_voltage_kv:.0f} kV)<br>"
        f"{row.freeway_exit_km:.2f} km to freeway exit<br>"
        f"{row.generation_mw_10mi:.0f} MW generation within 10 mi<br>"
        f"<a href='{gmaps}' target='_blank'>satellite view</a>"
    )


def _legend() -> str:
    rows = "".join(
        f"<div><span style='background:{c};border:1px solid #333;display:inline-block;"
        f"width:11px;height:11px;border-radius:50%;margin-right:6px'></span>{TIER_LABELS[t]}</div>"
        for t, c in TIER_COLORS.items()
    )
    return (
        "<div style='position:fixed;bottom:24px;left:12px;z-index:9999;background:white;padding:10px 12px;"
        "border-radius:6px;box-shadow:0 1px 4px rgba(0,0,0,.3);font:12px/1.6 sans-serif'>"
        "<b>GridSite: fleet-depot candidate sites</b><br>"
        f"{rows}<div><span style='display:inline-block;width:11px;height:11px;background:#08306b;"
        "margin-right:6px'></span>Substation &ge;115 kV (size = voltage)</div>"
        "<div style='color:#666'>Click a site for its score breakdown</div></div>"
    )


def build_map(sites, substations, center, out_path: Path) -> None:
    fmap = folium.Map(location=center, zoom_start=9, tiles="OpenStreetMap", control_scale=True)
    fmap.fit_bounds([[sites.lat.min(), sites.lon.min()], [sites.lat.max(), sites.lon.max()]])

    sub_layer = folium.FeatureGroup(name="Substations ≥115 kV")
    for row in substations.itertuples():
        kv = (row.max_voltage_v or 0) / 1000
        folium.RegularPolygonMarker(
            location=(row.lat, row.lon),
            number_of_sides=4,
            radius=4 + kv / 80,
            color="#08306b",
            weight=1,
            fill=True,
            fill_color="#08306b",
            fill_opacity=0.85,
            tooltip=f"{row.name or 'Substation'} · {kv:.0f} kV",
        ).add_to(sub_layer)

    ranked = sites.sort_values("score", ascending=False).reset_index(drop=True)
    for tier in "DCBA":  # draw A last so the best sites sit on top
        layer = folium.FeatureGroup(name=TIER_LABELS[tier], show=tier in "AB")
        for rank, row in ranked[ranked.tier == tier].iterrows():
            folium.CircleMarker(
                location=(row.lat, row.lon),
                radius=7 if tier == "A" else 4,
                color="#333",
                weight=1,
                fill=True,
                fill_color=TIER_COLORS[tier],
                fill_opacity=0.9,
                tooltip=f"#{rank + 1} · score {row.score}",
                popup=folium.Popup(_site_popup(rank + 1, row), max_width=280),
            ).add_to(layer)
        layer.add_to(fmap)
    sub_layer.add_to(fmap)

    fmap.get_root().html.add_child(folium.Element(_legend()))
    folium.LayerControl(collapsed=False).add_to(fmap)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(str(out_path))


def build_charts(sites, substations, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(sites["score"], bins=25, color="#2c7fb8", edgecolor="white")
    ax.set_title("Candidate site scores")
    ax.set_xlabel("Score (0-100)")
    ax.set_ylabel("Sites")
    paths.append(_save(fig, out_dir / "score_distribution.png"))

    fig, ax = plt.subplots(figsize=(7, 4))
    kv = (substations["max_voltage_v"].dropna() / 1000).round()
    counts = kv.value_counts().sort_index()
    ax.bar([f"{int(k)}" for k in counts.index], counts.values, color="#41ab5d")
    ax.set_title("Substations by highest voltage (kV)")
    ax.set_xlabel("kV")
    ax.set_ylabel("Substations")
    ax.tick_params(axis="x", rotation=45)
    paths.append(_save(fig, out_dir / "substations_by_voltage.png"))

    fig, ax = plt.subplots(figsize=(7, 4))
    for t, color in TIER_COLORS.items():
        part = sites[sites["tier"] == t]
        ax.scatter(part["hv_substation_km"], part["freeway_exit_km"], s=8, color=color, label=f"Tier {t}")
    ax.set_title("Grid distance vs truck access")
    ax.set_xlabel("km to nearest >=115 kV substation")
    ax.set_ylabel("km to nearest freeway exit")
    ax.legend()
    paths.append(_save(fig, out_dir / "grid_vs_access.png"))

    # Static overview map for the README (no basemap tiles needed).
    hv = substations[substations["max_voltage_v"].fillna(0) >= 115_000]
    fig, ax = plt.subplots(figsize=(8, 7))
    for t in ["D", "C", "B", "A"]:
        part = sites[sites["tier"] == t]
        ax.scatter(part["lon"], part["lat"], s=6 if t != "A" else 14, color=TIER_COLORS[t], label=f"Tier {t} site", alpha=0.85)
    ax.scatter(hv["lon"], hv["lat"], s=(hv["max_voltage_v"] / 1000) / 6, marker="^", facecolor="none",
               edgecolor="#08306b", linewidth=0.8, label=">=115 kV substation (size = kV)")
    ax.set_title("Candidate fleet-charging sites vs. high-voltage substations")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect(1 / 0.79)  # ~cos(37.8 deg) so the map isn't stretched
    ax.legend(loc="lower left", fontsize=8)
    paths.append(_save(fig, out_dir / "overview_map.png"))
    return paths


def _save(fig, path: Path) -> Path:
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def write_summary(summary: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, default=str))
