"""J&J supplier count over time: what our model explains, what the Kenvue spin-off explains, and Phase 2.

Reported J&J supplier counts (each with its source and what it covers):
  80,000   State of Flux case study (undated; after procurement became an enterprise function in 2014)
  50,000+  Procurement Magazine article (undated, later)
  38,500+  2023 Health for Humanity Report
  29,000+  2024 Health for Humanity Report (after Kenvue)
  ~39,000  FY2025 Modern Slavery Statement (new spend-classification method)

The fall from 80,000 is NOT all rationalization: in 2023 J&J separated its consumer health business
(Kenvue IPO May 2023; separation completed 23 Aug 2023), and suppliers went with it. Kenvue does not
publish a supplier count, so its share is an ASSUMPTION, run two ways:
  low  = Consumer Health share of J&J 2022 sales ($14,953M of $94,943M = 15.7%)
  high = 30% (consumer goods lean heavily on packaging, fragrance and contract manufacturers)

Back-test: apply the Phase 1 tiers (step 5) to the J&J base left after Kenvue and compare with ~39,000.
Phase 2: the category target model (step 8) from ~39,000.
Writes outputs/step9_jnj_timeline_backtest.csv and docs/images/jnj_supplier_timeline.png.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

OUT, IMG = Path("outputs"), Path("docs/images")
START, NOW = 80_000, 39_000
KENVUE = {"low": 14_953 / 94_943, "high": 0.30}

tiers = pd.read_csv(OUT / "step5_jnj_supplier_tiers.csv").set_index("tier").reduction
p2 = pd.read_csv(OUT / "step8_phase2_summary.csv").set_index("metric").value
p2s = pd.read_csv(OUT / "step8_phase2_coverage_sensitivity.csv")
phase2_after = p2["J&J suppliers after Phase 2"]

rows = []
for k, share in KENVUE.items():
    base = START * (1 - share)
    own = 1 - NOW / base                                # reduction J&J itself would have made
    rows.append(dict(kenvue_case=k, kenvue_share=share, kenvue_suppliers=round(START * share, -2),
                     jnj_base_after_kenvue=round(base, -2), reported_now=NOW, implied_own_reduction=own,
                     model_conservative=round(base * (1 - tiers["Conservative"]), -2),
                     model_base=round(base * (1 - tiers["Base"]), -2),
                     model_aggressive=round(base * (1 - tiers["Aggressive"]), -2),
                     phase2_from_now=phase2_after,
                     phase2_low=p2s.jnj_after.min(), phase2_high=p2s.jnj_after.max()))
bt = pd.DataFrame(rows)
bt.to_csv(OUT / "step9_jnj_timeline_backtest.csv", index=False)

# ---- chart: the bridge from 80,000 to today and to Phase 2 ---------------------------------
INK, MUTED, ACCENT, KEN, P2, GRID = "#14213D", "#5F6B7A", "#0F766E", "#C2410C", "#6B5FB5", "#E3E6EA"
lo, hi = bt.set_index("kenvue_case").loc["low"], bt.set_index("kenvue_case").loc["high"]
fig, ax = plt.subplots(figsize=(10, 5.4), dpi=150)
x = range(5)
ax.bar(0, START, color="#B8C0CC", width=0.6)
ax.bar(1, START - lo.jnj_base_after_kenvue, bottom=lo.jnj_base_after_kenvue, color=KEN, alpha=0.85, width=0.6)
ax.bar(1, lo.jnj_base_after_kenvue - hi.jnj_base_after_kenvue, bottom=hi.jnj_base_after_kenvue, color=KEN,
       alpha=0.35, width=0.6, hatch="//", edgecolor="white")
ax.bar(2, NOW, color=INK, width=0.6)
ax.vlines(2, hi.model_base, lo.model_conservative, color=ACCENT, lw=7, alpha=0.55)
ax.bar(3, phase2_after, color=P2, width=0.6)
ax.vlines(3, p2s.jnj_after.min(), p2s.jnj_after.max(), color="white", lw=2)
labels = [("80,000", START), (f"−{START - lo.jnj_base_after_kenvue:,.0f} to −{START - hi.jnj_base_after_kenvue:,.0f}", START),
          ("~39,000", NOW), (f"~{phase2_after:,.0f}", phase2_after)]
for i, (t, y) in enumerate(labels):
    ax.text(i, y + 1500, t, ha="center", fontsize=10.5, color=INK, weight="bold")
ax.text(2.33, (hi.model_base + lo.model_conservative) / 2,
        f"Our Phase 1 rules (conservative\nto base) on the post-Kenvue base:\n{hi.model_base:,.0f}–{lo.model_conservative:,.0f}",
        fontsize=9, color=ACCENT, va="center")
ax.annotate(f"J&J's own reduction\non the rest: {hi.implied_own_reduction:.0%}–{lo.implied_own_reduction:.0%}",
            xy=(1.55, (NOW + hi.jnj_base_after_kenvue) / 2), fontsize=9.5, color=INK, ha="right")
ax.annotate("", xy=(1.62, NOW), xytext=(1.62, hi.jnj_base_after_kenvue),
            arrowprops=dict(arrowstyle="->", color=INK, lw=1))
ax.set_xticks([0, 1, 2, 3], ["Reported earlier\n(State of Flux)", "Kenvue spin-off\n2023 (estimate)",
                             "Reported FY2025\n(Modern Slavery Stmt)", "After Phase 2\n(our recommendation)"])
ax.set_xlim(-0.5, 3.9)
ax.set_ylim(0, START * 1.12)
ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}")
ax.set_ylabel("J&J suppliers")
ax.grid(axis="y", color=GRID, lw=0.8)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("J&J's own drop from 80,000 is consistent with our rules once Kenvue is taken out\n"
             f"Kenvue share: {KENVUE['low']:.0%} (sales) to {KENVUE['high']:.0%} (assumed); "
             f"Phase 2 range {p2s.jnj_after.min():,.0f}–{p2s.jnj_after.max():,.0f} by coverage target",
             loc="left", fontsize=11)
fig.tight_layout()
fig.savefig(IMG / "jnj_supplier_timeline.png")
pd.set_option("display.width", 220)
print(bt.round(3).T)
