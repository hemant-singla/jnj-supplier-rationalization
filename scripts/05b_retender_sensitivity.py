"""Step 5b · How much of the case rests on the re-tender assumption?

The re-tender saving on kept Leverage suppliers cannot be measured in the data, and it is $280M of the
$414M base case. This script turns it into a testable claim: J&J run-rate savings as a function of the
re-tender rate, with the rate needed to reach the $300M goal (the break-even).

    run-rate(r) = measured savings (price gap + fewer suppliers) + r x kept Leverage spend (J&J scale)

Reads outputs/step5_savings_scenarios.csv and outputs/step5_model_inputs.csv (written by 05_savings.py).
Writes outputs/step5b_retender_sensitivity.csv and docs/images/retender_sensitivity.png.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT, IMG = Path("outputs"), Path("docs/images")
GOAL, JNJ_SPEND = 300.0, 35_000.0
ASSUMED = {"Low": 0.005, "Base": 0.015, "High": 0.03}   # same as 05_savings.py

sc = pd.read_csv(OUT / "step5_savings_scenarios.csv").set_index("scenario")
inp = pd.read_csv(OUT / "step5_model_inputs.csv").set_index("input").value
ca_spend = inp["CA addressable spend per year ($M)"]
kept_lev_jnj = inp["Kept spend per year, Leverage categories ($M)"] * JNJ_SPEND / ca_spend   # $M per year

measured = {s: sc.loc[s, "jnj_price_m"] + sc.loc[s, "jnj_process_m"] for s in sc.index}  # data-backed part
rates = np.round(np.arange(0, 0.0301, 0.0005), 4)
tab = pd.DataFrame({"retender_rate": rates})
for s in ["Low", "Base", "High"]:
    tab[f"run_rate_m_measured_{s.lower()}"] = measured[s] + rates * kept_lev_jnj
tab["meets_goal_base"] = tab.run_rate_m_measured_base >= GOAL
tab.to_csv(OUT / "step5b_retender_sensitivity.csv", index=False)

breakeven = {s: (GOAL - measured[s]) / kept_lev_jnj for s in measured}
summary = pd.DataFrame({
    "measured_savings_m": measured,
    "breakeven_retender_rate": breakeven,
}).reindex(["Low", "Base", "High"])
summary.to_csv(OUT / "step5b_breakeven.csv")

# ---- chart ---------------------------------------------------------------------------------
INK, MUTED, ACCENT, BAND, GRID = "#14213D", "#5F6B7A", "#0F766E", "#CDE6E2", "#E3E6EA"
fig, ax = plt.subplots(figsize=(9, 5.2), dpi=150)
x = rates * 100
ax.fill_between(x, tab.run_rate_m_measured_low, tab.run_rate_m_measured_high, color=BAND, lw=0,
                label="Range of the measured savings (low–high)")
ax.plot(x, tab.run_rate_m_measured_base, color=ACCENT, lw=2.5, label="Base case")
ax.axhline(GOAL, color=INK, lw=1, ls=(0, (5, 4)))
ax.text(0.05, GOAL + 12, r"\$300M goal", color=INK, fontsize=10)
be = breakeven["Base"] * 100
ax.axvline(be, color=INK, lw=1, ls=(0, (2, 3)))
ax.scatter([be], [GOAL], color=INK, zorder=5, s=28)
ax.annotate(f"Break-even {be:.2f}%", (be, GOAL), xytext=(be + 0.12, GOAL - 95), fontsize=10, color=INK,
            arrowprops=dict(arrowstyle="-", color=INK, lw=0.8))
for s, r in ASSUMED.items():
    y = measured["Base"] + r * kept_lev_jnj
    ax.scatter([r * 100], [y], color=ACCENT, edgecolor="white", zorder=6, s=46)
    ax.text(r * 100, y + 22, f"assumed {s.lower()}: {r*100:g}%\n\\${y:,.0f}M", ha="center", fontsize=9, color=MUTED)
ax.set_xlim(0, 3.05)
ax.set_ylim(0, tab.run_rate_m_measured_high.max() * 1.12)
ax.set_xlabel("Re-tender saving on kept Leverage suppliers (% of their spend)")
ax.set_ylabel("J&J run-rate savings ($M per year)")
ax.xaxis.set_major_formatter(lambda v, _: f"{v:g}%")
ax.yaxis.set_major_formatter(lambda v, _: f"${v:,.0f}M")
ax.grid(axis="y", color=GRID, lw=0.8)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title(f"The \\$300M goal needs a re-tender saving of at least {be:.2f}%\n"
             f"Measured savings (price gap + fewer suppliers) = \\${measured['Base']:,.0f}M; "
             f"every 0.1 pt of re-tender adds \\${0.001 * kept_lev_jnj:,.0f}M", loc="left", fontsize=11)
ax.legend(frameon=False, fontsize=9, loc="upper left", bbox_to_anchor=(0, 0.93))
fig.tight_layout()
fig.savefig(IMG / "retender_sensitivity.png")

print(f"Kept Leverage spend at J&J scale: ${kept_lev_jnj:,.0f}M per year")
print(summary.round(4))
