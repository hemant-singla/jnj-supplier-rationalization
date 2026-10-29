"""Phase 2 · From ~39,000 suppliers: how could J&J go further?

Phase 1 (steps 4-5) used blanket rules: merge duplicates, move one-time vendors to catalog, consolidate
the tail of Leverage and Non-critical categories. Applied to J&J's earlier 80,000 suppliers it gives
44,500 (base) to 38,300 (aggressive), the same range as the ~39,000 J&J reports for FY2025.

Phase 2 is a different model: a category-by-category target count with supply-risk constraints.
Start from the suppliers still managed after the Phase 1 base tier, using one year of spend (FY2014-15).
For every category (UNSPSC family):
  1. Rank the remaining suppliers by their spend in the category.
  2. Keep the smallest set that covers COVERAGE of the category's spend ("core suppliers").
  3. Supply-risk floor: at least 2 suppliers in Strategic and Bottleneck categories (where available),
     at least 1 elsewhere.
A supplier stays if it is core in ANY category it sells into. Always kept, whatever the ranking:
strategic (A-segment) suppliers, sole sources, and small/diverse suppliers (the diversity guardrail).
The rest move their volume to the category's core suppliers or to the catalog.

Outputs: outputs/step8_phase2_summary.csv, step8_phase2_by_quadrant.csv, step8_phase2_coverage_sensitivity.csv
"""
from pathlib import Path
import sqlite3

import pandas as pd

DB, OUT = Path("data/procurement.db"), Path("outputs")
BASE_YEAR = "2014-2015"
COVERAGE = 0.90
JNJ_NOW = 39_000          # J&J Modern Slavery Statement FY2025
COST_PER_SUPPLIER = 2_000  # $ per year to manage a supplier (same assumption as step 5)

with sqlite3.connect(DB) as con:
    lines = pd.read_sql("SELECT supplier_code, family_title AS category, amount_usd FROM spend_lines "
                        "WHERE fiscal_year = ?", con, params=(BASE_YEAR,))
    dec = pd.read_sql("SELECT supplier_code, segment, quadrant, rule, decision, small_or_diverse "
                      "FROM supplier_decisions", con)
quad = pd.read_csv(OUT / "step3_kraljic_categories.csv").set_index("category").quadrant
sole = set(pd.read_csv(OUT / "step4c_sole_source_suppliers.csv", dtype={"master_code": str}).master_code)
lines["supplier_code"] = lines.supplier_code.astype(str)
dec["supplier_code"] = dec.supplier_code.astype(str)
lines["category"] = lines.category.fillna("Unclassified")

# suppliers still managed after the Phase 1 base tier
phase1_out = dec.rule.isin(["R3", "R5"]) | ((dec.rule == "R8") & dec.quadrant.isin(["Leverage", "Non-critical"]))
remaining = set(dec.loc[~phase1_out, "supplier_code"]) & set(lines.supplier_code)
d = dec.set_index("supplier_code")
protected = {s for s in remaining
             if d.at[s, "segment"] == "A Strategic" or s in sole or d.at[s, "small_or_diverse"] == 1}

cat_spend = (lines[lines.supplier_code.isin(remaining)]
             .groupby(["category", "supplier_code"]).amount_usd.sum().reset_index())
cat_spend = cat_spend[cat_spend.amount_usd > 0]


def run(coverage):
    core = set()
    for cat, g in cat_spend.groupby("category"):
        g = g.sort_values("amount_usd", ascending=False)
        share = g.amount_usd.cumsum().shift(fill_value=0) / g.amount_usd.sum()
        n_cov = int((share < coverage).sum())                                  # smallest set reaching coverage
        floor = 2 if quad.get(cat, "Non-critical") in ("Strategic", "Bottleneck") else 1
        core |= set(g.supplier_code.iloc[:max(n_cov, min(floor, len(g)))])
    keep = core | protected
    return keep


keep = run(COVERAGE)
n0, n1 = len(remaining), len(keep)
moved_spend = cat_spend[~cat_spend.supplier_code.isin(keep)].amount_usd.sum()
year_spend = lines[lines.supplier_code.isin(remaining)].amount_usd.sum()
reduction = 1 - n1 / n0
jnj_after = round(JNJ_NOW * (1 - reduction), -2)

summary = pd.DataFrame([
    ("Suppliers managed after Phase 1 (CA, FY2014-15)", n0),
    ("Protected: strategic, sole source or small/diverse", len(protected)),
    (f"Core suppliers kept by the category model ({COVERAGE:.0%} coverage)", n1),
    ("Phase 2 reduction", reduction),
    ("Spend that moves to core suppliers, FY2014-15 ($M)", moved_spend / 1e6),
    ("Share of the year's spend that moves", moved_spend / year_spend),
    ("J&J suppliers now (FY2025)", JNJ_NOW),
    ("J&J suppliers after Phase 2", jnj_after),
    ("J&J process savings, Phase 2 ($M/yr)", (JNJ_NOW - jnj_after) * COST_PER_SUPPLIER / 1e6),
], columns=["metric", "value"])
summary.to_csv(OUT / "step8_phase2_summary.csv", index=False)

rows = []
for q in ["Strategic", "Leverage", "Bottleneck", "Non-critical"]:
    s_q = {s for s in remaining if d.at[s, "quadrant"] == q}
    rows.append((q, len(s_q), len(s_q & keep), 1 - len(s_q & keep) / max(len(s_q), 1)))
pd.DataFrame(rows, columns=["quadrant", "before", "after", "reduction"]).to_csv(
    OUT / "step8_phase2_by_quadrant.csv", index=False)

sens = []
for cov in [0.80, 0.85, 0.90, 0.95]:
    k = run(cov)
    r = 1 - len(k) / n0
    sens.append((cov, len(k), r, round(JNJ_NOW * (1 - r), -2)))
pd.DataFrame(sens, columns=["coverage", "ca_kept", "reduction", "jnj_after"]).to_csv(
    OUT / "step8_phase2_coverage_sensitivity.csv", index=False)

# concentration after Phase 2: categories where the top supplier holds > 50% of the year's spend
after = cat_spend.copy()
after["kept"] = after.supplier_code.isin(keep)
conc_rows = []
for cat, g in after.groupby("category"):
    tot = g.amount_usd.sum()
    b_top = g.amount_usd.max() / tot
    k = g[g.kept]
    a_top = (k.amount_usd.max() + 0) / k.amount_usd.sum() if len(k) else 1.0
    # moved spend goes to kept suppliers pro rata, so the top share after = top kept / kept total
    conc_rows.append((cat, quad.get(cat, "Non-critical"), b_top, a_top))
conc = pd.DataFrame(conc_rows, columns=["category", "quadrant", "top_share_before", "top_share_after"])
conc.to_csv(OUT / "step8_phase2_concentration.csv", index=False)

pd.set_option("display.width", 200)
print(summary.to_string(index=False))
print(pd.read_csv(OUT / "step8_phase2_by_quadrant.csv"))
print(pd.read_csv(OUT / "step8_phase2_coverage_sensitivity.csv"))
print("categories top>50%: before", int((conc.top_share_before > .5).sum()), "after", int((conc.top_share_after > .5).sum()),
      "of", len(conc))
print(conc.groupby("quadrant").apply(lambda g: pd.Series({"before": (g.top_share_before > .5).sum(),
                                                           "after": (g.top_share_after > .5).sum()})))
