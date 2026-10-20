"""Step 3 · Question 2: How should each category be handled? (Kraljic matrix)

Unit: UNSPSC family (category). Two axes, both measured from the real data:

  Value (profit impact)  = category spend. "High value" = the largest categories that together
                           make up 80% of addressable spend.
  Supply risk            = average percentile rank of three signals:
                             1. non-competitive share: % of spend bought sole-source (NCB),
                                as an emergency purchase, or by special category request
                             2. concentration: % of category spend with its top 3 suppliers
                             3. thin supply base: fewer active suppliers = higher risk
                           Signals 2 and 3 are ranked within size bands so small categories
                           are not flagged just for being small. "High risk" = above the median.

At J&J the risk axis would also carry regulatory weight (GMP-qualified, patient-critical inputs);
that flag does not exist in public data, so here risk is market-based only.
"""
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DB, OUT = Path("data/procurement.db"), Path("outputs")
NONCOMP = ("NCB", "Emergency Purchase", "Special Category Request (SCR)")

AGREEMENT = {
    "Strategic": "Partnership MOU + supply agreement; joint planning",
    "Bottleneck": "Long-term supply agreement + qualify a second source",
    "Leverage": "Competitive tender; MSA with 2-3 preferred suppliers",
    "Non-critical": "Catalog / marketplace / purchasing card",
}

with sqlite3.connect(DB) as con:
    lines = pd.read_sql(
        "SELECT family_title AS category, segment_title, supplier_code, acquisition_method, amount_usd "
        "FROM spend_lines WHERE family_title IS NOT NULL", con)
    seg = pd.read_sql("SELECT supplier_code, segment, inactive_18m FROM supplier_segments", con)

lines = lines.merge(seg, on="supplier_code")
lines["noncomp"] = lines.acquisition_method.isin(NONCOMP) * lines.amount_usd

by_sup = lines.groupby(["category", "supplier_code"]).amount_usd.sum().reset_index()
top3 = (by_sup.sort_values("amount_usd", ascending=False).groupby("category").head(3)
        .groupby("category").amount_usd.sum())
active = lines[lines.inactive_18m == 0].groupby("category").supplier_code.nunique()

cat = lines.groupby("category").agg(
    segment_title=("segment_title", "first"),
    spend_usd=("amount_usd", "sum"),
    noncomp_usd=("noncomp", "sum"),
    suppliers=("supplier_code", "nunique"),
)
cat["active_suppliers"] = active.reindex(cat.index).fillna(0).astype(int)
cat["pct_noncompetitive"] = 100 * cat.noncomp_usd / cat.spend_usd
cat["pct_top3"] = 100 * top3.reindex(cat.index) / cat.spend_usd
# Small categories naturally have few suppliers and high concentration, so signals 2 and 3 are
# ranked WITHIN size bands (quintiles of spend): risk is judged against categories of similar size.
cat["size_band"] = pd.qcut(np.log10(cat.spend_usd), 5, labels=False)
band = cat.groupby("size_band")
cat["risk_score"] = (cat.pct_noncompetitive.rank(pct=True)
                     + band.pct_top3.rank(pct=True)
                     + band.active_suppliers.rank(pct=True, ascending=False)) / 3

cat = cat.sort_values("spend_usd", ascending=False)
cat["cum_share"] = cat.spend_usd.cumsum() / cat.spend_usd.sum()
cat["high_value"] = (cat.cum_share - cat.spend_usd / cat.spend_usd.sum()) < 0.80

risk_cut = cat.risk_score.median()
cat["high_risk"] = cat.risk_score > risk_cut

cat["quadrant"] = np.select(
    [cat.high_value & cat.high_risk, ~cat.high_value & cat.high_risk, cat.high_value & ~cat.high_risk],
    ["Strategic", "Bottleneck", "Leverage"], "Non-critical")
cat["agreement"] = cat.quadrant.map(AGREEMENT)

out = cat.reset_index()[["category", "segment_title", "quadrant", "agreement", "spend_usd", "suppliers",
                         "active_suppliers", "pct_noncompetitive", "pct_top3", "risk_score"]]
out.round(3).to_csv(OUT / "step3_kraljic_categories.csv", index=False)

summary = out.groupby("quadrant").agg(categories=("category", "count"), spend_b=("spend_usd", "sum"),
                                      suppliers=("suppliers", "sum"))
summary["spend_b"] = (summary.spend_b / 1e9).round(2)
summary["pct_spend"] = (100 * summary.spend_b / summary.spend_b.sum()).round(1)
summary = summary.reindex(["Strategic", "Bottleneck", "Leverage", "Non-critical"])
summary.to_csv(OUT / "step3_kraljic_summary.csv")

# --- 2x2 chart -------------------------------------------------------------
colors = {"Strategic": "#2a78d6", "Bottleneck": "#eb6834", "Leverage": "#1baf7a", "Non-critical": "#a3a29b"}
fig, ax = plt.subplots(figsize=(10, 7), dpi=150)
for q, d in out.groupby("quadrant"):
    ax.scatter(d.spend_usd / 1e6, d.risk_score, s=np.clip(d.suppliers, 8, 600) * 0.6,
               c=colors[q], alpha=0.55, edgecolors="white", linewidths=0.5, label=q)
value_cut = cat[cat.high_value].spend_usd.min() / 1e6
ax.axvline(value_cut, color="#888780", lw=1, ls="--")
ax.axhline(risk_cut, color="#888780", lw=1, ls="--")
ax.set_xscale("log")
ax.set_xlabel("Category spend, FY2012-15 (log scale; categories under $10K not shown)")
ax.set_ylabel("Supply risk score (0 = low, 1 = high)")
ax.set_title("Kraljic matrix: 409 real procurement categories\nbubble size = number of suppliers",
             loc="left", fontsize=12)
for label, x, y in [("Bottleneck", 0.02, 0.97), ("Strategic", 0.98, 0.97),
                    ("Non-critical", 0.02, 0.03), ("Leverage", 0.98, 0.03)]:
    ax.text(x, y, label, transform=ax.transAxes, ha="left" if x < 0.5 else "right",
            va="top" if y > 0.5 else "bottom", fontsize=13, color=colors[label], weight="bold")
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
    lambda v, _: f"${v * 1000:,.0f}K" if v < 1 else (f"${v:,.0f}M" if v < 1000 else f"${v / 1000:,.0f}B")))
ax.set_xlim(left=0.01)
labelled = pd.concat([cat[cat.quadrant == "Leverage"].nlargest(3, "spend_usd"),
                      cat[cat.quadrant == "Strategic"].nlargest(3, "spend_usd")])
for i, (name, r) in enumerate(labelled.iterrows()):
    ax.annotate(name[:32], (r.spend_usd / 1e6, r.risk_score), fontsize=7.5, color="#444441",
                xytext=(-8, 10 if i % 2 else -14), textcoords="offset points", ha="right",
                arrowprops=dict(arrowstyle="-", color="#b4b2a9", lw=0.6),
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig("docs/images/kraljic_matrix.png")

pd.set_option("display.width", 200)
print(f"value cut: ${value_cut:,.1f}M   risk cut: {risk_cut:.3f}")
print(summary)
for q in ["Strategic", "Bottleneck", "Leverage", "Non-critical"]:
    d = out[out.quadrant == q].nlargest(6, "spend_usd")
    print(f"\n{q}:")
    print(d[["category", "spend_usd", "suppliers", "pct_noncompetitive", "pct_top3"]]
          .assign(spend_usd=lambda x: (x.spend_usd / 1e6).round(1)).round(1).to_string(index=False))
