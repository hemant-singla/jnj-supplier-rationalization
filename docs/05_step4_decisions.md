# Step 4 — Which suppliers stay and which go?

Every one of the 16,933 real suppliers gets a decision and a reason code (`outputs/step4_supplier_decisions.csv`, also tab `4_Supplier_Decisions` in the outputs workbook).

## 4a — Duplicate detection (the ML piece)

`scripts/04a_duplicates.py` — entity resolution on supplier names:

1. Normalize names (lowercase, strip punctuation and legal suffixes like Inc, LLC, Corp).
2. TF-IDF on character 3–4-grams + cosine nearest neighbours (scikit-learn).
3. A pair is a duplicate if the normalized names match exactly, or cosine similarity ≥ 0.88 and both share the same first word.
4. Chained matches are grouped (union-find); the highest-spend record becomes the master.

**Choosing the threshold:** first chosen from 10 sampled pairs per similarity band (about 6 of 10 were the same company between 0.85 and 0.88; "Supreme Oil" vs "Supreme Enterprise" is not). The threshold favours precision: wrongly merging two companies is worse than missing a duplicate. A larger check of 70 pairs at the chosen threshold is [below](#how-precise-is-the-duplicate-matching).

**Result:** 858 duplicate records in 644 groups, $804M of spend. Many are the identical name registered twice under different supplier codes (CH2M HILL, Telecare, RBF Consulting). All pairs are in `outputs/step4_duplicate_pairs_review.csv` for manual review.

## 4b — Scorecard and rules

`scripts/04b_decisions.py`. **Scorecard (0–100)**, percentile ranks within the supplier's main category: spend in category 30, recency 20, departments served 20, share bought competitively 15, share bought through an existing contract 15.

**Rules**, applied in order — the first match decides:

| Rule | Decision | Reason | Suppliers | Spend, 3 yrs |
| --- | --- | --- | --- | --- |
| R1 | KEEP | Strategic (A-segment) supplier | 327 | $15,319M |
| R2 | KEEP | Supply protection: top-3 active supplier in a Strategic/Bottleneck category, or the only active supplier in any category (sole source) | 375 | $730M |
| R3 | MERGE | Duplicate record: fold into master supplier | 838 | $341M |
| R4 | EXIT | Inactive: no PO in 18+ months | 5,614 | $1,294M |
| R5 | EXIT | One-time vendor: 1 PO in 3 years | 3,210 | $637M |
| R6 | KEEP | Preferred supplier: core 80% of category spend, or top-10% scorecard | 1,781 | $2,418M |
| R7 | KEEP | Small/diverse guardrail: preferred-supplier development program | 2,166 | $567M |
| R8 | CONSOLIDATE | Volume moves to the category's preferred suppliers | 2,622 | $567M |

## Result

- **Suppliers: 16,933 → 4,649 kept.** That's a 73% cut in supplier records, or **59% of the active base** once inactive records (which cost nothing to remove) are excluded. The business case assumed 54%.
- **87% of spend stays with kept suppliers** ($19.0B of $21.9B). Only **$1.2B over 3 years** (~$400M a year) has to be re-routed to preferred suppliers; inactive suppliers' spend has already stopped, and merged duplicates are the same company.
- **Diversity guardrail holds:** kept suppliers retain **96.6% of active small/diverse spend.**
- **Every exit is explainable:** 64% of all decisions are inactive, one-time or duplicate records, the easiest exits to defend.

| Segment | Keep | Consolidate | Exit | Merge |
| --- | --- | --- | --- | --- |
| A Strategic | 327 | 0 | 0 | 0 |
| B Core | 914 | 120 | 396 | 67 |
| C Tail | 3,407 | 2,503 | 8,428 | 771 |

## Does consolidation add supply risk?

Consolidation moves volume onto fewer suppliers, so it raises concentration. `scripts/04c_concentration.py` measures it per category (409 UNSPSC families) on active spend, with duplicate records folded into their master in both views; R5 and R8 spend moves to the kept suppliers in the same category in proportion to their spend.

| Categories where the top supplier holds > 50% of spend | Before | After |
| --- | --- | --- |
| All categories (406 with active spend) | 129 | 136 |
| Strategic | 9 | 9 |
| Leverage | 0 | 0 |
| Bottleneck | 95 | 99 |
| Non-critical | 25 | 28 |
| Categories with a single supplier | 10 | 13 |

- The increase is small and sits in Bottleneck and Non-critical categories; Strategic and Leverage are unchanged. Median top-supplier share goes from 33% to 36%.
- **Ten categories newly cross 50%**, $64M of 3-year spend (0.3% of active spend): [`outputs/step4c_concentration_watchlist.csv`](../outputs/step4c_concentration_watchlist.csv). Each gets the bottleneck template's second-source clause, or keeps its second supplier.
- Most of the concentration was already there: 95 of 180 Bottleneck categories had a dominant supplier before any change. That is the existing risk the bottleneck agreements address.
- **Sole-source suppliers are never cut.** The first version of the rules let one sole supplier (the only active company in a Bottleneck category) be consolidated; the new test caught it, and rule R2 now keeps the only active supplier in any category. That moved one supplier from CONSOLIDATE to KEEP (4,648 → 4,649 kept).

## How precise is the duplicate matching?

`scripts/04d_duplicate_precision.py` draws a fixed random sample (seed 42) of accepted pairs, each judged by hand from both names, the main ZIP code, main category and main buying department. Uncertain pairs count as wrong. Verdicts: [`outputs/step4_duplicate_review_sample.csv`](../outputs/step4_duplicate_review_sample.csv).

| Accepted pairs | In data | Checked | Correct | Precision |
| --- | --- | --- | --- | --- |
| Exact match after normalizing names | 868 | 20 | 20 | 100% |
| Fuzzy match, similarity 0.88–0.99 | 197 | 50 | 39 | 78% (86% if the 4 uncertain pairs are the same company) |
| All accepted pairs, weighted | 1,065 | 70 | 59 | **≈96%** |

The errors are names that share most characters but not the company: "United Rentals" / "United Van Rentals", "J & A Fence" / "J&R Fence", "Thrifty Medical Supply" / "Thrifty Supply". **Change to the process:** exact matches merge automatically; fuzzy matches go to a review queue before the records are merged. Fuzzy pairs touch 188 merged records and $129M of 3-year spend (0.6%), so the headline numbers barely move either way.

## Known limitations

- Public-body filtering misses misspelled names (e.g. "Montana State Unversity", $375K).
- Individual practitioners (e.g. physicians billed by name) are treated like any other supplier; at J&J, professional-services categories would get a separate review.
- The 0.88 threshold misses some true duplicates with typos (e.g. "Wildfire Enviromental" / "Environmental", similarity 0.81).
