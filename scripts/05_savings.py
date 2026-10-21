"""Step 5 · Question 4: What is it worth? Savings model on the real keep / exit list.

Three savings levers, each tied to a step-4 decision. Spend is annualized (3-year total / 3).

  1. Price gap on re-routed spend (R5 one-time + R8 consolidate): spend moves to preferred
     suppliers. Rate per Kraljic quadrant = MEASURED in the data: median unit-price gap between
     exiting and kept suppliers for the same goods item (scripts/05_savings.py: price_gap()).
     Low = 0, base = half the measured gap, high = the measured gap. Quadrants where exiting
     suppliers were not dearer get 0.
  2. Re-tender of kept suppliers in Leverage categories: more volume with fewer suppliers.
     ASSUMPTION (cannot be measured in this data): low 0.5% / base 1.5% / high 3%.
  3. Process savings: active supplier records removed (R3 merge, R5, R8) x cost to maintain a
     supplier per year. ASSUMPTION: $1,000 / $2,000 / $3,000. Inactive records (R4) save $0.

One-time cost: transition per supplier by rule + program cost (0.057% of annual spend, the same
ratio as the J&J business case: $20M on $35B) + 15% contingency.
Scale to J&J: price and re-tender savings and program cost scale with spend ($35B / CA annual spend);
process savings and transition cost scale with supplier count (29,000 / 16,933).
"""
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DB, OUT = Path("data/procurement.db"), Path("outputs")
YEARS, JNJ_SPEND, JNJ_SUPPLIERS = 3, 35_000.0, 29_000
RAMP, DISC, CONT = [0.3, 0.7, 1.0], 0.08, 0.15
PROGRAM_RATIO = 20 / 35_000
TRANSITION = {"R8": 2_500, "R5": 500, "R3": 200, "R4": 50}          # $ per supplier
RETENDER = {"Low": 0.005, "Base": 0.015, "High": 0.03}
COST_PER_SUPPLIER = {"Low": 1_000, "Base": 2_000, "High": 3_000}
PRICE_FACTOR = {"Low": 0.0, "Base": 0.5, "High": 1.0}


def price_gap(con) -> pd.DataFrame:
    """Median unit-price gap, exiting (R5/R8) vs kept suppliers, same UNSPSC code + item name, goods only."""
    l = pd.read_sql("""
        SELECT l.normalized_unspsc AS u, LOWER(TRIM(l.item_name)) AS item, l.quantity AS q,
               l.unit_price AS p, l.amount_usd AS a, d.decision, d.rule, d.quadrant
        FROM spend_lines l JOIN supplier_decisions d USING (supplier_code)
        WHERE l.quantity > 0 AND l.unit_price > 0 AND l.normalized_unspsc IS NOT NULL
          AND l.item_name IS NOT NULL AND l.acquisition_type IN ('NON-IT Goods', 'IT Goods')""", con)
    l = l[(l.q * l.p - l.a).abs() <= 0.02 * l.a.clip(lower=1)]          # quantity x unit price = total
    l["moved"], l["kept"] = l.rule.isin(["R5", "R8"]), l.decision == "KEEP"
    rows = []
    for (u, item), d in l.groupby(["u", "item"]):
        k, m = d[d.kept], d[d.moved]
        if len(k) >= 3 and len(m) >= 3:
            kp, mp = np.median(k.p), np.median(m.p)
            rows.append((u, item, d.quadrant.iloc[0], kp, mp, (mp - kp) / mp, len(k), len(m), m.a.sum()))
    g = pd.DataFrame(rows, columns=["unspsc", "item", "quadrant", "kept_median_price", "exiting_median_price",
                                    "gap", "kept_lines", "exiting_lines", "exiting_spend"])
    return g[g.gap.between(-1, 0.9)]


with sqlite3.connect(DB) as con:
    gaps = price_gap(con)
    dec = pd.read_sql("SELECT rule, decision, quadrant, spend_usd FROM supplier_decisions", con)
gaps.to_csv(OUT / "step5_price_gap_goods.csv", index=False)

measured = gaps.groupby("quadrant").agg(items=("gap", "size"), median_gap=("gap", "median"),
                                        share_items_dearer=("gap", lambda s: (s > 0).mean()))
measured["rate_used_high"] = measured.median_gap.clip(lower=0)
measured = measured.reindex(["Leverage", "Non-critical", "Bottleneck", "Strategic"])
measured.to_csv(OUT / "step5_measured_price_gap.csv")

