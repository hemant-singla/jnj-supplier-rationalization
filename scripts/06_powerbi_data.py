"""Step 6: build the Power BI data file (one clean table per sheet, star-schema friendly).

Sheets
  Suppliers   one row per supplier: segment, primary category, quadrant, spend, decision, rule, flags
  Categories  one row per category: Kraljic quadrant, spend, suppliers, risk signals
  Pareto      cumulative share of spend vs share of suppliers (every 50th supplier + endpoints)
  Savings     J&J savings by scenario and lever (long format), measured vs assumption
  PriceGap    goods items bought from both kept and exiting suppliers
  Rules       rule code -> decision and reason
"""
import sqlite3
from pathlib import Path

import pandas as pd

OUT = Path("outputs/powerbi/JnJ_PowerBI_Data.xlsx")
OUT.parent.mkdir(parents=True, exist_ok=True)

with sqlite3.connect("data/procurement.db") as con:
    seg = pd.read_sql("SELECT supplier_code, spend_rank, cum_share, inactive_18m, one_time FROM supplier_segments", con)
    pareto = pd.read_sql("SELECT spend_rank, cum_share FROM supplier_segments ORDER BY spend_rank", con)

dec = pd.read_csv("outputs/step4_supplier_decisions.csv", dtype={"supplier_code": str})
sup = dec.merge(seg, on="supplier_code")
sup["spend_per_year"] = sup.spend_usd / 3
sup["kept"] = (sup.decision == "KEEP").astype(int)
sup["small_or_diverse"] = sup.small_or_diverse.map({1: "Yes", 0: "No"})
sup = sup.rename(columns={
    "supplier_code": "Supplier Code", "supplier_name": "Supplier", "segment": "Segment",
    "primary_category": "Category", "quadrant": "Quadrant", "spend_usd": "Spend 3yr", "spend_per_year": "Spend per Year",
    "po_count": "POs", "departments": "Departments", "last_po_date": "Last PO", "small_or_diverse": "Small or Diverse",
    "score": "Score", "rule": "Rule", "decision": "Decision", "reason": "Reason", "master_name": "Merge Into",
    "agreement_if_kept": "Agreement", "spend_rank": "Spend Rank", "inactive_18m": "Inactive 18m",
    "one_time": "One Time", "kept": "Kept"})
sup["Last PO"] = pd.to_datetime(sup["Last PO"])
sup["Decision Order"] = sup.Decision.map({"KEEP": 1, "CONSOLIDATE": 2, "MERGE": 3, "EXIT": 4})
sup = sup[["Supplier Code", "Supplier", "Segment", "Category", "Quadrant", "Decision", "Rule", "Reason", "Agreement",
           "Merge Into", "Spend 3yr", "Spend per Year", "POs", "Departments", "Last PO", "Score", "Small or Diverse",
           "Inactive 18m", "One Time", "Kept", "Spend Rank", "Decision Order"]]

cat = pd.read_csv("outputs/step3_kraljic_categories.csv").rename(columns={
    "category": "Category", "segment_title": "UNSPSC Segment", "quadrant": "Quadrant", "agreement": "Agreement",
    "spend_usd": "Spend 3yr", "suppliers": "Suppliers", "active_suppliers": "Active Suppliers",
    "pct_noncompetitive": "Pct Noncompetitive", "pct_top3": "Pct Top 3", "risk_score": "Risk Score"})
cat["Pct Noncompetitive"] /= 100
cat["Pct Top 3"] /= 100

n = len(pareto)
p = pareto[(pareto.spend_rank % 50 == 1) | (pareto.spend_rank == n)].copy()
p = pd.concat([pd.DataFrame({"spend_rank": [0], "cum_share": [0.0]}), p])
p["Pct Suppliers"] = p.spend_rank / n
p = p.rename(columns={"spend_rank": "Supplier Rank", "cum_share": "Pct Spend"})

s = pd.read_csv("outputs/step5_savings_scenarios.csv")
lev = []
for _, r in s.iterrows():
    for lever, col, basis, order in [("Price gap on re-routed spend", "jnj_price_m", "Measured", 1),
                                     ("Process: fewer active suppliers", "jnj_process_m", "Measured", 2),
                                     ("Re-tender of kept leverage suppliers", "jnj_retender_m", "Assumption", 3)]:
        lev.append((r.scenario, lever, basis, order, round(r[col], 1)))
savings = pd.DataFrame(lev, columns=["Scenario", "Lever", "Basis", "Lever Order", "Savings $M per Year"])
savings["Scenario Order"] = savings.Scenario.map({"Low": 1, "Base": 2, "High": 3})
summary = s[["scenario", "jnj_run_rate_m", "jnj_one_time_m", "jnj_npv_m", "data_backed_share"]].round(3)
summary.columns = ["Scenario", "Run Rate $M", "One Time Cost $M", "NPV 3yr $M", "Share Measured"]
summary["Goal $M"] = 300
inp = dict(pd.read_csv("outputs/step5_model_inputs.csv").values)
spend_ratio = 35000 / inp["CA addressable spend per year ($M)"]
summary["Measured $M"] = (s.jnj_price_m + s.jnj_process_m).round(1).values
summary["Retender Needed"] = ((300 - summary["Measured $M"]).clip(lower=0)
                              / (inp["Kept spend per year, Leverage categories ($M)"] * spend_ratio)).round(4)
summary["Scenario Order"] = summary.Scenario.map({"Low": 1, "Base": 2, "High": 3})

gap = pd.read_csv("outputs/step5_price_gap_goods.csv").rename(columns={
    "unspsc": "UNSPSC", "item": "Item", "quadrant": "Quadrant", "kept_median_price": "Kept Median Price",
    "exiting_median_price": "Exiting Median Price", "gap": "Price Gap", "kept_lines": "Kept Lines",
    "exiting_lines": "Exiting Lines", "exiting_spend": "Exiting Spend"})

quads = pd.DataFrame({
    "Quadrant": ["Strategic", "Leverage", "Bottleneck", "Non-critical"],
    "Quadrant Order": [1, 2, 3, 4],
    "Approach": ["Keep and partner: MOU + supply agreement", "Tender and consolidate: MSA with 2-3 suppliers",
                 "Secure supply: long-term agreement + 2nd source", "Simplify: catalog / purchasing card"]})
top = cat.sort_values("Suppliers", ascending=False).head(15)[["Category", "Quadrant", "Suppliers", "Spend 3yr"]]
top["Fragmentation Rank"] = range(1, len(top) + 1)
rules = pd.read_csv("outputs/step4_decisions_by_rule.csv")[["rule", "decision", "reason"]]
rules.columns = ["Rule", "Decision", "Reason"]

with pd.ExcelWriter(OUT) as xw:
    for name, df in [("Suppliers", sup), ("Categories", cat), ("Pareto", p[["Supplier Rank", "Pct Suppliers", "Pct Spend"]]),
                     ("Savings", savings), ("Scenarios", summary), ("PriceGap", gap), ("Rules", rules), ("Quadrants", quads), ("TopFragmented", top)]:
        df.to_excel(xw, sheet_name=name, index=False)
print("saved", OUT, {k: len(v) for k, v in [("Suppliers", sup), ("Categories", cat), ("Savings", savings)]})
