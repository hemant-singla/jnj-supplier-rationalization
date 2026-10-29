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
    assert sc.loc["Base", "jnj_run_rate_m"] == pytest.approx(414.1, abs=0.5)
    measured = sc.loc["Base", "jnj_price_m"] + sc.loc["Base", "jnj_process_m"]
    assert measured == pytest.approx(133.8, abs=0.5)


def test_breakeven_rate_reaches_the_goal_exactly():
    be = pd.read_csv(OUT / "step5b_breakeven.csv", index_col=0)
    inp = pd.read_csv(OUT / "step5_model_inputs.csv").set_index("input").value
    kept_lev = inp["Kept spend per year, Leverage categories ($M)"] * 35_000 / inp["CA addressable spend per year ($M)"]
    rate = be.loc["Base", "breakeven_retender_rate"]
    assert be.loc["Base", "measured_savings_m"] + rate * kept_lev == pytest.approx(300.0, abs=1e-6)
    assert rate == pytest.approx(0.0089, abs=0.0001)


def test_sensitivity_is_increasing_and_crosses_the_goal_once():
    t = pd.read_csv(OUT / "step5b_retender_sensitivity.csv")
    assert t.run_rate_m_measured_base.is_monotonic_increasing
    assert t.meets_goal_base.astype(int).diff().fillna(0).abs().sum() == 1


def test_supplier_tiers_are_nested_and_scaled_from_80000():
    t = pd.read_csv(OUT / "step5_jnj_supplier_tiers.csv").set_index("tier")
    assert (t.jnj_before == 80_000).all()
    assert t.loc["Conservative", "reduction"] < t.loc["Base", "reduction"] < t.loc["Aggressive", "reduction"]
    assert (t.ca_removed == t.ca_removed_R3 + t.ca_removed_R5 + t.ca_removed_R8).all()


def test_phase2_keeps_protected_suppliers_and_reduces_from_39000():
    p2 = pd.read_csv(OUT / "step8_phase2_summary.csv").set_index("metric").value
    assert p2["Core suppliers kept by the category model (90% coverage)"] >= p2["Protected: strategic, sole source or small/diverse"]
    assert 0 < p2["Phase 2 reduction"] < 0.5
    assert p2["J&J suppliers after Phase 2"] < p2["J&J suppliers now (FY2025)"] == 39_000


def test_backtest_brackets_the_reported_count():
    bt = pd.read_csv(OUT / "step9_jnj_timeline_backtest.csv").set_index("kenvue_case")
    # J&J's reported ~39,000 sits inside the range our Phase 1 tiers give on the post-Kenvue base
    assert bt.model_base.min() <= 39_000 <= bt.model_conservative.max()
