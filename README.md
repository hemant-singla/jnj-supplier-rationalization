# J&J Supplier Rationalization

A supply chain case study: how Johnson & Johnson could cut its active supplier base by more than half (~29,000 today), justify every exit with data, and put the remaining suppliers on MOUs and tiered agreements.

**Headline (base case, on the real supplier list):** $366M a year in run-rate savings for $40M one-time cost; 3-year NPV $572M. Only $86M of it is measured in the data; reaching the $300M goal needs a ≥1.15% re-tender saving on kept leverage suppliers.

> J&J does not publish supplier-level data, so the methods run on **real public procurement data** (State of California purchase orders FY2012–15: 344,504 lines, 16,933 addressable suppliers) and the results are scaled to J&J's published totals. Every assumption is labeled.

## Goal

Decide which of J&J's ~29,000 suppliers to keep, consolidate or exit, with a data reason behind every exit, and show the result saves at least $300M a year without adding supply risk. Full method: [docs/02_methodology.md](docs/02_methodology.md).

## Project steps

| # | Step | Answers | Method | Tools | Status |
| --- | --- | --- | --- | --- | --- |
| 0 | Business case | Is this worth doing? | Top-down savings model | Python | ✅ [docs/01_business_case.md](docs/01_business_case.md) |
| 1 | Load real data | — | Clean California purchase orders, addressable-spend rules | pandas, SQLite | ✅ [data/README.md](data/README.md) |
| 2 | Spend cube + Pareto / ABC | Where does the spend sit? | SQL window functions | SQL | ✅ [docs/03_step2_spend_cube.md](docs/03_step2_spend_cube.md) |
| 3 | Kraljic matrix | How should each category be handled? | Value vs supply risk 2x2 | Python | ✅ [docs/04_step3_kraljic.md](docs/04_step3_kraljic.md) |
| 4 | Keep / consolidate / exit list | Which suppliers stay and which go? | Duplicate detection (ML) + scorecard + rules | scikit-learn, SQL | ✅ [docs/05_step4_decisions.md](docs/05_step4_decisions.md) |
| 5 | Savings model on real list | What is it worth? | Measured price gap + low / base / high scenarios | Python | ✅ [docs/06_step5_savings.md](docs/06_step5_savings.md) |
| 6 | Dashboard | — | 4-page Power BI report (star schema, 21 DAX measures) | Power BI | ✅ [powerbi/](powerbi/README.md) |
| 6b | Real J&J suppliers | Who are J&J's strategic suppliers? | SEC 10-K full-text search, filings read | EDGAR | ✅ [docs/07_real_jnj_suppliers.md](docs/07_real_jnj_suppliers.md) |
| 7 | Agreements | — | MOU, MSA, bottleneck supply and catalog terms + transition notices | Markdown | ✅ [docs/agreements/](docs/agreements/README.md) |

## All outputs in one file

[`outputs/JnJ_Supplier_Rationalization_Outputs.xlsx`](outputs/JnJ_Supplier_Rationalization_Outputs.xlsx): one tab per completed step.

## Repository layout

```
docs/        business case, methodology, agreement templates, chart images
model/       business case financial model
powerbi/     Power BI dashboard project (.pbip) + its data file
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

## Status (paused 2026-10-21)

**Done:** steps 0–7: business case, real-data cleaning, spend cube, Kraljic, keep/consolidate/exit list, savings model, Power BI dashboard, agreement templates.

**Open items when resuming:**
1. Add the dashboard PDF export (`docs/JnJ_Supplier_Dashboard.pdf`).
2. ~~Verify the candidate real J&J suppliers from SEC filings~~ ✅ done 2026-10-22: [docs/07_real_jnj_suppliers.md](docs/07_real_jnj_suppliers.md)
3. Final presentation deck (problem → method → findings → recommendation → roadmap), reusing the charts and the `Files_and_Sources` list.
4. Update the business case doc with the real-data results (base $366M/yr; $86M measured; ≥ 1.15% re-tender hurdle).

**To rebuild locally:** download the California CSV (see `data/README.md`), then run `scripts/01_clean_load.py` → `02_spend_cube.py` → `03_kraljic.py` → `04a_duplicates.py` → `04b_decisions.py` → `05_savings.py` → `build_outputs_workbook.py` → `06_powerbi_data.py` → `07_build_pbip.py`.
