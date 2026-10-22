"""Totals reconcile from the raw file to the decisions.

The first tests run on committed outputs. The raw-data tests need the downloaded CSV and the SQLite database
built by scripts/01_clean_load.py; they are skipped when those files are not present.
"""
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT, DB = ROOT / "outputs", ROOT / "data" / "procurement.db"
RAW = ROOT / "data" / "raw" / "purchase-order-data-2012-2015-.csv"
RAW_ROWS, KEPT_ROWS = 344_504, 278_632
EXCLUDED = {"exempt_method": 44_341, "public_body_or_health_plan": 15_276, "missing_or_zero_amount": 6_255}
ADDRESSABLE_USD = 21_872_596_938  # 3-year addressable spend after cleaning (data/README.md)


def test_cleaning_counts_add_up_to_the_raw_file():
    assert KEPT_ROWS + sum(EXCLUDED.values()) == RAW_ROWS


def test_decisions_cover_all_addressable_spend():
    dec = pd.read_csv(OUT / "step4_supplier_decisions.csv")
    assert dec.spend_usd.sum() == pytest.approx(ADDRESSABLE_USD, rel=1e-6)


def test_segments_cover_all_addressable_spend():
    seg = pd.read_csv(OUT / "step2_segment_summary.csv")
    spend_col = [c for c in seg.columns if "spend" in c.lower()][0]
    total = seg[spend_col].sum()
    scale = 1e9 if total < 1e3 else (1e6 if total < 1e6 else 1)
    assert total * scale == pytest.approx(ADDRESSABLE_USD, rel=1e-3)


needs_db = pytest.mark.skipif(not DB.exists(), reason="data/procurement.db not built (run scripts/01_clean_load.py)")
needs_raw = pytest.mark.skipif(not RAW.exists(), reason="raw CSV not downloaded (see data/README.md)")


@needs_db
def test_every_raw_row_has_a_status_and_every_exclusion_a_reason():
    with sqlite3.connect(DB) as con:
        st = pd.read_sql("SELECT status, exclusion_reason FROM raw_line_status", con)
    assert len(st) == RAW_ROWS
    assert set(st.status) == {"KEPT", "EXCLUDED"}
    ex = st[st.status == "EXCLUDED"]
    assert ex.exclusion_reason.notna().all() and (ex.exclusion_reason != "").all()
    assert ex.exclusion_reason.value_counts().to_dict() == EXCLUDED
    assert (st.status == "KEPT").sum() == KEPT_ROWS


@needs_db
def test_kept_lines_match_spend_table_and_decisions():
    with sqlite3.connect(DB) as con:
        kept = con.execute("SELECT SUM(amount_usd_parsed) FROM raw_line_status WHERE status='KEPT'").fetchone()[0]
        lines = con.execute("SELECT COUNT(*), SUM(amount_usd) FROM spend_lines").fetchone()
        dec = con.execute("SELECT SUM(spend_usd) FROM supplier_decisions").fetchone()[0]
    assert lines[0] == KEPT_ROWS
    assert kept == pytest.approx(lines[1], rel=1e-9)
    assert dec == pytest.approx(lines[1], rel=1e-9)
    assert lines[1] == pytest.approx(ADDRESSABLE_USD, rel=1e-6)


@needs_raw
def test_raw_file_has_the_expected_rows():
    raw = pd.read_csv(RAW, dtype=str, keep_default_na=False, usecols=[0])
    assert len(raw) == RAW_ROWS
