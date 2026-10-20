"""Build outputs/JnJ_Supplier_Rationalization_Outputs.xlsx — one tab per completed step."""
import sqlite3
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

OUT = Path("outputs/JnJ_Supplier_Rationalization_Outputs.xlsx")
F = "Arial"
BLUE, BLACK, GREEN = "0000FF", "000000", "008000"
HDR_FILL = PatternFill("solid", fgColor="1F3864")
KEY_FILL = PatternFill("solid", fgColor="FFFF00")
THIN = Border(bottom=Side(style="thin", color="BFBFBF"))
USD_M = '$#,##0.0;($#,##0.0);"-"'
USD = '$#,##0;($#,##0);"-"'
PCT = '0.0%;(0.0%);"-"'
NUM = '#,##0;(#,##0);"-"'

wb = Workbook()


def font(color=BLACK, bold=False, size=10, italic=False):
    return Font(name=F, color=color, bold=bold, size=size, italic=italic)


def title(ws, text, sub=None):
    ws["A1"] = text
    ws["A1"].font = font(bold=True, size=14)
    if sub:
        ws["A2"] = sub
        ws["A2"].font = font(italic=True, color="595959")


def header(ws, row, cols, start_col=1):
    for i, c in enumerate(cols):
        cell = ws.cell(row=row, column=start_col + i, value=c)
        cell.font = Font(name=F, bold=True, color="FFFFFF", size=10)
        cell.fill = HDR_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="center")


def write_df(ws, df, row, fmts=None, start_col=1):
    """Write a DataFrame with a header row; fmts maps column name -> number format."""
    header(ws, row, list(df.columns), start_col)
    for r, rec in enumerate(df.itertuples(index=False), start=row + 1):
        for c, v in enumerate(rec, start=start_col):
            cell = ws.cell(row=r, column=c, value=None if pd.isna(v) else v)
            cell.font = font()
            col = df.columns[c - start_col]
            if fmts and col in fmts:
                cell.number_format = fmts[col]
    return row + len(df)


def widths(ws, w):
    for i, x in enumerate(w, start=1):
        ws.column_dimensions[get_column_letter(i)].width = x


# ---------------------------------------------------------------- README
ws = wb.active
ws.title = "README"
title(ws, "J&J Supplier Rationalization — outputs by step",
      "Real data: State of California purchase orders FY2012-15 (data.gov); J&J figures from J&J's public reports")
rows = [
    ("Tab", "Step", "Question it answers", "Method"),
    ("Files_and_Sources", "All", "Where every number comes from", "Data sources, code, SQL, outputs with links"),
    ("0_Business_Case", "0 Business case", "Is this worth doing for J&J?", "Top-down savings model with live formulas"),
    ("1_Data_Cleaning", "1 Load real data", "What spend is addressable?", "Exclusion rules with reason codes"),
    ("2_Segments", "2 Spend cube + Pareto/ABC", "Where does the spend sit?", "SQL window functions"),
    ("2_Fragmented_Categories", "2 Spend cube", "Which categories have too many suppliers?", "SQL category cube"),
    ("2_Supplier_List", "2 Spend cube", "Segment of every supplier", "SQL (16,933 rows)"),
    ("3_Kraljic", "3 Kraljic matrix", "How should each category be handled?", "Value vs supply-risk scoring"),
    ("4_Decision_Summary", "4 Keep / consolidate / exit", "Which suppliers stay and which go?", "Duplicate detection (ML) + scorecard + rules"),
    ("4_Supplier_Decisions", "4 Keep / consolidate / exit", "Decision and reason for every supplier", "16,933 rows, filterable"),
    ("SQL_Code", "2", "The SQL behind the segmentation", "Full query text"),
]
for r, rec in enumerate(rows, start=4):
    for c, v in enumerate(rec, start=1):
        ws.cell(row=r, column=c, value=v).font = font(bold=(r == 4))
header(ws, 4, list(rows[0]))
ws["A16"] = "Colour code: blue = input you can change; black = formula; yellow fill = key assumption."
ws["A16"].font = font(italic=True)
widths(ws, [26, 26, 40, 44])

# ---------------------------------------------------------------- Step 0
ws = wb.create_sheet("0_Business_Case")
title(ws, "Step 0 — Business case (J&J, base year)",
      "Inputs in blue drive every number below. $ in millions unless stated.")
