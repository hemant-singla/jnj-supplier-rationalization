# Data

**Source:** State of California, Department of General Services — *Purchase Order Data, FY2012-13 to FY2014-15*
([data.gov](https://catalog.data.gov/dataset/purchase-order-data), public, no use restrictions). Real purchase orders over $5,000 with supplier names, amounts and UNSPSC categories.

**Why this dataset:** J&J does not publish supplier-level data. This is real procurement data with a supplier base of similar size (16,933 addressable suppliers vs J&J's ~29,000), so the methods run on real transactions; results are then scaled to J&J's published totals.

## Rebuild

1. Download the CSV (157 MB) from the link above into `data/raw/`.
2. `python scripts/01_clean_load.py data/raw/purchase-order-data-2012-2015-.csv` → creates `data/procurement.db` (SQLite).

## Cleaning result (step 1)

| | Lines | Spend |
| --- | --- | --- |
| Raw file | 344,504 | $150.7B |
| Excluded: procurement-exempt methods | 44,341 | $60.7B |
| Excluded: public bodies and health plans (pass-through funds) | 15,276 | $68.1B |
| Excluded: missing or zero amount | 6,255 | $0 |
| **Addressable** | **278,632** | **$21.9B** (3 years) |

Addressable suppliers: 16,933 supplier codes / 16,567 distinct names.

## Tables in `procurement.db`

- `spend_lines` — addressable purchase lines (date, fiscal year, PO, department, supplier code/name, small-business qualifications, item, amount, UNSPSC segment/family/class)
- `excluded_lines` — every dropped line with its exclusion reason, for audit

`raw/jnj_supplier_candidates_sec.md` — candidate real J&J suppliers from SEC filings (being verified).
