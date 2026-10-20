# Progress log

## 2026-10-20 — Step 0: Business case
- Gathered J&J public procurement figures (29,000 suppliers in 2024; ~$35B addressable spend).
- Built top-down savings model (`model/business_case_model.py`): segments, exits, savings, one-time cost, NPV, low/base/high scenarios.
- Wrote the business case (`docs/01_business_case.md`) with savings bridge and roadmap.
- Defined the 10-step methodology and data model (`docs/02_methodology.md`).
- Drafted the Pareto / ABC segmentation query (`sql/01_pareto_abc.sql`).

## 2026-10-20 — Focused the goal and methods
- Set one goal: keep / consolidate / exit decision per supplier, ≥ $300M a year, no added supply risk.
- Cut the method set to four decision questions, one method each (Pareto/ABC, Kraljic, duplicate detection + scorecard + rules, savings scenarios).
- Kept one ML piece (fuzzy duplicate matching) and one dashboard; documented the methods left out and why.

## 2026-10-20 — Switched to real data
- Replaced the synthetic-data plan with real public procurement data (State of California purchase orders, FY2012–15) plus real J&J suppliers from SEC filings.

## 2026-10-20 — Step 1: Load and clean real data
- `scripts/01_clean_load.py`: cleaned 344,504 lines into SQLite; kept $21.9B addressable spend across 16,933 suppliers.
- Excluded $128.8B of non-addressable spend (procurement-exempt methods, public bodies, Medi-Cal health plans), each line kept with a reason code.
- First finding: top 1.9% of suppliers = 70% of spend, top 10.8% = 92% — matches the business case segment assumptions.
- Started list of candidate real J&J suppliers from SEC full-text search.

## 2026-10-20 — Step 2: Spend cube + Pareto / ABC
- `sql/01_pareto_abc.sql`, `sql/02_category_fragmentation.sql`, `scripts/02_spend_cube.py`; write-up in `docs/03_step2_spend_cube.md`.
- A: 327 suppliers (1.9%) = 70% of spend; B: 1,497 (8.8%) = 22%; C: 15,109 (89.2%) = 8%.
- 59% of tail suppliers are inactive (18+ months) or one-time — matches the business case's 60% tail-cut assumption.
- Most fragmented categories: refuse disposal, measuring instruments, batteries/generators, material handling.