inputs = [
    ("Addressable spend ($M)", 35000, USD, "J&J careers posting: ~$35B across ~35,000 suppliers"),
    ("Active suppliers", 29000, NUM, "J&J 2024 Health for Humanity Report: 29,000+ suppliers"),
    ("Annual cost to maintain one supplier ($M)", 0.002, '$#,##0.000', "Assumption: $2,000 per supplier per year"),
    ("Program team + analytics ($M)", 15, USD_M, "Assumption"),
    ("Contracting and legal ($M)", 5, USD_M, "Assumption"),
    ("Contingency", 0.15, PCT, "Assumption"),
    ("Discount rate", 0.08, PCT, "Assumption"),
    ("Savings ramp year 1", 0.30, PCT, "Assumption"),
    ("Savings ramp year 2", 0.70, PCT, "Assumption"),
    ("Savings ramp year 3", 1.00, PCT, "Assumption"),
]
header(ws, 4, ["Input", "Value", "Source / note"])
for i, (lab, v, fmt, src) in enumerate(inputs, start=5):
    ws.cell(row=i, column=1, value=lab).font = font()
    c = ws.cell(row=i, column=2, value=v)
    c.font, c.number_format, c.fill = font(BLUE), fmt, KEY_FILL
    ws.cell(row=i, column=3, value=src).font = font(italic=True, color="595959")
SPEND, SUP, COST, PROG, LEGAL, CONT, DISC, R1, R2, R3 = [f"$B${i}" for i in range(5, 15)]

r0 = 17
ws.cell(row=r0 - 1, column=1, value="Segments (shares validated on real data in step 2)").font = font(bold=True)
cols = ["Segment", "Share of suppliers", "Share of spend", "Target cut", "Price savings rate",
        "Transition cost per exit ($M)", "Suppliers", "Spend ($M)", "Exits", "Suppliers after",
        "Spend addressed ($M)", "Price savings ($M)", "Transition cost ($M)"]
header(ws, r0, cols)
segs = [("A Strategic", 0.02, 0.70, 0.00, 0.005, 0.0),
        ("B Core", 0.13, 0.22, 0.25, 0.05, 0.025),
        ("C Tail", 0.85, 0.08, 0.60, 0.08, 0.0005)]
for i, (name, ss, sp, cut, rate, tr) in enumerate(segs, start=r0 + 1):
    ws.cell(row=i, column=1, value=name).font = font()
    for col, v, fmt in [(2, ss, PCT), (3, sp, PCT), (4, cut, PCT), (5, rate, PCT), (6, tr, '$#,##0.0000')]:
        c = ws.cell(row=i, column=col, value=v)
        c.font, c.number_format = font(BLUE), fmt
    f = {
        7: (f"={SUP}*B{i}", NUM), 8: (f"={SPEND}*C{i}", USD), 9: (f"=G{i}*D{i}", NUM), 10: (f"=G{i}-I{i}", NUM),
        11: (f"=IF(D{i}=0,H{i},H{i}*D{i})", USD), 12: (f"=K{i}*E{i}", USD_M), 13: (f"=I{i}*F{i}", USD_M),
    }
    for col, (formula, fmt) in f.items():
        c = ws.cell(row=i, column=col, value=formula)
        c.font, c.number_format = font(), fmt
tr_ = r0 + 4
ws.cell(row=tr_, column=1, value="Total").font = font(bold=True)
for col, fmt in [(7, NUM), (8, USD), (9, NUM), (10, NUM), (11, USD), (12, USD_M), (13, USD_M)]:
    L = get_column_letter(col)
    c = ws.cell(row=tr_, column=col, value=f"=SUM({L}{r0+1}:{L}{r0+3})")
    c.font, c.number_format = font(bold=True), fmt
ws.cell(row=tr_ + 1, column=1, value="Supplier reduction").font = font()
c = ws.cell(row=tr_ + 1, column=9, value=f"=I{tr_}/G{tr_}")
c.font, c.number_format = font(), PCT

