# Goal and method

**Goal:** decide which of J&J's suppliers (80,000 reported earlier, ~39,000 today) to keep, consolidate or exit, with a data reason behind every exit, and show whether the result can save at least $300M a year, with any added supply risk measured (concentration before vs after) and covered by an agreement.

We answer four questions, one method each. Each answer feeds the next; together they produce the exit list and the business case numbers.

| # | Decision question | Method | Tool | Output |
| --- | --- | --- | --- | --- |
| 1 | Where does the spend sit? | Spend cube + Pareto / ABC analysis | SQL | A / B / C segment per supplier |
| 2 | How should each category be handled? | Kraljic matrix (value vs supply risk) | Python | Quadrant per category, which sets the agreement type |
| 3 | Which suppliers stay and which go? | Duplicate detection + weighted scorecard + rules 1–5 | Python (rapidfuzz), SQL | Keep / consolidate / exit list, one reason code per supplier |
| 4 | What is it worth? | Savings model, low / base / high scenarios | Python | Savings, one-time cost, NPV |

**The one AI/ML piece:** fuzzy name matching to find duplicate suppliers (for example "Acme Lab Supply Inc" and "ACME Laboratory Supplies"). Duplicates are the easiest exits to justify, so this is where ML directly supports the recommendation.

**One dashboard** (Power BI or Tableau), one view per question: Pareto curve, Kraljic 2x2, exit list by reason code, savings bridge.

## Deliberately left out

None of these would change the recommendation:

| Method | Why it is out |
| --- | --- |
| NLP spend classification | Our synthetic data is already categorized; it solves a real-data problem we don't have |
| Supplier risk prediction (random forest, XGBoost) | Needs real failure history; on synthetic data it would only learn our own assumptions |
| K-means clustering | The scorecard and Kraljic matrix already group suppliers in ways a reader can explain |
| Linear programming optimization | Rules 1–5 already encode the constraints; an optimizer adds complexity, not a different list |
| Monte Carlo simulation | Three scenarios show the range clearly enough |

## Data needed

Five tables, generated synthetically and calibrated to J&J's public totals:

- `suppliers`: supplier_id, name, country, diverse_flag, small_business_flag, regulated_flag, sole_source_flag
- `spend_transactions`: txn_id, supplier_id, category_id, site, date, amount_usd
- `categories`: category_id, category_name, kraljic_quadrant, patient_critical_flag
- `scorecards`: supplier_id, on_time_pct, defect_ppm, audit_score, esg_score, financial_risk
- `contracts`: contract_id, supplier_id, type (MOU / MSA / catalog), start, end, payment_terms
