# J&J Supplier Rationalization

A supply chain case study: how Johnson & Johnson could cut its supplier base from ~29,000 to ~13,300 suppliers, justify every exit with data, and put the remaining suppliers on MOUs and tiered agreements.

**Headline (base case):** $385M a year in run-rate savings for $59M one-time cost; 3-year NPV $584M.

> Built on J&J's public reporting plus a synthetic dataset and clearly labeled assumptions. J&J's internal supplier data is not public.

## Project steps

| # | Step | Method | Tools | Status |
| --- | --- | --- | --- | --- |
| 0 | Business case | Top-down savings model, scenarios, NPV | Python | ✅ Done — [docs/01_business_case.md](docs/01_business_case.md) |
| 1 | Set the baseline | Public figures + assumptions register | J&J reports, Excel | ✅ Done (in business case) |
| 2 | Build the dataset | Synthetic data calibrated to $35B / 29,000 suppliers | pandas, numpy, Faker | ⬜ Next |
| 3 | Clean and deduplicate suppliers | Name normalization, fuzzy matching | rapidfuzz, SQL | ⬜ |
| 4 | Classify spend | Invoice line → category | TF-IDF + logistic regression / LLM | ⬜ |
| 5 | Build the spend cube | Pareto / ABC segmentation | SQL window functions | ⬜ ([draft query](sql/01_pareto_abc.sql)) |
| 6 | Segment categories | Kraljic matrix | Python, scatter plot | ⬜ |
| 7 | Score and cluster suppliers | Weighted scorecard (AHP) + K-means, PCA | scikit-learn | ⬜ |
| 8 | Predict supplier risk | Random forest / XGBoost + SHAP | scikit-learn, xgboost, shap | ⬜ |
| 9 | Decide keep vs exit | Rules + linear programming | SQL, PuLP | ⬜ |
| 10 | Value it and show it | Monte Carlo + dashboard | Python, Power BI / Tableau / Streamlit | ⬜ |
| 11 | Agreements | Template MOU and MSA term sheet | Markdown / Word | ⬜ |

## Repository layout

```
docs/        business case, methodology, agreement templates, chart images
model/       business case financial model
sql/         spend cube and rationalization queries
data/        synthetic dataset (generated, step 2)
notebooks/   analysis and ML notebooks (steps 3–10)
```

## Run the business case model

```bash
python model/business_case_model.py
```

## Progress log

See [CHANGELOG.md](CHANGELOG.md) — one entry per step.