r = tr_ + 3
summary = [
    ("Price savings ($M/yr)", f"=L{tr_}"),
    ("Process savings: fewer suppliers to maintain ($M/yr)", f"=I{tr_}*{COST}"),
    ("Run-rate savings ($M/yr)", f"=B{r}+B{r+1}"),
    ("Run-rate as % of addressable spend", f"=B{r+2}/{SPEND}"),
    ("One-time cost ($M)", f"=({PROG}+{LEGAL}+M{tr_})*(1+{CONT})"),
]
for i, (lab, formula) in enumerate(summary):
    ws.cell(row=r + i, column=1, value=lab).font = font(bold=(i in (2, 4)))
    c = ws.cell(row=r + i, column=2, value=formula)
    c.font, c.number_format = font(bold=(i in (2, 4))), (PCT if i == 3 else USD_M)
RUN, OT = f"$B${r+2}", f"$B${r+4}"

rs = r + 7
ws.cell(row=rs - 1, column=1, value="Scenarios").font = font(bold=True)
header(ws, rs, ["Scenario", "Savings vs base", "Cost vs base", "Run-rate ($M/yr)", "Year 1 ($M)", "Year 2 ($M)",
                "Year 3 ($M)", "3-yr savings ($M)", "One-time cost ($M)", "3-yr NPV ($M)", "ROI"])
for i, (name, a, b) in enumerate([("Low", 0.5, 1.25), ("Base", 1.0, 1.0), ("High", 1.3, 0.9)], start=rs + 1):
    ws.cell(row=i, column=1, value=name).font = font()
    for col, v in [(2, a), (3, b)]:
        c = ws.cell(row=i, column=col, value=v)
        c.font, c.number_format = font(BLUE), PCT
    f = {4: f"={RUN}*B{i}", 5: f"=D{i}*{R1}", 6: f"=D{i}*{R2}", 7: f"=D{i}*{R3}", 8: f"=SUM(E{i}:G{i})",
         9: f"={OT}*C{i}", 10: f"=-I{i}+E{i}/(1+{DISC})+F{i}/(1+{DISC})^2+G{i}/(1+{DISC})^3",
         11: f"=(H{i}-I{i})/I{i}"}
    for col, formula in f.items():
        c = ws.cell(row=i, column=col, value=formula)
        c.font, c.number_format = font(), ('0.0"x"' if col == 11 else USD_M)
widths(ws, [44, 14, 14, 12, 12, 14, 12, 12, 12, 14, 14, 14, 14])

# ---------------------------------------------------------------- data
con = sqlite3.connect("data/procurement.db")

# ---------------------------------------------------------------- Step 1
ws = wb.create_sheet("1_Data_Cleaning")
title(ws, "Step 1 — Load and clean real data",
      "Source: State of California DGS, Purchase Order Data FY2012-15, https://catalog.data.gov/dataset/purchase-order-data")
ex = pd.read_sql("SELECT exclusion_reason AS reason, COUNT(*) AS lines, SUM(amount_usd)/1e6 AS spend_m "
                 "FROM excluded_lines GROUP BY 1", con)
kept = pd.read_sql("SELECT COUNT(*) AS lines, SUM(amount_usd)/1e6 AS spend_m, "
                   "COUNT(DISTINCT supplier_code) AS suppliers FROM spend_lines", con).iloc[0]
label = {"exempt_method": "Excluded: procurement-exempt methods",
         "public_body_or_health_plan": "Excluded: public bodies and health plans (pass-through)",
         "missing_or_zero_amount": "Excluded: missing or zero amount"}
header(ws, 4, ["Stage", "Lines", "Spend ($M)"])
rows = [(label[x.reason], x.lines, x.spend_m) for x in ex.itertuples()]
for i, (lab, n, s) in enumerate(rows, start=6):
    ws.cell(row=i, column=1, value=lab).font = font()
    ws.cell(row=i, column=2, value=int(n)).number_format = NUM
    ws.cell(row=i, column=3, value=float(s)).number_format = USD_M
k = 6 + len(rows)
ws.cell(row=k, column=1, value="Addressable (kept)").font = font(bold=True)
ws.cell(row=k, column=2, value=int(kept.lines)).number_format = NUM
ws.cell(row=k, column=3, value=float(kept.spend_m)).number_format = USD_M
ws.cell(row=5, column=1, value="Raw file").font = font(bold=True)
for col in (2, 3):
    L = get_column_letter(col)
    c = ws.cell(row=5, column=col, value=f"=SUM({L}6:{L}{k})")
    c.font, c.number_format = font(bold=True), (NUM if col == 2 else USD_M)
