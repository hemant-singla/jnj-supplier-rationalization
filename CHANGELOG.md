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

## 2026-10-20 — Step 3: Kraljic matrix
- `scripts/03_kraljic.py`; write-up in `docs/04_step3_kraljic.md`; chart `docs/images/kraljic_matrix.png`.
- Value = category spend (top categories = 80% of spend); risk = non-competitive share + top-3 concentration + thin supply base, ranked within size bands.
- Leverage 59% of spend (20 categories), Strategic 21% (21), Bottleneck 13% (183), Non-critical 7% (185, but 21,991 supplier relationships).
- Fixed a first-pass bias where small categories scored high-risk just for having few suppliers.

## 2026-10-20 — Outputs workbook
- `scripts/build_outputs_workbook.py` → `outputs/JnJ_Supplier_Rationalization_Outputs.xlsx`: one tab per completed step (business case with live formulas, cleaning, segments, fragmented categories, full 16,933-supplier list, Kraljic).
- Corrected excluded-line counts in `data/README.md` (44,341 / 15,276 / 6,255; they sum with the 278,632 kept lines to 344,504).

## 2026-10-20 — Step 4: Keep / consolidate / exit list
- `scripts/04a_duplicates.py`: TF-IDF character n-gram duplicate detection (threshold 0.88 chosen from sampled pairs) → 858 duplicate records in 644 groups.
- `scripts/04b_decisions.py`: scorecard + rules R1–R8 → decision and reason code for all 16,933 suppliers.
- 4,648 kept (−73% of records, −59% of active base); $1.2B over 3 years to re-route; 96.6% of active small/diverse spend retained.
- Workbook gains tabs `4_Decision_Summary` and `4_Supplier_Decisions`; write-up in `docs/05_step4_decisions.md`.

## 2026-10-20 — Full data traceability
- `scripts/01_clean_load.py` now records the outcome of every raw row (`raw_line_status` table).
- `scripts/build_data_workbook.py` → `JnJ_Data_Raw_to_Decision.xlsx`: all 344,504 raw rows exactly as downloaded, plus trace columns (step 1 status / reason / parsed amount, step 2 segment, step 3 quadrant, step 4 decision / rule), a cleaning-steps tab and the top 100 excluded payees. 100 MB, so shared outside git; rebuild with the script.
- Outputs workbook gains `Files_and_Sources` (every data source, script, SQL file and output with links) and `SQL_Code` tabs.

## 2026-10-21 — Step 5: Savings on the real list
- `scripts/05_savings.py`; write-up `docs/06_step5_savings.md`; chart `docs/images/savings_bridge_real.png`; workbook tab `5_Savings_Real_List` with live formulas.
- Price-gap test (127 goods items bought from both kept and exiting suppliers): exiting suppliers dearer by 9.8% in Leverage and 5.2% in Non-critical categories, but cheaper in Bottleneck (−10%) and Strategic (−7%).
- First pass mixed in services (unit = whole project) and was discarded; goods only.
- J&J base case $366M/yr (low $105M, high $721M), one-time $40M, NPV $572M. Only $86M/yr is measured in the data; goal of $300M needs ≥1.15% re-tender saving on kept leverage spend.
- Fixed: process savings scale with supplier count, not spend.

## 2026-10-21 — Step 6: Power BI dashboard
- `scripts/06_powerbi_data.py` → `JnJ_PowerBI_Data.xlsx` (9 tables incl. Quadrants dimension and sort-order columns).
- `scripts/07_build_pbip.py` generates the Power BI project (TMDL model: 9 tables, 6 relationships, 21 DAX measures; PBIR report: 4 pages, 38 visuals) using the file format saved by the user's Power BI Desktop.
- Pages: Executive Summary, Category Strategy (log-scale Kraljic), Savings Case (scenarios vs $300M goal, price-gap evidence), Supplier Explorer.
- Opened, refreshed and checked in Power BI Desktop; fixed log axis property (`logAxisScale`), removed auto subtitles, removed meaningless totals.
- Saved project committed under `powerbi/`.

## 2026-10-21 — Step 7: Agreements for retained suppliers
- `docs/agreements/`: strategic partnership MOU (417 suppliers), leverage MSA term sheet with volume tiers and benchmark clause (1,648), bottleneck long-term supply agreement with second-source plan (1,061), catalog / purchasing-card terms (1,522).
- Transition notices for the 12,285 suppliers not kept: closure (R4, R5), consolidation (R8), duplicate merge (R3).
- MSA clauses tied to the step 5 hurdle (≥ 1.15% re-tender saving) and tracked against the price-gap baseline.

## 2026-10-22 — Real J&J suppliers verified (SEC filings)
- Read the 10-K of each of 9 candidates to confirm the direction of the relationship; write-up `docs/07_real_jnj_suppliers.md`.
- Confirmed suppliers: Alkermes (exclusive RISPERDAL CONSTA manufacturer), MeiraGTx (RPGR gene therapy, 4+1-year supply agreement), Mersana (clinical ADC manufacturing, tech-transfer clause), Emergent (former COVID-19 vaccine CDMO, ended 2022 over GMP breaches, settled 2024 for $50M).
- Legend is a collaboration partner; ORIC and Coherus are reverse-direction (J&J supplies them); XBiotech and Viscogliosi unconfirmed.

## 2026-10-22 — Project closed out
- Business case doc updated with the real-data results: new executive summary, "What the real data shows", verified J&J suppliers, real-data savings model and chart ($366M base, $86M measured, ≥1.15% re-tender hurdle), agreement counts, deliverables, KPI targets.
- Final 13-slide presentation built (problem → method → findings → recommendation → roadmap → sources).
- Power BI dashboard PDF export added: `docs/JnJ_Supplier_Dashboard.pdf` (4 pages).
- README: final deliverables table, corrected repo layout, status set to complete.

## 2026-10-22 — Checks on the conclusion
- **Re-tender sensitivity** (`scripts/05b_retender_sensitivity.py`, chart `docs/images/retender_sensitivity.png`): savings vs re-tender rate; the $300M goal needs 1.15% in the base case (0.75–1.54% across the measured range); +$19M a year per 0.1 point.
- **Concentration before vs after** (`scripts/04c_concentration.py`): categories with a >50% top supplier go from 129 to 136 of 406 (Strategic 9 → 9, Leverage 0 → 0); 10 categories newly cross 50% ($64M over 3 years) and form a second-source watch-list.
- **Sole-source rule fix:** the new test found one sole supplier in a Bottleneck category marked CONSOLIDATE; rule R2 now keeps the only active supplier in any category (kept 4,648 → 4,649; R8 2,623 → 2,622; MSA suppliers 1,648 → 1,649). Savings unchanged at the reported precision.
- **Duplicate precision** (`scripts/04d_duplicate_precision.py`): 70 accepted pairs judged by hand: exact matches 20/20, fuzzy matches 39/50 (78%), ≈96% overall; fuzzy matches now go to a review queue before merging.
- **"What carries over and what doesn't"** section in the README: the method transfers to J&J, the exact percentages don't.
- **Tests** (`tests/`): no strategic or sole-source exits, a reason code on every supplier and raw row, totals reconcile raw → decisions, savings add up and the break-even reproduces. 18 tests pass.
- Repo cleanup: README and docs link to PDFs only; removed START_HERE.md and the empty notebooks folder; added requirements.txt; outputs workbook gains tabs 4_Concentration, 4_Duplicate_Check, 5b_Retender_Sensitivity.