annual = lambda mask: dec.loc[mask, "spend_usd"].sum() / YEARS / 1e6       # $M per year
ca_spend = annual(dec.index == dec.index)
moved = {q: annual(dec.rule.isin(["R5", "R8"]) & (dec.quadrant == q)) for q in measured.index}
kept_leverage = annual((dec.decision == "KEEP") & (dec.quadrant == "Leverage"))
removed_active = int(dec.rule.isin(["R3", "R5", "R8"]).sum())
counts = dec.rule.value_counts()
transition_ca = sum(counts.get(r, 0) * c for r, c in TRANSITION.items()) / 1e6
program_ca = PROGRAM_RATIO * ca_spend
spend_ratio, sup_ratio = JNJ_SPEND / ca_spend, JNJ_SUPPLIERS / len(dec)

rows = []
for sc in ["Low", "Base", "High"]:
    price = sum(moved[q] * measured.rate_used_high[q] * PRICE_FACTOR[sc] for q in measured.index)
    retender = kept_leverage * RETENDER[sc]
    process = removed_active * COST_PER_SUPPLIER[sc] / 1e6
    run = price + retender + process
    one_time = (program_ca + transition_ca) * (1 + CONT)
    jnj_price, jnj_retender, jnj_process = price * spend_ratio, retender * spend_ratio, process * sup_ratio
    jnj_run = jnj_price + jnj_retender + jnj_process
    jnj_one = (program_ca * spend_ratio + transition_ca * sup_ratio) * (1 + CONT)
    flows = [r * jnj_run for r in RAMP]
    npv = -jnj_one + sum(f / (1 + DISC) ** (i + 1) for i, f in enumerate(flows))
    rows.append(dict(scenario=sc, price_gap_m=price, retender_m=retender, process_m=process, run_rate_ca_m=run,
                     pct_of_spend=run / ca_spend, one_time_ca_m=one_time, jnj_price_m=jnj_price, jnj_retender_m=jnj_retender,
                     jnj_process_m=jnj_process, jnj_run_rate_m=jnj_run,
                     jnj_one_time_m=jnj_one, jnj_3yr_savings_m=sum(flows), jnj_npv_m=npv,
                     data_backed_share=(jnj_price + jnj_process) / jnj_run))
res = pd.DataFrame(rows)
res.to_csv(OUT / "step5_savings_scenarios.csv", index=False)

inputs = pd.DataFrame([
    ("CA addressable spend per year ($M)", ca_spend),
    *[(f"Re-routed spend per year, {q} ($M)", moved[q]) for q in measured.index],
    ("Kept spend per year, Leverage categories ($M)", kept_leverage),
    ("Active supplier records removed (R3+R5+R8)", removed_active),
    *[(f"Suppliers under {r}", int(counts.get(r, 0))) for r in TRANSITION],
    ("CA suppliers", len(dec)),
], columns=["input", "value"])
inputs.to_csv(OUT / "step5_model_inputs.csv", index=False)

# ---- chart: base-case bridge, J&J scale ------------------------------------------------
b = res.set_index("scenario").loc["Base"]
steps = [("Price gap on\nre-routed spend", b.jnj_price_m, "data"),
         ("Process: fewer\nactive suppliers", b.jnj_process_m, "data"),
         ("Re-tender of kept\nleverage suppliers", b.jnj_retender_m, "assumption")]
measured_total = b.jnj_price_m + b.jnj_process_m
fig, ax = plt.subplots(figsize=(9, 5.2), dpi=150)
base = 0
for i, (lab, v, kind) in enumerate(steps):
    ax.bar(i, v, bottom=base, color="#1baf7a" if kind == "data" else "#a3d9c4", width=0.6,
           hatch=None if kind == "data" else "//", edgecolor="white")
    ax.text(i, base + v + 6, f"+${v:,.0f}M", ha="center", fontsize=10)
    base += v
ax.bar(3, base, color="#888780", width=0.6)
ax.text(3, base + 6, f"${base:,.0f}M", ha="center", fontsize=11, weight="bold")
ax.bar(4, 384.6, color="#d3d1c7", width=0.6)
ax.text(4, 384.6 + 6, "$385M", ha="center", fontsize=10, color="#5f5e5a")
ax.set_xticks(range(5), [s[0] for s in steps] + ["Real-data\nrun-rate", "Original\nbusiness case"])
ax.set_ylabel("J&J run-rate savings ($M per year)")
ax.set_title(f"Only \\${measured_total:,.0f}M of the \\${base:,.0f}M base case is measured in the data\n"
             f"J&J scale, base case · solid = measured, hatched = assumption", loc="left", fontsize=11)
ax.spines[["top", "right"]].set_visible(False)
ax.set_ylim(0, max(base, 384.6) * 1.15)
fig.tight_layout()
fig.savefig("docs/images/savings_bridge_real.png")

pd.set_option("display.width", 220)
print(measured.round(3)); print(); print(inputs.round(1).to_string(index=False)); print()
print(res.round(2).T)