ws.cell(row=k + 2, column=1, value="Addressable suppliers").font = font()
ws.cell(row=k + 2, column=2, value=int(kept.suppliers)).number_format = NUM
ws.cell(row=k + 3, column=1, value="Addressable share of raw spend").font = font()
c = ws.cell(row=k + 3, column=2, value=f"=C{k}/C5")
c.number_format = PCT
widths(ws, [52, 14, 16])

# ---------------------------------------------------------------- Step 2
ws = wb.create_sheet("2_Segments")
title(ws, "Step 2 — Where does the spend sit? (Pareto / ABC)",
      "A = suppliers making up the first 70% of spend; B = next 22%; C = long tail. 3-year spend.")
seg = pd.read_sql("""SELECT segment AS Segment, COUNT(*) AS Suppliers, SUM(spend_usd)/1e6 AS "Spend ($M)",
    SUM(inactive_18m) AS "Inactive 18+ months", SUM(one_time) AS "One-time (1 PO)",
    SUM(CASE WHEN inactive_18m=1 OR one_time=1 THEN 1 ELSE 0 END) AS "Inactive or one-time",
    SUM(small_or_diverse) AS "Small or diverse"
    FROM supplier_segments GROUP BY 1 ORDER BY 1""", con)
end = write_df(ws, seg, 4, {"Suppliers": NUM, "Spend ($M)": USD_M, "Inactive 18+ months": NUM,
                            "One-time (1 PO)": NUM, "Inactive or one-time": NUM, "Small or diverse": NUM})
t = end + 1
ws.cell(row=t, column=1, value="Total").font = font(bold=True)
for col in range(2, 8):
    L = get_column_letter(col)
    c = ws.cell(row=t, column=col, value=f"=SUM({L}5:{L}{end})")
    c.font, c.number_format = font(bold=True), (USD_M if col == 3 else NUM)
header(ws, 4, ["Segment", "Suppliers", "Spend ($M)", "Inactive 18+ months", "One-time (1 PO)",
               "Inactive or one-time", "Small or diverse", "% of suppliers", "% of spend", "% of segment inactive or one-time"])
for i in range(5, end + 1):
    for col, formula in [(8, f"=B{i}/B${t}"), (9, f"=C{i}/C${t}"), (10, f"=F{i}/B{i}")]:
        c = ws.cell(row=i, column=col, value=formula)
        c.font, c.number_format = font(), PCT

p = t + 3
ws.cell(row=p - 1, column=1, value="Pareto curve (real data) vs business case assumption").font = font(bold=True)
curve = pd.read_csv("outputs/step2_pareto_curve.csv")
curve.columns = ["Top % of suppliers", "% of spend (real)"]
curve["Top % of suppliers"] /= 100
curve["% of spend (real)"] /= 100
write_df(ws, curve, p, {"Top % of suppliers": PCT, "% of spend (real)": PCT})
ws.cell(row=p, column=4, value="Business case assumption").font = Font(name=F, bold=True, color="FFFFFF")
ws.cell(row=p, column=4).fill = HDR_FILL
ws.cell(row=p + 3, column=4, value="2% of suppliers = 70% of spend").font = font(italic=True)
widths(ws, [16, 12, 14, 16, 14, 16, 14, 14, 12, 18])

ws = wb.create_sheet("2_Fragmented_Categories")
title(ws, "Step 2 — Most fragmented categories (most suppliers)",
      "Many suppliers with little spend each = first consolidation targets")
frag = pd.read_csv("outputs/step2_fragmented_categories.csv")
frag.columns = ["Category", "Suppliers", "Tail suppliers", "Spend ($M)", "Spend per supplier ($K)",
                "% of spend with tail suppliers"]
frag["% of spend with tail suppliers"] /= 100
write_df(ws, frag, 4, {"Suppliers": NUM, "Tail suppliers": NUM, "Spend ($M)": USD_M,
                       "Spend per supplier ($K)": USD, "% of spend with tail suppliers": PCT})
widths(ws, [60, 12, 14, 12, 18, 20])

