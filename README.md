# J&J Supplier Rationalization

A supply chain case study: how Johnson & Johnson could cut its supplier base from ~29,000 to ~13,300 suppliers, justify every exit with data, and put the remaining suppliers on MOUs and tiered agreements.

**Headline (base case):** $385M a year in run-rate savings for $59M one-time cost; 3-year NPV $584M.

> Built on J&J's public reporting plus a synthetic dataset and clearly labeled assumptions. J&J's internal supplier data is not public.

## Goal

Decide which of J&J's ~29,000 suppliers to keep, consolidate or exit, with a data reason behind every exit, and show the result saves at least $300M a year without adding supply risk. Full method: [docs/02_methodology.md](docs/02_methodology.md).

## Project steps

| # | Step | Answers | Method | Tools | Status |
| --- | --- | --- | --- | --- | --- |
| 0 | Business case | Is this worth doing? | Top-down savings model | Python | ✅ [docs/01_business_case.md](docs/01_business_case.md) |
| 1 | Build the dataset | — | Synthetic data calibrated to $35B / 29,000 suppliers | pandas, numpy, Faker | ⬜ Next |
| 2 | Spend cube + Pareto / ABC | Where does the spend sit? | SQL window functions | SQL | ⬜ ([draft query](sql/01_pareto_abc.sql)) |
| 3 | Kraljic matrix | How should each category be handled? | Value vs supply risk 2x2 | Python | ⬜ |
| 4 | Keep / consolidate / exit list | Which suppliers stay and which go? | Duplicate detection (ML) + scorecard + rules 1–5 | rapidfuzz, SQL | ⬜ |
| 5 | Savings model on real list | What is it worth? | Low / base / high scenarios | Python | ⬜ |
| 6 | Dashboard | — | One view per question | Power BI or Tableau | ⬜ |
| 7 | Agreements | — | Template MOU + MSA term sheet | Markdown | ⬜ |

## Repository layout

```
docs/        business case, methodology, agreement templates, chart images
model/       business case financial model
sql/         spend cube and rationalization queries
data/        synthetic dataset (generated, step 1)
notebooks/   analysis notebooks (steps 2–5)
```

## Run the business case model

```bash
python model/business_case_model.py
```

## Progress log

See [CHANGELOG.md](CHANGELOG.md) — one entry per step.
