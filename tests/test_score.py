import numpy as np
import pytest

from gridsite import checks
from gridsite.clean import clean_plants, clean_points, clean_sites, clean_substations
import pandas as pd

from gridsite.score import assign_tiers, generation_score, linear_decay, score_sites, voltage_score
from tests.fixtures.mini import EXITS, INDUSTRIAL, PLANTS, SUBSTATIONS


def scored():
    return score_sites(
        clean_sites(INDUSTRIAL),
        clean_substations(SUBSTATIONS),
        clean_plants(PLANTS),
        clean_points(EXITS),
    )


def test_components_stay_in_unit_range():
    assert linear_decay(0, 10) == 1.0
    assert linear_decay(25, 10) == 0.0
    assert list(voltage_score([500_000, 230_000, 115_000, 12_000])) == [1.0, 0.8, 0.5, 0.0]
    assert generation_score(1000) == pytest.approx(1.0)
    assert generation_score(0) == 0.0


def test_site_next_to_big_substation_ranks_first():
    df = scored()
    assert df.iloc[0]["name"] == "Near Grid Park"
    assert df.iloc[0]["nearest_hv_substation"] == "Metcalf"
    assert df.iloc[0]["score"] > df.iloc[-1]["score"]


def test_low_voltage_substations_are_ignored():
    df = scored()
    assert "Small Dist" not in set(df["nearest_hv_substation"])


def test_scores_pass_quality_gate():
    df = scored()
    assert checks.check_scores(df) == []
    assert df["score"].between(0, 100).all()


def test_tiers_are_percentile_bands():
    tiers = assign_tiers(pd.Series(range(100)))
    assert (tiers == "A").sum() == 10
    assert (tiers == "B").sum() == 25
    assert (tiers == "C").sum() == 35
    assert (tiers == "D").sum() == 30


def test_no_hv_substation_raises():
    subs = clean_substations(SUBSTATIONS)
    subs["max_voltage_v"] = 1_000
    with pytest.raises(ValueError):
        score_sites(clean_sites(INDUSTRIAL), subs, clean_plants(PLANTS), clean_points(EXITS))


def test_check_points_flags_bad_rows():
    df = clean_sites(INDUSTRIAL)
    df.loc[0, "lat"] = np.nan
    problems = checks.check_points(df, "sites")
    assert any("null" in p for p in problems)