ws = wb.create_sheet("2_Supplier_List")
title(ws, "Step 2 — Every supplier with its segment (16,933 real suppliers)",
      "Spend is 3-year addressable spend. Inactive = no PO after 2013-12-31. One-time = one PO in 3 years.")
sl = pd.read_sql("""SELECT spend_rank AS Rank, supplier_code AS "Supplier code", supplier_name AS Supplier,
    segment AS Segment, spend_usd AS "Spend ($)", po_count AS POs, departments AS Departments,
    categories AS Categories, substr(last_po_date,1,10) AS "Last PO", inactive_18m AS "Inactive 18m",
    one_time AS "One-time", small_or_diverse AS "Small or diverse", cum_share AS "Cumulative % of spend"
    FROM supplier_segments ORDER BY spend_rank""", con)
write_df(ws, sl, 4, {"Spend ($)": USD, "POs": NUM, "Cumulative % of spend": PCT})
ws.freeze_panes = "D5"
ws.auto_filter.ref = f"A4:{get_column_letter(len(sl.columns))}{4 + len(sl)}"
widths(ws, [8, 13, 46, 13, 15, 8, 12, 11, 12, 11, 10, 14, 14])

# ---------------------------------------------------------------- Step 3
ws = wb.create_sheet("3_Kraljic")
title(ws, "Step 3 — How should each category be handled? (Kraljic matrix)",
      "Value = category spend (top categories = 80% of spend). Risk = non-competitive share + top-3 concentration "
      "+ thin supply base, ranked within size bands.")
ks = pd.read_csv("outputs/step3_kraljic_summary.csv")
ks = ks[["quadrant", "categories", "spend_b", "suppliers"]]
ks.columns = ["Quadrant", "Categories", "Spend ($B)", "Supplier relationships"]
end = write_df(ws, ks, 4, {"Categories": NUM, "Spend ($B)": '$#,##0.00', "Supplier relationships": NUM})
ws.cell(row=4, column=5, value="% of spend")
header(ws, 4, ["Quadrant", "Categories", "Spend ($B)", "Supplier relationships", "% of spend"])
for i in range(5, end + 1):
    c = ws.cell(row=i, column=5, value=f"=C{i}/SUM(C$5:C${end})")
    c.font, c.number_format = font(), PCT
kc = pd.read_csv("outputs/step3_kraljic_categories.csv")
kc = kc[["category", "segment_title", "quadrant", "agreement", "spend_usd", "suppliers", "active_suppliers",
         "pct_noncompetitive", "pct_top3", "risk_score"]]
kc.columns = ["Category", "UNSPSC segment", "Quadrant", "Agreement type", "Spend ($)", "Suppliers",
              "Active suppliers", "% non-competitive", "% with top 3 suppliers", "Risk score (0-1)"]
kc["% non-competitive"] /= 100
kc["% with top 3 suppliers"] /= 100
s = end + 3
ws.cell(row=s - 1, column=1, value="All 409 categories").font = font(bold=True)
write_df(ws, kc, s, {"Spend ($)": USD, "Suppliers": NUM, "Active suppliers": NUM,
                     "% non-competitive": PCT, "% with top 3 suppliers": PCT, "Risk score (0-1)": "0.00"})
ws.auto_filter.ref = f"A{s}:J{s + len(kc)}"
widths(ws, [52, 40, 13, 46, 15, 11, 11, 14, 14, 12])

