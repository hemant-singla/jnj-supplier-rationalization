# Step 2 — Where does the spend sit? (Spend cube + Pareto / ABC)

**Method:** SQL window functions rank all 16,933 suppliers by 3-year addressable spend and cut them at 70% and 92% of cumulative spend (`sql/01_pareto_abc.sql`). A category cube shows where the supplier base is most fragmented (`sql/02_category_fragmentation.sql`). Run with `python scripts/02_spend_cube.py`.

## Result

| Segment | Suppliers | % of suppliers | Spend | % of spend | Inactive 18+ months | One-time (1 PO in 3 yrs) | Small / diverse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A Strategic | 327 | 1.9% | $15.32B | 70.0% | 60 | 59 | 88 |
| B Core | 1,497 | 8.8% | $4.80B | 22.0% | 279 | 320 | 659 |
| C Tail | 15,109 | 89.2% | $1.75B | 8.0% | 5,616 | 7,341 | 5,570 |

## What it means

1. **The business case segment assumptions hold on real data.** Assumed: 2% of suppliers = 70% of spend, 15% = 92%. Real: 1.9% = 70%, 10.7% = 92%.
2. **59% of tail suppliers are already "dead weight":** 8,908 of 15,109 tail suppliers had no PO in the last 18 months or only one PO in three years. They hold just $707M (3% of spend). The business case assumed a 60% tail cut.
3. **The diversity guardrail matters:** 2,723 of those 8,908 are small or diverse businesses. Rule 3 routes them to preferred-supplier programs instead of simply dropping them.
4. **Fragmentation is worst in low-value, commodity categories.** Refuse disposal: 1,070 suppliers for $103M (47% of it with tail suppliers). Measuring and testing instruments: 781 suppliers for $49M. Batteries and generators: 541 suppliers for $34M. These are the first consolidation targets.

Output tables: `outputs/step2_*.csv`.
