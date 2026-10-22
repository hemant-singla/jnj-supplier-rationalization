# Power BI dashboard

`JnJ_Supplier_Dashboard/JnJ_Supplier_Rationalization.pbip` is a Power BI project (PBIP: TMDL semantic model + PBIR report). It's version-control friendly, and every visual is a readable JSON file.

| Page | Answers |
| --- | --- |
| 1 Executive Summary | 16,933 → 4,648 suppliers, spend retained, diversity guardrail, decision by rule, Pareto curve |
| 2 Category Strategy | Kraljic matrix of 409 categories (log scale), quadrant summary, most fragmented categories |
| 3 Savings Case | $366M base run-rate vs $300M goal, measured vs assumed savings, price-gap evidence |
| 4 Supplier Explorer | Decision and reason code for every supplier, with slicers |

## Open it

1. The model reads `JnJ_PowerBI_Data.xlsx` from this `powerbi` folder at `C:\Users\SAMSUNG\Downloads\JnJ_Supplier_Rationalization_Project\powerbi\`. On another computer, edit the file path in the `partition` block of each table under `JnJ_Supplier_Dashboard/JnJ_Supplier_Rationalization.SemanticModel/definition/tables/*.tmdl`).
2. Open `JnJ_Supplier_Rationalization.pbip` in Power BI Desktop and click **Refresh**.

## Rebuild from scratch

```bash
python scripts/06_powerbi_data.py   # data file
python scripts/07_build_pbip.py     # project files (model, measures, 4 pages, 38 visuals)
```

The model has 9 tables, 6 relationships (star schema around a Quadrants dimension) and 21 DAX measures.