# ---------------------------------------------------------------- Step 4
if Path("outputs/step4_supplier_decisions.csv").exists():
    ws = wb.create_sheet("4_Decision_Summary")
    title(ws, "Step 4 — Which suppliers stay and which go?",
          "Rules applied in order; the first rule that matches sets the decision. Duplicates found by TF-IDF "
          "name matching (cosine >= 0.88).")
    br = pd.read_csv("outputs/step4_decisions_by_rule.csv")
    br.columns = ["Rule", "Decision", "Reason", "Suppliers", "Spend 3 yrs ($M)"]
    end = write_df(ws, br, 4, {"Suppliers": NUM, "Spend 3 yrs ($M)": USD_M})
    t = end + 1
    ws.cell(row=t, column=1, value="Total").font = font(bold=True)
    for col, fmt in [(4, NUM), (5, USD_M)]:
        L = get_column_letter(col)
        c = ws.cell(row=t, column=col, value=f"=SUM({L}5:{L}{end})")
        c.font, c.number_format = font(bold=True), fmt
    h = pd.read_csv("outputs/step4_headline.csv")
    r = t + 3
    ws.cell(row=r - 1, column=1, value="Headline").font = font(bold=True)
    header(ws, r, ["Metric", "Value"])
    for i, rec in enumerate(h.itertuples(index=False), start=r + 1):
        ws.cell(row=i, column=1, value=rec.metric).font = font()
        c = ws.cell(row=i, column=2, value=float(rec.value))
        c.number_format = PCT if rec.value < 1 else (USD_M if "$M" in rec.metric else NUM)
    seg = pd.read_csv("outputs/step4_decisions_by_segment.csv")
    r = r + len(h) + 3
    ws.cell(row=r - 1, column=1, value="Decisions by segment").font = font(bold=True)
    write_df(ws, seg, r, {c: NUM for c in seg.columns[1:]})
    widths(ws, [66, 14, 70, 12, 16])

    ws = wb.create_sheet("4_Supplier_Decisions")
    title(ws, "Step 4 — Decision and reason code for every supplier (16,933 real suppliers)",
          "Filter by Decision or Rule. Score = 0-100 scorecard within the supplier's primary category.")
    sd = pd.read_csv("outputs/step4_supplier_decisions.csv")
    sd.columns = ["Supplier code", "Supplier", "Segment", "Primary category", "Kraljic quadrant", "Spend 3 yrs ($)",
                  "POs", "Departments", "Last PO", "Small or diverse", "Score", "Rule", "Decision", "Reason",
                  "Merge into (master)", "Agreement if kept"]
    sd["Last PO"] = sd["Last PO"].astype(str).str[:10]
    write_df(ws, sd, 4, {"Spend 3 yrs ($)": USD, "POs": NUM, "Score": "0.0"})
    ws.freeze_panes = "C5"
    ws.auto_filter.ref = f"A4:{get_column_letter(len(sd.columns))}{4 + len(sd)}"
    widths(ws, [12, 42, 12, 36, 13, 15, 7, 11, 11, 10, 8, 6, 13, 60, 36, 34])

# ---------------------------------------------------------------- Files and sources
REPO = "https://github.com/hemant-singla/jnj-supplier-rationalization/blob/main/"
ws = wb.create_sheet("Files_and_Sources", 1)
title(ws, "Files and sources used in this workbook",
      "Every number traces to one of these. Code links point to the project's GitHub repository.")
