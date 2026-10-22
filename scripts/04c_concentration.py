"""Step 4c · Does consolidation add supply risk? Supplier concentration before and after.

Consolidation moves volume onto fewer suppliers, which raises concentration. This script measures it
per category (UNSPSC family, the same 409 categories as the Kraljic step):

  * Supplier identity = company, not record: duplicate records (R3) are folded into their master in
    BOTH views, so the change shown comes only from the keep / exit decisions.
  * Before = active spend: inactive suppliers (R4, no PO in 18+ months) are left out of both views,
    because that spend has already stopped.
  * After  = spend of R5 (one-time) and R8 (consolidate) suppliers moves to the KEPT suppliers in the
    same category, in proportion to their current spend. If a category has no kept supplier, its spend
    is counted as one catalog / purchasing-card channel.

Measures per category: top supplier's share of spend, number of suppliers, HHI.
Writes outputs/step4c_sole_source_suppliers.csv (the only active company in a category),
outputs/step4c_concentration_summary.csv, outputs/step4c_concentration_by_category.csv and
outputs/step4c_concentration_watchlist.csv (categories where the top supplier crosses 50% after).
"""
import sqlite3
from pathlib import Path

import pandas as pd

DB, OUT = Path("data/procurement.db"), Path("outputs")
THRESH = 0.5

with sqlite3.connect(DB) as con:
    lines = pd.read_sql("SELECT supplier_code, family_title AS category, amount_usd FROM spend_lines", con)
    dec = pd.read_sql("SELECT supplier_code, decision, rule FROM supplier_decisions", con)
    dup = pd.read_sql("SELECT supplier_code, master_code FROM supplier_duplicates", con)
quad = pd.read_csv(OUT / "step3_kraljic_categories.csv")[["category", "quadrant"]]

lines["supplier_code"] = lines.supplier_code.astype(str)
dec["supplier_code"] = dec.supplier_code.astype(str)
dup = dup.astype(str)
master = dict(zip(dup.supplier_code, dup.master_code))
rule = dict(zip(dec.supplier_code, dec.rule))
decision = dict(zip(dec.supplier_code, dec.decision))

lines["company"] = lines.supplier_code.map(lambda s: master.get(s, s))
lines["rule"] = lines.supplier_code.map(rule)
lines = lines[lines.rule != "R4"]                                    # inactive: spend already stopped
lines["kept"] = lines.company.map(decision).eq("KEEP")
lines["moves"] = lines.rule.isin(["R5", "R8"])

before = lines.groupby(["category", "company"]).amount_usd.sum().rename("spend").reset_index()

stay = lines[~lines.moves].groupby(["category", "company", "kept"]).amount_usd.sum().reset_index()
moved = lines[lines.moves].groupby("category").amount_usd.sum()
after_rows = []
for cat, g in stay.groupby("category"):
    k = g[g.kept]
    extra = moved.get(cat, 0.0)
    # suppliers that stay but are not KEPT (e.g. masters of merged records that exit) keep their own spend
    for _, r in g[~g.kept].iterrows():
        after_rows.append((cat, r.company, r.amount_usd))
    if len(k) and k.amount_usd.sum() > 0:
        for _, r in k.iterrows():
            after_rows.append((cat, r.company, r.amount_usd + extra * r.amount_usd / k.amount_usd.sum()))
    elif extra:
        after_rows.append((cat, "CATALOG_CHANNEL", extra))
for cat in set(moved.index) - set(stay.category):                    # categories where every supplier moved
    after_rows.append((cat, "CATALOG_CHANNEL", moved[cat]))
after = pd.DataFrame(after_rows, columns=["category", "company", "spend"])


def per_category(df):
    df = df[df.spend > 0]
    tot = df.groupby("category").spend.transform("sum")
    df = df.assign(share=df.spend / tot)
    return df.groupby("category").agg(spend=("spend", "sum"), suppliers=("company", "nunique"),
                                      top_share=("share", "max"), hhi=("share", lambda s: (s ** 2).sum()))


b, a = per_category(before), per_category(after)
cat = b.join(a, lsuffix="_before", rsuffix="_after", how="outer").join(quad.set_index("category"))
cat["quadrant"] = cat.quadrant.fillna("Unclassified")
cat.to_csv(OUT / "step4c_concentration_by_category.csv")


def summarize(c, label):
    return {
        "group": label, "categories": len(c),
        "top_supplier_over_50pct_before": int((c.top_share_before > THRESH).sum()),
        "top_supplier_over_50pct_after": int((c.top_share_after > THRESH).sum()),
        "single_supplier_before": int((c.suppliers_before == 1).sum()),
        "single_supplier_after": int((c.suppliers_after == 1).sum()),
        "median_top_share_before": c.top_share_before.median(),
        "median_top_share_after": c.top_share_after.median(),
        "median_hhi_before": c.hhi_before.median(), "median_hhi_after": c.hhi_after.median(),
        "spend_in_over_50pct_categories_before_m": c.loc[c.top_share_before > THRESH, "spend_before"].sum() / 1e6,
        "spend_in_over_50pct_categories_after_m": c.loc[c.top_share_after > THRESH, "spend_after"].sum() / 1e6,
    }


rows = [summarize(cat, "All categories")]
for q in ["Strategic", "Bottleneck", "Leverage", "Non-critical"]:
    rows.append(summarize(cat[cat.quadrant == q], q))
summary = pd.DataFrame(rows)
summary.to_csv(OUT / "step4c_concentration_summary.csv", index=False)

watch = cat[(cat.top_share_after > THRESH) & (cat.top_share_before <= THRESH)].sort_values("spend_after", ascending=False)
watch[["quadrant", "spend_after", "suppliers_before", "suppliers_after", "top_share_before", "top_share_after"]] \
    .to_csv(OUT / "step4c_concentration_watchlist.csv")

# sole-source suppliers: the only active company selling into a category (used by tests/test_decisions.py)
sole_cats = b[b.suppliers == 1].index
sole = before[before.category.isin(sole_cats)].rename(columns={"company": "master_code"})
sole["master_decision"] = sole.master_code.map(decision)
sole["category_quadrant"] = sole.category.map(quad.set_index("category").quadrant)
sole.to_csv(OUT / "step4c_sole_source_suppliers.csv", index=False)

pd.set_option("display.width", 200)
print(summary.round(3).T)
print(f"\nNewly over 50% after consolidation: {len(watch)} categories, "
      f"${watch.spend_after.sum()/1e6:,.0f}M of 3-year spend")
print(watch[["quadrant", "spend_after", "suppliers_before", "suppliers_after", "top_share_before",
             "top_share_after"]].head(15).round(3))
