# Methodology: how we figure it out

Ten steps, each with one method, one toolset and one output that feeds the next step.

| # | Step | Method | Tools / technique | Output |
| --- | --- | --- | --- | --- |
| 1 | Set the baseline | Collect public figures; write every assumption down | J&J reports, Excel | Assumptions register |
| 2 | Build the dataset | Synthetic data calibrated to $35B / 29,000 suppliers (Pareto-shaped spend) | Python (pandas, numpy, Faker) | 5 tables in a database |
| 3 | Clean and deduplicate suppliers | Name normalization + fuzzy matching (entity resolution) | rapidfuzz, SQL | Clean supplier master |
| 4 | Classify spend | Map each invoice line to a category (UNSPSC-style) | ML/NLP: TF-IDF + logistic regression, or an LLM classifier | Every dollar tagged |
| 5 | Build the spend cube | Supplier × category × region; Pareto / ABC | SQL (GROUP BY, window functions) | A/B/C segment per supplier |
| 6 | Segment categories | Kraljic matrix: value vs supply risk | Python, scatter plot | Quadrant per category |
| 7 | Score and cluster suppliers | Weighted scorecard (AHP weights) + K-means, PCA | scikit-learn | Score 0–100 + cluster |
| 8 | Predict supplier risk | Classifier for late delivery / quality failure; SHAP | random forest / XGBoost, SHAP | Risk probability |
| 9 | Decide keep vs exit | Rules 1–5 + linear programming (≥2 sources, $3B diversity floor, capacity) | SQL CASE + PuLP | Keep / consolidate / exit list with reason codes |
| 10 | Value it and show it | Savings model + Monte Carlo; dashboard | Python, Power BI / Tableau / Streamlit | Final numbers + dashboard |

## Data model

- `suppliers`: supplier_id, name, country, diverse_flag, small_business_flag, regulated_flag, sole_source_flag
- `spend_transactions`: txn_id, supplier_id, category_id, site, date, amount_usd, line_description
- `categories`: category_id, category_name, kraljic_quadrant, patient_critical_flag
- `scorecards`: supplier_id, on_time_pct, defect_ppm, audit_score, esg_score, financial_risk
- `contracts`: contract_id, supplier_id, type (MOU / MSA / catalog), start, end, payment_terms

## Visualizations

Pareto curve of spend, spend-by-category treemap, Kraljic 2x2, supplier cluster scatter (PCA), risk heatmap by region and category, before/after supplier count, savings waterfall.
