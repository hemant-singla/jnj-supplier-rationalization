"""Step 4b · Question 3: Which suppliers stay and which go?

Scorecard (0-100, percentile ranks within the supplier's primary category):
  spend in category 30 · recency of last PO 20 · departments served 20 ·
  share of spend bought competitively 15 · share bought through an existing contract vehicle 15

Rules, applied in order — the first rule that matches sets the decision and the reason code:
  R1 KEEP        A-segment (strategic) supplier
  R2 KEEP        Supply protection: one of the top-3 active suppliers in a Strategic or Bottleneck category,
                 or the only active supplier (sole source) in any category it sells into
  R3 MERGE       Duplicate record of another supplier (step 4a) — fold into the master record
  R4 EXIT        Inactive: no PO in the last 18 months
  R5 EXIT        One-time vendor: one PO in three years — future buys go to catalog / preferred suppliers
  R6 KEEP        Preferred supplier: among the suppliers making up 80% of its primary category's spend,
                 or scorecard in the top 10% of its category
  R7 KEEP        Small / diverse guardrail: active small or diverse business, routed to the
                 preferred-supplier development program instead of being cut
  R8 CONSOLIDATE Everything else: volume moves to the category's preferred suppliers
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

DB, OUT = Path("data/procurement.db"), Path("outputs")
COMPETITIVE = ("Formal Competitive", "Informal Competitive", "Statement of Qualifications", "SB/DVBE Option")
CONTRACT = ("Statewide Contract", "Master Service Agreement", "WSCA/Coop", "CMAS", "Software License Program",
            "Master Purchase/Price Agreement", "State Price Schedule")
DATA_END = pd.Timestamp("2015-06-30")

with sqlite3.connect(DB) as con:
    sup = pd.read_sql("SELECT * FROM supplier_segments", con)
    lines = pd.read_sql("SELECT supplier_code, family_title, acquisition_method, amount_usd FROM spend_lines", con)
    dups = pd.read_sql("SELECT supplier_code, master_code, master_name FROM supplier_duplicates", con)
quad = pd.read_csv(OUT / "step3_kraljic_categories.csv")[["category", "quadrant"]]

# primary category = where the supplier has most of its spend
lines["family_title"] = lines.family_title.fillna("Unclassified")
by_cat = lines.groupby(["supplier_code", "family_title"]).amount_usd.sum().reset_index()
primary = by_cat.sort_values("amount_usd", ascending=False).drop_duplicates("supplier_code")
primary = primary.rename(columns={"family_title": "primary_category", "amount_usd": "spend_in_primary"})
sup = sup.merge(primary, on="supplier_code", how="left")
sup = sup.merge(quad.rename(columns={"category": "primary_category"}), on="primary_category", how="left")
sup["quadrant"] = sup.quadrant.fillna("Non-critical")

method = lines.assign(comp=lines.acquisition_method.isin(COMPETITIVE) * lines.amount_usd,
                      contr=lines.acquisition_method.isin(CONTRACT) * lines.amount_usd)
m = method.groupby("supplier_code")[["comp", "contr", "amount_usd"]].sum()
sup = sup.merge((m.comp / m.amount_usd).rename("pct_competitive"), on="supplier_code", how="left")
sup = sup.merge((m.contr / m.amount_usd).rename("pct_on_contract"), on="supplier_code", how="left")
sup["months_since_po"] = (DATA_END - pd.to_datetime(sup.last_po_date)).dt.days / 30.4

# ---- scorecard: percentile ranks within primary category -----------------------------
g = sup.groupby("primary_category")
sup["score"] = (30 * g.spend_in_primary.rank(pct=True)
                + 20 * g.months_since_po.rank(pct=True, ascending=False)
                + 20 * g.departments.rank(pct=True)
                + 15 * g.pct_competitive.rank(pct=True)
                + 15 * g.pct_on_contract.rank(pct=True)).round(1)
sup["score_pct_in_cat"] = g.score.rank(pct=True)

# category position: cumulative share of the primary category held by this supplier and bigger ones
sup = sup.sort_values(["primary_category", "spend_in_primary"], ascending=[True, False])
cat_total = sup.groupby("primary_category").spend_in_primary.transform("sum")
sup["cat_cum_share_before"] = (sup.groupby("primary_category").spend_in_primary.cumsum()
                               - sup.spend_in_primary) / cat_total
active = sup[sup.inactive_18m == 0]
sup["active_rank_in_cat"] = active.groupby("primary_category").spend_in_primary.rank(ascending=False, method="first")
sup = sup.merge(dups, on="supplier_code", how="left")

# sole-source: the only active company (duplicate records folded into their master) selling into a category
company = dict(zip(dups.supplier_code.astype(str), dups.master_code.astype(str)))
act_lines = lines[lines.supplier_code.isin(active.supplier_code)].assign(
    company=lambda d: d.supplier_code.astype(str).map(lambda s: company.get(s, s)))
n_comp = act_lines.groupby("family_title").company.nunique()
sole_companies = set(act_lines[act_lines.family_title.isin(n_comp[n_comp == 1].index)].company)
sup["sole_source"] = sup.supplier_code.astype(str).isin(sole_companies) & sup.master_code.isna()

# ---- rules -----------------------------------------------------------------------------
rules = [
    ("R1", "KEEP", "Strategic (A-segment) supplier", sup.segment == "A Strategic"),
    ("R2", "KEEP", "Supply protection: top-3 active supplier in a Strategic/Bottleneck category, "
                   "or the only active supplier in any category",
     (sup.quadrant.isin(["Strategic", "Bottleneck"]) & (sup.active_rank_in_cat <= 3)) | sup.sole_source),
    ("R3", "MERGE", "Duplicate record: fold into master supplier", sup.master_code.notna()),
    ("R4", "EXIT", "Inactive: no PO in 18+ months", sup.inactive_18m == 1),
    ("R5", "EXIT", "One-time vendor: 1 PO in 3 years; route future buys to preferred/catalog", sup.one_time == 1),
    ("R6", "KEEP", "Preferred supplier: core of category spend or top-10% scorecard",
     (sup.cat_cum_share_before < 0.80) | (sup.score_pct_in_cat >= 0.90)),
    ("R7", "KEEP", "Small/diverse guardrail: move to preferred-supplier development program",
     sup.small_or_diverse == 1),
    ("R8", "CONSOLIDATE", "Volume moves to the category's preferred suppliers", pd.Series(True, index=sup.index)),
]
sup["rule"], sup["decision"], sup["reason"] = None, None, None
for code, decision, reason, cond in rules:
    take = sup.rule.isna() & cond
    sup.loc[take, ["rule", "decision", "reason"]] = [code, decision, reason]

AGREEMENT = {"Strategic": "Partnership MOU + supply agreement", "Bottleneck": "Long-term supply agreement + 2nd source",
             "Leverage": "MSA with volume-tiered pricing", "Non-critical": "Catalog / purchasing card"}
sup["agreement_if_kept"] = np.where(sup.decision == "KEEP", sup.quadrant.map(AGREEMENT), "")

cols = ["supplier_code", "supplier_name", "segment", "primary_category", "quadrant", "spend_usd", "po_count",
        "departments", "last_po_date", "small_or_diverse", "score", "rule", "decision", "reason",
        "master_name", "agreement_if_kept"]
result = sup[cols].sort_values("spend_usd", ascending=False)
with sqlite3.connect(DB) as con:
    result.to_sql("supplier_decisions", con, if_exists="replace", index=False)
result.to_csv(OUT / "step4_supplier_decisions.csv", index=False)

# ---- summaries ---------------------------------------------------------------------------
n, total = len(result), result.spend_usd.sum()
by_rule = result.groupby(["rule", "decision", "reason"]).agg(suppliers=("supplier_code", "count"),
                                                            spend_m=("spend_usd", "sum")).reset_index()
by_rule["spend_m"] = (by_rule.spend_m / 1e6).round(1)
by_rule.to_csv(OUT / "step4_decisions_by_rule.csv", index=False)

by_seg = pd.crosstab(result.segment, result.decision, margins=True)
by_seg.to_csv(OUT / "step4_decisions_by_segment.csv")

kept = result.decision == "KEEP"
div_before = result.loc[result.small_or_diverse == 1, "spend_usd"].sum()
div_kept = result.loc[kept & (result.small_or_diverse == 1), "spend_usd"].sum()
spend = lambda mask: round(result.loc[mask, "spend_usd"].sum() / 1e6, 1)
active_div = (result.small_or_diverse == 1) & (result.rule != "R4")
headline = pd.DataFrame([
    ("Suppliers before", n),
    ("Suppliers kept", int(kept.sum())),
    ("Supplier reduction (all records)", round(1 - kept.sum() / n, 3)),
    ("Active suppliers before (excl. inactive 18m)", int((result.rule != "R4").sum())),
    ("Supplier reduction (active base)", round(1 - kept.sum() / (result.rule != "R4").sum(), 3)),
    ("Spend with kept suppliers, 3 yrs ($M)", spend(kept)),
    ("Spend to re-route to kept suppliers: consolidate + one-time, 3 yrs ($M)",
     spend(result.rule.isin(["R5", "R8"]))),
    ("Spend on merged duplicates (same company, admin only), 3 yrs ($M)", spend(result.rule == "R3")),
    ("Spend with inactive suppliers (already stopped), 3 yrs ($M)", spend(result.rule == "R4")),
    ("Small/diverse spend, active suppliers ($M)", spend(active_div)),
    ("Small/diverse spend kept ($M)", spend(kept & (result.small_or_diverse == 1))),
    ("Small/diverse active spend retained", round(result.loc[kept & active_div, "spend_usd"].sum()
                                                  / result.loc[active_div, "spend_usd"].sum(), 3)),
], columns=["metric", "value"])
headline.to_csv(OUT / "step4_headline.csv", index=False)

pd.set_option("display.width", 220, "display.max_colwidth", 80)
print(by_rule.to_string(index=False)); print(); print(by_seg); print(); print(headline.to_string(index=False))
