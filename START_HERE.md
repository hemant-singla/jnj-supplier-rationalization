# J&J Supplier Rationalization: start here

Everything for the project lives in this one folder (a copy of the GitHub repo plus the final exports).

## Final deliverables

| What | File / link |
| --- | --- |
| Final presentation (17 slides, incl. 4 dashboard pages) | https://claude.ai/artifact/PMEvigAodrVzwBANkQKpEK (Share › Export to download PPTX or PDF) |
| Business case (final, real-data results) | `docs/JnJ_Business_Case_Final.pdf`, `docs/JnJ_Business_Case_Final.docx` · live: https://claude.ai/artifact/4igvcEzcavrtJf1t9koTqZ |
| Power BI dashboard (open the .pbip in Power BI Desktop) | `powerbi/JnJ_Supplier_Rationalization.pbip` · PDF: `docs/JnJ_Supplier_Dashboard.pdf` |
| All step outputs in one workbook | `outputs/JnJ_Supplier_Rationalization_Outputs.xlsx` |
| Agreement templates (MOU, MSA, supply, catalog, transition notices) | `docs/agreements/` |
| Real J&J suppliers from SEC filings | `docs/07_real_jnj_suppliers.md` |
| GitHub repo | https://github.com/hemant-singla/jnj-supplier-rationalization |

## Folder map

- `docs/` business case, methodology, step write-ups (steps 2–5), agreements, charts, PDFs
- `scripts/` pipeline 01–07 and workbook builders · `sql/` spend cube queries · `model/` step-0 model
- `outputs/` step CSVs and the outputs workbook · `powerbi/` dashboard project + its data file
- `data/` data README and SEC candidate list

## Large files kept outside this folder

- Raw data: `Downloads\purchase-order-data-2012-2015-.csv` (164 MB, data.ca.gov)
- Raw-to-decision trace workbook `JnJ_Data_Raw_to_Decision.xlsx` (100 MB): rebuild with `scripts/build_data_workbook.py`
