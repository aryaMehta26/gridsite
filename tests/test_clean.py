import pytest

from gridsite.clean import (
    bounds_area_m2,
    clean_plants,
    clean_sites,
    clean_substations,
    parse_capacity_mw,
    parse_max_voltage,
)
from tests.fixtures.mini import INDUSTRIAL, PLANTS, SUBSTATIONS


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("500000;230000;115000", 500_000),
        ("115000", 115_000),
        ("12 kV", 12_000),
        ("69kv;12kv", 69_000),
        ("medium", None),
        (None, None),
    ],
)
def test_parse_max_voltage(raw, expected):
    assert parse_max_voltage(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [("600 MW", 600.0), ("1.2 GW", 1200.0), ("500 kW", 0.5), ("50", 50.0), ("yes", None), (None, None)],
)
def test_parse_capacity(raw, expected):
    assert parse_capacity_mw(raw) == expected


def test_bounds_area_is_roughly_right():
    # 0.004 x 0.004 degrees near 37N is about 445 m x 355 m
    area = bounds_area_m2({"minlat": 37.303, "minlon": -121.907, "maxlat": 37.307, "maxlon": -121.903})
    assert 140_000 < area < 175_000


def test_clean_substations_keeps_points_and_parses_voltage():
    df = clean_substations(SUBSTATIONS)
    assert len(df) == 3
    assert df.set_index("name").loc["Metcalf", "max_voltage_v"] == 500_000


def test_small_sites_are_filtered_out():
    df = clean_sites(INDUSTRIAL)
    assert "Too Small" not in set(df["name"])
    assert len(df) == 2


def test_plants_without_numeric_capacity_are_nan():
    df = clean_plants(PLANTS)
    assert df["capacity_mw"].isna().sum() == 1


def test_bounds_only_elements_get_a_center_point():
    raw = {"elements": [{"type": "way", "id": 99,
                         "bounds": {"minlat": 37.0, "minlon": -122.0, "maxlat": 37.2, "maxlon": -121.8},
                         "tags": {"landuse": "industrial"}}]}
    df = clean_sites(raw)
    assert len(df) == 1
    assert abs(df.loc[0, "lat"] - 37.1) < 1e-9 and abs(df.loc[0, "lon"] + 121.9) < 1e-9


def test_power_plants_and_refineries_are_not_candidate_sites():
    raw = {"elements": [
        {"type": "way", "id": 1, "bounds": {"minlat": 37.0, "minlon": -122.0, "maxlat": 37.01, "maxlon": -121.99},
         "tags": {"landuse": "industrial", "power": "plant", "name": "Some Energy Center"}},
        {"type": "way", "id": 2, "bounds": {"minlat": 37.0, "minlon": -122.0, "maxlat": 37.01, "maxlon": -121.99},
         "tags": {"landuse": "industrial", "industrial": "refinery"}},
        {"type": "way", "id": 3, "bounds": {"minlat": 37.0, "minlon": -122.0, "maxlat": 37.01, "maxlon": -121.99},
         "tags": {"landuse": "industrial", "industrial": "depot"}},
    ]}
    df = clean_sites(raw)
    assert list(df["osm_id"]) == ["way/3"]
