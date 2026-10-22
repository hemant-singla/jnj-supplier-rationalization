# J&J Supplier Rationalization: start here

Everything for the project lives in this one folder (a copy of the GitHub repo plus the final exports).

## Final deliverables

| What | File / link |
| --- | --- |
| Final presentation (17 slides, incl. 4 dashboard pages) | `JnJ_Supplier_Rationalization_Deck.pdf` / `.pptx` in this folder · live: https://claude.ai/artifact/PMEvigAodrVzwBANkQKpEK |
| Business case (final, real-data results) | `docs/JnJ_Business_Case_Final.pdf`, `docs/JnJ_Business_Case_Final.docx` · live: https://claude.ai/artifact/4igvcEzcavrtJf1t9koTqZ |
| Power BI dashboard (open the .pbip in Power BI Desktop) | `powerbi/JnJ_Supplier_Dashboard/JnJ_Supplier_Rationalization.pbip` · PDF: `docs/JnJ_Supplier_Dashboard.pdf` |
| All step outputs in one workbook | `outputs/JnJ_Supplier_Rationalization_Outputs.xlsx` |
| Agreement templates (MOU, MSA, supply, catalog, transition notices) | `docs/agreements/` |
| Real J&J suppliers from SEC filings | `docs/07_real_jnj_suppliers.md` |
| GitHub repo | https://github.com/hemant-singla/jnj-supplier-rationalization |

## Folder map

- `docs/` business case, methodology, step write-ups (steps 2–5), agreements, charts, PDFs
- `scripts/` pipeline 01–07 and workbook builders · `sql/` spend cube queries · `model/` step-0 model
- `outputs/` step CSVs and the outputs workbook · `powerbi/` dashboard project + its data file
- `data/` data README and SEC candidate list

## Raw data and full trace

- `data/raw/purchase-order-data-2012-2015-.csv`: the raw California file exactly as downloaded (164 MB, not in GitHub)
- `outputs/JnJ_Data_Raw_to_Decision_part1of5.xlsx` … `part5of5.xlsx`: all 344,504 raw rows traced through every step, split into 5 workbooks (part 1 also has README, Cleaning_Steps, Excluded_Payees). Rebuild: `python scripts/build_data_workbook.py data/raw/purchase-order-data-2012-2015-.csv 5`
- The Power BI dashboard reads `powerbi/JnJ_PowerBI_Data.xlsx` in this folder, so the folder is self-contained.
