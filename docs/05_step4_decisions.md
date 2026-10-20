# Step 4 — Which suppliers stay and which go?

Every one of the 16,933 real suppliers gets a decision and a reason code (`outputs/step4_supplier_decisions.csv`, also tab `4_Supplier_Decisions` in the outputs workbook).

## 4a — Duplicate detection (the ML piece)

`scripts/04a_duplicates.py` — entity resolution on supplier names:

1. Normalize names (lowercase, strip punctuation and legal suffixes like Inc, LLC, Corp).
2. TF-IDF on character 3–4-grams + cosine nearest neighbours (scikit-learn).
3. A pair is a duplicate if the normalized names match exactly, or cosine similarity ≥ 0.88 and both share the same first word.
4. Chained matches are grouped (union-find); the highest-spend record becomes the master.

**Choosing the threshold:** sampled pairs by similarity band. At ≥ 0.88, 10 of 10 sampled pairs were the same company ("Dell Marketing L.P" / "DELL MARKETING LP", "Hewlett Packard IPG" / "Hewlett-Packard Company"). Between 0.85 and 0.88, about 6 of 10 were ("Supreme Oil" vs "Supreme Enterprise" is not). The threshold favours precision: wrongly merging two companies is worse than missing a duplicate.

**Result:** 858 duplicate records in 644 groups, $804M of spend. Many are the identical name registered twice under different supplier codes (CH2M HILL, Telecare, RBF Consulting). All pairs are in `outputs/step4_duplicate_pairs_review.csv` for manual review.

## 4b — Scorecard and rules

`scripts/04b_decisions.py`. **Scorecard (0–100)**, percentile ranks within the supplier's main category: spend in category 30, recency 20, departments served 20, share bought competitively 15, share bought through an existing contract 15.

**Rules**, applied in order — the first match decides:

| Rule | Decision | Reason | Suppliers | Spend, 3 yrs |
| --- | --- | --- | --- | --- |
| R1 | KEEP | Strategic (A-segment) supplier | 327 | $15,319M |
| R2 | KEEP | Supply protection: top-3 active supplier in a Strategic/Bottleneck category | 369 | $720M |
| R3 | MERGE | Duplicate record: fold into master supplier | 838 | $341M |
| R4 | EXIT | Inactive: no PO in 18+ months | 5,614 | $1,294M |
| R5 | EXIT | One-time vendor: 1 PO in 3 years | 3,210 | $637M |
| R6 | KEEP | Preferred supplier: core 80% of category spend, or top-10% scorecard | 1,785 | $2,428M |
| R7 | KEEP | Small/diverse guardrail: preferred-supplier development program | 2,167 | $567M |
| R8 | CONSOLIDATE | Volume moves to the category's preferred suppliers | 2,623 | $567M |

## Result

- **Suppliers: 16,933 → 4,648 kept.** That's a 73% cut in supplier records, or **59% of the active base** once inactive records (which cost nothing to remove) are excluded. The business case assumed 54%.
- **87% of spend stays with kept suppliers** ($19.0B of $21.9B). Only **$1.2B over 3 years** (~$400M a year) has to be re-routed to preferred suppliers; inactive suppliers' spend has already stopped, and merged duplicates are the same company.
- **Diversity guardrail holds:** kept suppliers retain **96.6% of active small/diverse spend.**
- **Every exit is explainable:** 64% of all decisions are inactive, one-time or duplicate records, the easiest exits to defend.

| Segment | Keep | Consolidate | Exit | Merge |
| --- | --- | --- | --- | --- |
| A Strategic | 327 | 0 | 0 | 0 |
| B Core | 914 | 120 | 396 | 67 |
| C Tail | 3,407 | 2,503 | 8,428 | 771 |

## Known limitations

- Public-body filtering misses misspelled names (e.g. "Montana State Unversity", $375K).
- Individual practitioners (e.g. physicians billed by name) are treated like any other supplier; at J&J, professional-services categories would get a separate review.
- The 0.88 threshold misses some true duplicates with typos (e.g. "Wildfire Enviromental" / "Environmental", similarity 0.81).