files = [
    ("Data source", "All", "State of California DGS — Purchase Order Data FY2012-15 (CSV, 157 MB, public)",
     "https://catalog.data.gov/dataset/purchase-order-data", "Real purchase orders: suppliers, amounts, UNSPSC categories"),
    ("Data source", "0", "J&J 2024 Health for Humanity Report",
     "https://healthforhumanityreport.jnj.com/2024/_assets/downloads/johnson-johnson-2024-health-for-humanity-report.pdf?h=EDX6Vl9g",
     "29,000+ suppliers (2024)"),
    ("Data source", "0", "J&J 2023 Health for Humanity Report",
     "https://healthforhumanityreport.jnj.com/2023/_assets/downloads/johnson-johnson-2023-health-for-humanity-report.pdf?h=Ka9OvM1t",
     "38,500+ suppliers (2023)"),
    ("Data source", "0", "J&J careers: Director, Procurement Global Process Owner",
     "https://www.careers.jnj.com/en/jobs/r-088156/director-procurement-global-process-owner/",
     "~$35B spend across ~35,000 suppliers"),
    ("Data source", "0", "J&J: DEI in our supply base (2022)",
     "https://belong.jnj.com/2022/driving-innovation/dei-in-our-supply-base.html", "$3B Tier 1 diverse spend (2022)"),
    ("Data source", "—", "SEC EDGAR full-text search (10-K / 20-F, 2023-2026)", "https://efts.sec.gov/LATEST/search-index",
     "Candidate real J&J suppliers (data/raw/jnj_supplier_candidates_sec.md), being verified"),
    ("Code", "0", "model/business_case_model.py", REPO + "model/business_case_model.py",
     "Business case model (same logic as tab 0_Business_Case)"),
    ("Code", "1", "scripts/01_clean_load.py", REPO + "scripts/01_clean_load.py", "Cleans the CSV, applies exclusion rules, loads SQLite"),
    ("SQL", "2", "sql/01_pareto_abc.sql", REPO + "sql/01_pareto_abc.sql", "Pareto / ABC segment per supplier"),
    ("SQL", "2", "sql/02_category_fragmentation.sql", REPO + "sql/02_category_fragmentation.sql", "Category cube"),
    ("Code", "2", "scripts/02_spend_cube.py", REPO + "scripts/02_spend_cube.py", "Runs the step 2 SQL, saves outputs"),
    ("Code", "3", "scripts/03_kraljic.py", REPO + "scripts/03_kraljic.py", "Kraljic scoring and 2x2 chart"),
    ("Code", "4", "scripts/04a_duplicates.py", REPO + "scripts/04a_duplicates.py", "TF-IDF duplicate detection"),
    ("Code", "4", "scripts/04b_decisions.py", REPO + "scripts/04b_decisions.py", "Scorecard and decision rules"),
    ("Code", "All", "scripts/build_outputs_workbook.py", REPO + "scripts/build_outputs_workbook.py", "Builds this workbook"),
    ("Code", "1-4", "scripts/build_data_workbook.py", REPO + "scripts/build_data_workbook.py",
     "Builds the raw-data workbook (every raw row traced through steps 1-4)"),
    ("Output", "1-4", "outputs/JnJ_Data_Raw_to_Decision.xlsx (100 MB, shared separately; too large for GitHub)",
     REPO + "scripts/build_data_workbook.py",
     "All 344,504 raw rows as downloaded + status, exclusion reason, segment, quadrant, decision per row"),
    ("Output", "2", "outputs/step2_*.csv", REPO + "outputs", "Segment summary, Pareto curve, fragmented categories"),
    ("Output", "3", "outputs/step3_kraljic_*.csv; docs/images/kraljic_matrix.png", REPO + "outputs", "Quadrant per category; chart"),
    ("Output", "4", "outputs/step4_*.csv", REPO + "outputs",
     "Supplier decisions, decisions by rule/segment, headline, duplicate pairs for review"),
    ("Write-up", "0", "docs/01_business_case.md", REPO + "docs/01_business_case.md", "Business case"),
    ("Write-up", "—", "docs/02_methodology.md", REPO + "docs/02_methodology.md", "Goal and methods"),
    ("Write-up", "2", "docs/03_step2_spend_cube.md", REPO + "docs/03_step2_spend_cube.md", "Step 2 findings"),
    ("Write-up", "3", "docs/04_step3_kraljic.md", REPO + "docs/04_step3_kraljic.md", "Step 3 findings"),
    ("Write-up", "4", "docs/05_step4_decisions.md", REPO + "docs/05_step4_decisions.md", "Step 4 findings"),
    ("Database", "1-4", "data/procurement.db (SQLite, rebuilt locally, not in git)", REPO + "data/README.md",
     "Tables: spend_lines, excluded_lines, supplier_segments, category_cube, supplier_duplicates, supplier_decisions"),
]
header(ws, 4, ["Type", "Step", "File / source", "Link", "What it provides"])
for i, rec in enumerate(files, start=5):
    for c, v in enumerate(rec, start=1):
        cell = ws.cell(row=i, column=c, value=v)
        cell.font = font()
        if c == 4:
            cell.hyperlink = v
            cell.font = Font(name=F, size=10, color="0563C1", underline="single")
widths(ws, [11, 6, 52, 60, 70])

ws = wb.create_sheet("SQL_Code")
title(ws, "SQL used in step 2 (runs on SQLite)", "Full text of the queries; also in the repo's sql/ folder.")
r = 4
for fname in ["sql/01_pareto_abc.sql", "sql/02_category_fragmentation.sql"]:
    ws.cell(row=r, column=1, value=fname).font = font(bold=True)
    r += 1
    for ln in Path(fname).read_text().splitlines():
        ws.cell(row=r, column=1, value=ln).font = Font(name="Consolas", size=9)
        r += 1
    r += 2
widths(ws, [130])

OUT.parent.mkdir(exist_ok=True)
wb.save(OUT)
print("saved", OUT)
