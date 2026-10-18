import pandas as pd
import pytest

from medimesh_ml.scenarios import SCENARIO_DESCRIPTIONS, generate_hospital_data


def test_same_seed_gives_same_data():
    pd.testing.assert_frame_equal(generate_hospital_data(days=3, seed=7), generate_hospital_data(days=3, seed=7))


def test_unknown_scenario_is_rejected():
    with pytest.raises(ValueError):
        generate_hospital_data(scenario="nope")


@pytest.mark.parametrize("name", list(SCENARIO_DESCRIPTIONS))
def test_every_scenario_produces_sane_values(name):
    df = generate_hospital_data(days=14, scenario=name, seed=1)
    assert len(df) == 14 * 24
    assert (df["ed_wait_minutes"] > 0).all()
    assert df["bed_occupancy_pct"].between(0, 100).all()
    assert (df["staff_on_duty"] >= 1).all()


def test_stress_scenarios_are_harder_than_baseline():
    base = generate_hospital_data(days=28, scenario="baseline", seed=1)
    busy = generate_hospital_data(days=28, scenario="busy_er", seed=1)
    thin = generate_hospital_data(days=28, scenario="reduced_staffing", seed=1)
    assert busy["ed_wait_minutes"].mean() > base["ed_wait_minutes"].mean()
    assert thin["ed_wait_minutes"].mean() > base["ed_wait_minutes"].mean()
    assert thin["staff_on_duty"].mean() < base["staff_on_duty"].mean()
