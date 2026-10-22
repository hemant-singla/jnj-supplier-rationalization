"""The savings model adds up, and the break-even claim is reproducible."""
from pathlib import Path

import pandas as pd
import pytest

OUT = Path(__file__).resolve().parents[1] / "outputs"


@pytest.fixture(scope="module")
def sc():
    return pd.read_csv(OUT / "step5_savings_scenarios.csv").set_index("scenario")


def test_run_rate_is_the_sum_of_its_levers(sc):
    parts = sc.jnj_price_m + sc.jnj_retender_m + sc.jnj_process_m
    assert (parts - sc.jnj_run_rate_m).abs().max() < 1e-6


def test_scenarios_are_ordered(sc):
    assert sc.loc["Low", "jnj_run_rate_m"] < sc.loc["Base", "jnj_run_rate_m"] < sc.loc["High", "jnj_run_rate_m"]


def test_base_case_headline(sc):
    assert sc.loc["Base", "jnj_run_rate_m"] == pytest.approx(366.0, abs=0.5)
    measured = sc.loc["Base", "jnj_price_m"] + sc.loc["Base", "jnj_process_m"]
    assert measured == pytest.approx(85.7, abs=0.5)


def test_breakeven_rate_reaches_the_goal_exactly():
    be = pd.read_csv(OUT / "step5b_breakeven.csv", index_col=0)
    inp = pd.read_csv(OUT / "step5_model_inputs.csv").set_index("input").value
    kept_lev = inp["Kept spend per year, Leverage categories ($M)"] * 35_000 / inp["CA addressable spend per year ($M)"]
    rate = be.loc["Base", "breakeven_retender_rate"]
    assert be.loc["Base", "measured_savings_m"] + rate * kept_lev == pytest.approx(300.0, abs=1e-6)
    assert rate == pytest.approx(0.0115, abs=0.0001)


def test_sensitivity_is_increasing_and_crosses_the_goal_once():
    t = pd.read_csv(OUT / "step5b_retender_sensitivity.csv")
    assert t.run_rate_m_measured_base.is_monotonic_increasing
    assert t.meets_goal_base.astype(int).diff().fillna(0).abs().sum() == 1
