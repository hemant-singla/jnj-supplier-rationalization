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
