"""Checks on the keep / consolidate / exit decisions (run on the committed outputs; no database needed)."""
from pathlib import Path

import pandas as pd
import pytest

OUT = Path(__file__).resolve().parents[1] / "outputs"
RULES = {"R1": "KEEP", "R2": "KEEP", "R3": "MERGE", "R4": "EXIT", "R5": "EXIT", "R6": "KEEP", "R7": "KEEP",
         "R8": "CONSOLIDATE"}


@pytest.fixture(scope="module")
def dec():
    return pd.read_csv(OUT / "step4_supplier_decisions.csv", dtype={"supplier_code": str})


def test_every_supplier_has_one_decision_and_a_reason_code(dec):
    assert len(dec) == 16_933
    assert dec.supplier_code.is_unique
    assert dec[["rule", "decision", "reason"]].notna().all().all()
    assert (dec.reason.str.len() > 0).all()


def test_rule_and_decision_agree(dec):
    assert set(dec.rule) <= set(RULES)
    assert (dec.rule.map(RULES) == dec.decision).all()


def test_strategic_suppliers_are_never_exited(dec):
    strategic = dec[dec.segment == "A Strategic"]
    assert len(strategic) == 327
    assert (strategic.decision == "KEEP").all()


def test_sole_source_suppliers_are_never_exited():
    """The only active company selling into a category must be kept (rule R2)."""
    sole = pd.read_csv(OUT / "step4c_sole_source_suppliers.csv", dtype={"master_code": str})
    assert len(sole) > 0
    assert (sole.master_decision == "KEEP").all(), sole[sole.master_decision != "KEEP"]


def test_merged_records_point_to_a_master(dec):
    merged = dec[dec.decision == "MERGE"]
    assert merged.master_name.notna().all()


def test_kept_suppliers_have_an_agreement_type(dec):
    kept = dec[dec.decision == "KEEP"]
    assert kept.agreement_if_kept.notna().all()
    assert dec.loc[dec.decision != "KEEP", "agreement_if_kept"].isna().all()


def test_decision_counts_add_up(dec):
    by_rule = pd.read_csv(OUT / "step4_decisions_by_rule.csv")
    assert by_rule.suppliers.sum() == len(dec)
    assert dict(zip(by_rule.rule, by_rule.suppliers)) == dec.rule.value_counts().to_dict()
