# Step 7 — Agreements for retained suppliers

Every kept supplier gets the agreement its Kraljic quadrant calls for (step 3). The agreement type for each supplier is in `outputs/step4_supplier_decisions.csv` (column `agreement_if_kept`).

| Quadrant | Agreement | Template | Kept suppliers | Spend / yr | Share of kept spend |
| --- | --- | --- | --- | --- | --- |
| Strategic | Partnership MOU + supply agreement | [01_MOU_strategic_partnership.md](01_MOU_strategic_partnership.md) | 417 | $1,350M | 21% |
| Leverage | Master supply/services agreement (MSA) with volume-tiered pricing | [02_MSA_term_sheet_leverage.md](02_MSA_term_sheet_leverage.md) | 1,648 | $3,892M | 61% |
| Bottleneck | Long-term supply agreement + second-source plan | [03_supply_agreement_bottleneck.md](03_supply_agreement_bottleneck.md) | 1,061 | $791M | 13% |
| Non-critical | Catalog / purchasing-card terms | [04_catalog_terms_noncritical.md](04_catalog_terms_noncritical.md) | 1,522 | $312M | 5% |
| **Total** | | | **4,648** | **$6,345M** | **100%** |

(California case-study data. At J&J scale, every regulated supplier also keeps its GMP quality agreement, whatever the commercial agreement.)

For the 12,285 suppliers that are not kept, [05_supplier_transition_notice.md](05_supplier_transition_notice.md) has a notice for each decision type: exit (inactive or one-time vendors), consolidate, and merge duplicate records.

## How the templates tie back to the analysis

- **The MSA's price and re-tender clauses** test the business case's critical assumption. To reach the $300M goal, the base case needs at least a **1.15% saving** on kept leverage spend (step 5). The MSA's tier structure and benchmark clause are how that saving is captured and measured.
- **Bottleneck agreements don't consolidate.** Step 5 found small bottleneck suppliers were *cheaper* than the kept ones (median −10%). These agreements secure supply and add a second source rather than squeezing price.
- **The MOU is deliberately non-binding** on price and volume. It records shared intent (joint roadmap, capacity, innovation) and always sits on top of a binding supply agreement.
- **Small and diverse suppliers kept under rule R7** go into the development program referenced in the MSA and catalog terms. That is how 96.6% of active small/diverse spend is retained.

## Important

These are **case-study templates for a student project, not legal advice**. Real agreements need review by counsel and procurement, and they depend on jurisdiction, the category, and regulatory requirements (e.g., FDA GMP quality agreements for pharma and medtech inputs). Placeholders appear as `[BRACKETS]`; `[Buyer]` stands for the buying company (Johnson & Johnson in this case study).
