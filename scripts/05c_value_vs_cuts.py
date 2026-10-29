"""Step 5c · Small cut, big impact: savings depend little on how many suppliers are cut.

Every cut has to be justified, noticed and defended with the buyers who use the supplier, so cuts are costly.
At the BASE savings rates, compare the three tiers: suppliers cut at J&J scale, run-rate savings, one-time cost.
Most of the value is the re-tender of kept Leverage suppliers, which needs few cuts; and a small number of
large suppliers hold most of that spend.

Reads outputs/step5_jnj_supplier_tiers.csv and outputs/step4_supplier_decisions.csv.
Writes outputs/step5c_value_vs_cuts.csv and docs/images/value_vs_cuts.png.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

OUT, IMG = Path("outputs"), Path("docs/images")
t = pd.read_csv(OUT / "step5_jnj_supplier_tiers.csv").set_index("tier")
dec = pd.read_csv(OUT / "step4_supplier_decisions.csv")
lev = dec[(dec.decision == "KEEP") & (dec.quadrant == "Leverage")].sort_values("spend_usd", ascending=False)
n80 = int((lev.spend_usd.cumsum() / lev.spend_usd.sum() <= 0.80).sum()) + 1

v = t[["reduction", "jnj_suppliers_cut", "jnj_after", "base_rate_price_m", "base_rate_process_m", "base_rate_retender_m",
       "base_rate_run_rate_m", "base_rate_one_time_m", "savings_per_supplier_cut_k"]].copy()
v["share_of_base_value"] = v.base_rate_run_rate_m / v.loc["Base", "base_rate_run_rate_m"]
v["extra_suppliers_cut_vs_previous"] = v.jnj_suppliers_cut.diff()
v["extra_savings_m_vs_previous"] = v.base_rate_run_rate_m.diff()
v["extra_one_time_m_vs_previous"] = v.base_rate_one_time_m.diff()
v["kept_leverage_suppliers"] = len(lev)
v["suppliers_holding_80pct_of_kept_leverage_spend"] = n80
v.to_csv(OUT / "step5c_value_vs_cuts.csv")

INK, MUTED, ACCENT, ASSUME, GRID = "#14213D", "#5F6B7A", "#0F766E", "#A7D7CF", "#E3E6EA"
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 4.8), dpi=150, gridspec_kw={"wspace": 0.35})
names = ["Conservative", "Base", "Aggressive"]
x = range(3)
a1.bar(x, v.loc[names, "jnj_suppliers_cut"], color=["#C9D1DC", "#8C99AB", "#5F6B7A"], width=0.6)
for i, n in enumerate(names):
    a1.text(i, v.loc[n, "jnj_suppliers_cut"] + 700, f"{v.loc[n, 'jnj_suppliers_cut']:,.0f}\n(−{v.loc[n, 'reduction']:.0%})",
            ha="center", fontsize=9.5, color=INK)
a1.set_title("Suppliers cut (from 80,000)", loc="left", fontsize=11, color=INK)
a1.set_xticks(list(x), names)
a1.set_ylim(0, v.jnj_suppliers_cut.max() * 1.25)
a1.yaxis.set_major_formatter(lambda y, _: f"{y:,.0f}")
measured = v.loc[names, "base_rate_price_m"] + v.loc[names, "base_rate_process_m"]
a2.bar(x, measured, color=ACCENT, width=0.6, label="Measured: price gap + fewer suppliers")
a2.bar(x, v.loc[names, "base_rate_retender_m"], bottom=measured, color=ASSUME, width=0.6,
       label="Assumed: re-tender of kept suppliers")
for i, n in enumerate(names):
    a2.text(i, v.loc[n, "base_rate_run_rate_m"] + 8,
            f"${v.loc[n, 'base_rate_run_rate_m']:,.0f}M\none-time ${v.loc[n, 'base_rate_one_time_m']:,.0f}M",
            ha="center", fontsize=9.5, color=INK)
a2.set_title("Savings a year at J&J scale", loc="left", fontsize=11, color=INK)
a2.set_xticks(list(x), names)
a2.set_ylim(0, v.base_rate_run_rate_m.max() * 1.3)
a2.yaxis.set_major_formatter(lambda y, _: f"${y:,.0f}M")
a2.legend(frameon=False, fontsize=8.5, loc="upper left")
for a in (a1, a2):
    a.grid(axis="y", color=GRID, lw=0.8)
    a.spines[["top", "right"]].set_visible(False)
fig.suptitle(f"Small cut, big impact: the conservative tier keeps {v.loc['Conservative', 'share_of_base_value']:.0%} "
             f"of the base-case value with {v.loc['Conservative', 'jnj_suppliers_cut'] / v.loc['Base', 'jnj_suppliers_cut']:.0%} of the cuts",
             x=0.02, ha="left", fontsize=12, color=INK)
fig.text(0.02, 0.005, f"Base savings rates in every tier. {n80} of {len(lev):,} kept Leverage suppliers hold 80% of the spend "
         f"the re-tender applies to.", fontsize=8.5, color=MUTED)
fig.tight_layout(rect=(0, 0.03, 1, 0.93))
fig.savefig(IMG / "value_vs_cuts.png")
pd.set_option("display.width", 220)
print(v.round(2).T)
