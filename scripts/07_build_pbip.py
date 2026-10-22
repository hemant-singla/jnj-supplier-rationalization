"""Step 6: generate the Power BI project (PBIP: TMDL semantic model + PBIR report) for the dashboard.

Output: outputs/powerbi/JnJ_Supplier_Dashboard/  (open JnJ_Supplier_Rationalization.pbip in Power BI Desktop)
The model reads powerbi\\JnJ_PowerBI_Data.xlsx inside the project folder (built by scripts/06_powerbi_data.py).
File formats copied from a project saved by the user's Power BI Desktop (visualContainer 2.14.0, TMDL).
"""
import json
import shutil
import sys
import uuid
from pathlib import Path

XLSX = r"C:\Users\SAMSUNG\Downloads\JnJ_Supplier_Rationalization_Project\powerbi\JnJ_PowerBI_Data.xlsx"
NAME = "JnJ_Supplier_Rationalization"
ROOT = Path("outputs/powerbi/JnJ_Supplier_Dashboard")
THEME_SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else None   # Fluent2 base theme json from the template

# ----------------------------------------------------------------------------- palette
NAVY, TEAL, AMBER, RED, GREY, INK, MUTED = "#0B3C5D", "#1B998B", "#E09F3E", "#C8553D", "#8D99AE", "#1F2933", "#52606D"
PAGE_BG, CARD_BG, BORDER = "#F3F5F8", "#FFFFFF", "#E1E5EA"
DECISION_COLORS = {"KEEP": TEAL, "CONSOLIDATE": AMBER, "MERGE": GREY, "EXIT": RED}
QUAD_COLORS = {"Strategic": NAVY, "Leverage": TEAL, "Bottleneck": AMBER, "Non-critical": GREY}
LEVER_COLORS = {"Price gap on re-routed spend": TEAL, "Process: fewer active suppliers": "#4FB3A9",
                "Re-tender of kept leverage suppliers": "#B8C4D6"}

# ----------------------------------------------------------------------------- semantic model
TABLES = {
    "Suppliers": [("Supplier Code", "string"), ("Supplier", "string"), ("Segment", "string"), ("Category", "string"),
                  ("Quadrant", "string"), ("Decision", "string"), ("Rule", "string"), ("Reason", "string"),
                  ("Agreement", "string"), ("Merge Into", "string"), ("Spend 3yr", "double"),
                  ("Spend per Year", "double"), ("POs", "int64"), ("Departments", "int64"), ("Last PO", "dateTime"),
                  ("Score", "double"), ("Small or Diverse", "string"), ("Inactive 18m", "int64"),
                  ("One Time", "int64"), ("Kept", "int64"), ("Spend Rank", "int64"), ("Decision Order", "int64")],
    "Categories": [("Category", "string"), ("UNSPSC Segment", "string"), ("Quadrant", "string"),
                   ("Agreement", "string"), ("Spend 3yr", "double"), ("Suppliers", "int64"),
                   ("Active Suppliers", "int64"), ("Pct Noncompetitive", "double"), ("Pct Top 3", "double"),
                   ("Risk Score", "double")],
    "Pareto": [("Supplier Rank", "int64"), ("Pct Suppliers", "double"), ("Pct Spend", "double")],
    "Savings": [("Scenario", "string"), ("Lever", "string"), ("Basis", "string"), ("Lever Order", "int64"),
                ("Savings $M per Year", "double"), ("Scenario Order", "int64")],
    "Scenarios": [("Scenario", "string"), ("Run Rate $M", "double"), ("One Time Cost $M", "double"),
                  ("NPV 3yr $M", "double"), ("Share Measured", "double"), ("Goal $M", "double"),
                  ("Measured $M", "double"), ("Retender Needed", "double"), ("Scenario Order", "int64")],
    "PriceGap": [("UNSPSC", "string"), ("Item", "string"), ("Quadrant", "string"), ("Kept Median Price", "double"),
                 ("Exiting Median Price", "double"), ("Price Gap", "double"), ("Kept Lines", "int64"),
                 ("Exiting Lines", "int64"), ("Exiting Spend", "double")],
    "Rules": [("Rule", "string"), ("Decision", "string"), ("Reason", "string")],
    "Quadrants": [("Quadrant", "string"), ("Quadrant Order", "int64"), ("Approach", "string")],
    "TopFragmented": [("Category", "string"), ("Quadrant", "string"), ("Suppliers", "int64"), ("Spend 3yr", "double"),
                      ("Fragmentation Rank", "int64")],
}
COL_FORMAT = {
    ("Suppliers", "Spend 3yr"): r"\$#,0", ("Suppliers", "Spend per Year"): r"\$#,0",
    ("Suppliers", "Last PO"): "yyyy-mm-dd", ("Suppliers", "Score"): "0.0",
    ("Categories", "Spend 3yr"): r"\$#,0", ("Categories", "Pct Noncompetitive"): "0.0%",
    ("Categories", "Pct Top 3"): "0.0%", ("Categories", "Risk Score"): "0.00",
    ("Pareto", "Pct Suppliers"): "0%", ("Pareto", "Pct Spend"): "0%",
    ("PriceGap", "Kept Median Price"): r"\$#,0.00", ("PriceGap", "Exiting Median Price"): r"\$#,0.00",
    ("PriceGap", "Price Gap"): "0.0%", ("PriceGap", "Exiting Spend"): r"\$#,0",
    ("TopFragmented", "Spend 3yr"): r"\$#,0",
}
SORT_BY = {("Savings", "Scenario"): "Scenario Order", ("Savings", "Lever"): "Lever Order",
           ("Scenarios", "Scenario"): "Scenario Order", ("Quadrants", "Quadrant"): "Quadrant Order",
           ("Suppliers", "Decision"): "Decision Order"}
HIDDEN = {("Suppliers", "Decision Order"), ("Suppliers", "Kept"), ("Savings", "Lever Order"),
          ("Savings", "Scenario Order"), ("Scenarios", "Scenario Order"), ("Quadrants", "Quadrant Order")}
M_TYPES = {"string": "type text", "double": "type number", "int64": "Int64.Type", "dateTime": "type datetime"}

USD = r"\$#,0.0;(\$#,0.0);\$#,0.0"
MEASURES = {
    "Suppliers": [
        ("Suppliers Today", "COUNTROWS(Suppliers)", "#,0"),
        ("Suppliers Kept", 'CALCULATE(COUNTROWS(Suppliers), Suppliers[Decision] = "KEEP")', "#,0"),
        ("Supplier Reduction %", "1 - DIVIDE([Suppliers Kept], [Suppliers Today])", "0.0%"),
        ("Annual Spend ($M)", "DIVIDE(SUM(Suppliers[Spend per Year]), 1000000)", USD),
        ("Spend Retained %", 'DIVIDE(CALCULATE(SUM(Suppliers[Spend per Year]), Suppliers[Decision] = "KEEP"), '
                             "SUM(Suppliers[Spend per Year]))", "0.0%"),
        ("Diverse Spend Retained %",
         'DIVIDE(CALCULATE(SUM(Suppliers[Spend per Year]), Suppliers[Small or Diverse] = "Yes", '
         'Suppliers[Decision] = "KEEP"), CALCULATE(SUM(Suppliers[Spend per Year]), '
         'Suppliers[Small or Diverse] = "Yes", Suppliers[Rule] <> "R4"))', "0.0%"),
        ("Re-routed Spend ($M)", 'DIVIDE(CALCULATE(SUM(Suppliers[Spend per Year]), Suppliers[Rule] IN {"R5", "R8"}), '
                                 "1000000)", USD),
    ],
    "Categories": [
        ("Categories Count", "COUNTROWS(Categories)", "#,0"),
        ("Category Spend ($M)", "DIVIDE(SUM(Categories[Spend 3yr]), 3000000)", USD),
        ("Supplier Relationships", "SUM(Categories[Suppliers])", "#,0"),
        ("Avg Risk Score", "AVERAGE(Categories[Risk Score])", "0.00"),
        ("Share of Spend %", "DIVIDE(SUM(Categories[Spend 3yr]), CALCULATE(SUM(Categories[Spend 3yr]), "
                             "ALL(Categories), ALL(Quadrants)))", "0.0%"),
    ],
    "Savings": [
        ("Savings ($M/yr)", "SUM(Savings[Savings $M per Year])", USD),
        ("Goal ($M/yr)", "300", USD),
    ],
    "Scenarios": [
        ("Base Run-rate ($M)", 'CALCULATE(SUM(Scenarios[Run Rate $M]), Scenarios[Scenario] = "Base")', USD),
        ("Base Measured ($M)", 'CALCULATE(SUM(Scenarios[Measured $M]), Scenarios[Scenario] = "Base")', USD),
        ("One-time Cost ($M)", 'CALCULATE(SUM(Scenarios[One Time Cost $M]), Scenarios[Scenario] = "Base")', USD),
        ("Base NPV ($M)", 'CALCULATE(SUM(Scenarios[NPV 3yr $M]), Scenarios[Scenario] = "Base")', USD),
        ("Re-tender Needed %", 'CALCULATE(MAX(Scenarios[Retender Needed]), Scenarios[Scenario] = "Base")', "0.00%"),
    ],
    "PriceGap": [
        ("Median Price Gap", "MEDIAN(PriceGap[Price Gap])", "0.0%"),
        ("Items Compared", "COUNTROWS(PriceGap)", "#,0"),
    ],
}
RELATIONSHIPS = [("Suppliers", "Quadrant", "Quadrants", "Quadrant"),
                 ("Categories", "Quadrant", "Quadrants", "Quadrant"),
                 ("PriceGap", "Quadrant", "Quadrants", "Quadrant"),
                 ("TopFragmented", "Quadrant", "Quadrants", "Quadrant"),
                 ("Suppliers", "Rule", "Rules", "Rule"),
                 ("Savings", "Scenario", "Scenarios", "Scenario")]


def q(name):
    return f"'{name}'" if any(c in name for c in " $%()-/") else name


def table_tmdl(t):
    out = [f"table {t}", f"\tlineageTag: {uuid.uuid4()}", ""]
    for m, expr, fmt in MEASURES.get(t, []):
        out += [f"\tmeasure {q(m)} = {expr}", f"\t\tformatString: {fmt}", f"\t\tlineageTag: {uuid.uuid4()}", ""]
    for c, dt in TABLES[t]:
        numeric = dt in ("double", "int64")
        out += [f"\tcolumn {q(c)}", f"\t\tdataType: {dt}"]
        if (t, c) in COL_FORMAT:
            out.append(f"\t\tformatString: {COL_FORMAT[(t, c)]}")
        elif dt == "int64":
            out.append("\t\tformatString: 0")
        if (t, c) in HIDDEN:
            out.append("\t\tisHidden")
        out += [f"\t\tlineageTag: {uuid.uuid4()}",
                f"\t\tsummarizeBy: {'sum' if numeric and 'Order' not in c and 'Rank' not in c else 'none'}",
                f"\t\tsourceColumn: {c}"]
        if (t, c) in SORT_BY:
            out.append(f"\t\tsortByColumn: {q(SORT_BY[(t, c)])}")
        out += ["", "\t\tannotation SummarizationSetBy = Automatic", ""]
    types = ", ".join(f'{{"{c}", {M_TYPES[dt]}}}' for c, dt in TABLES[t])
    out += [f"\tpartition {t} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
            f'\t\t\t\t  Source = Excel.Workbook(File.Contents("{XLSX}"), null, true),',
            f'\t\t\t\t  Sheet = Source{{[Item = "{t}", Kind = "Sheet"]}}[Data],',
            '\t\t\t\t  Promoted = Table.PromoteHeaders(Sheet, [PromoteAllScalars = true]),',
            f"\t\t\t\t  Typed = Table.TransformColumnTypes(Promoted, {{{types}}})",
            "\t\t\t\tin", "\t\t\t\t  Typed", "", "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(out)


# ----------------------------------------------------------------------------- report helpers
def L(v):
    return {"expr": {"Literal": {"Value": v}}}


def S(text):
    return L("'" + text.replace("'", "''") + "'")


def color(hexv):
    return {"solid": {"color": S(hexv)}}


def col(t, c):
    return {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}}


def meas(t, m):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": t}}, "Property": m}}


def agg(t, c, fn):
    return {"Aggregation": {"Expression": col(t, c), "Function": fn}}


def proj(field, display=None):
    kind = next(iter(field))
    if kind == "Aggregation":
        t = field[kind]["Expression"]["Column"]["Expression"]["SourceRef"]["Entity"]
        p = field[kind]["Expression"]["Column"]["Property"]
        fn = {0: "Sum", 1: "Avg", 5: "CountNonNull"}[field[kind]["Function"]]
        ref, native = f"{fn}({t}.{p})", p
    else:
        t, p = field[kind]["Expression"]["SourceRef"]["Entity"], field[kind]["Property"]
        ref, native = f"{t}.{p}", p
    out = {"field": field, "queryRef": ref, "nativeQueryRef": native}
    if display:
        out["displayName"] = display
    return out


def container(title=None, bg=True, title_size=11):
    o = {
        "background": [{"properties": {"show": L("true"), "color": color(CARD_BG), "transparency": L("0D")}}],
        "border": [{"properties": {"show": L("true"), "color": color(BORDER), "radius": L("8D")}}],
        "dropShadow": [{"properties": {"show": L("false")}}],
        "padding": [{"properties": {"top": L("8D"), "bottom": L("8D"), "left": L("10D"), "right": L("10D")}}],
        "visualHeader": [{"properties": {"show": L("false")}}],
        "subTitle": [{"properties": {"show": L("false")}}],
    }
    if title:
        o["title"] = [{"properties": {"show": L("true"), "text": S(title), "fontSize": L(f"{title_size}D"),
                                      "fontColor": color(INK), "bold": L("true")}}]
    else:
        o["title"] = [{"properties": {"show": L("false")}}]
    if not bg:
        o["background"] = [{"properties": {"show": L("false")}}]
        o["border"] = [{"properties": {"show": L("false")}}]
    return o


def point_colors(t, c, mapping):
    return [{"properties": {"fill": color(v)},
             "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": col(t, c),
                                                               "Right": {"Literal": {"Value": f"'{k}'"}}}}}]}}
            for k, v in mapping.items()]


class Page:
    def __init__(self, name, display):
        self.name, self.display, self.visuals = name, display, []

    def add(self, vtype, x, y, w, h, query=None, objects=None, cont=None, sort=None):
        v = {"visualType": vtype}
        if query:
            v["query"] = {"queryState": query}
            if sort:
                v["query"]["sortDefinition"] = {"sort": [{"field": sort[0], "direction": sort[1]}]}
        if objects:
            v["objects"] = objects
        v["visualContainerObjects"] = cont or container()
        v["drillFilterOtherVisuals"] = True
        n = len(self.visuals)
        self.visuals.append({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
            "name": f"{self.name}v{n:02d}",
            "position": {"x": x, "y": y, "z": n * 100, "height": h, "width": w, "tabOrder": n * 100},
            "visual": v})

    # ---- building blocks
    def header(self, title, subtitle):
        paragraphs = [
            {"textRuns": [{"value": title, "textStyle": {"fontWeight": "bold", "fontSize": "20px", "color": NAVY}}]},
            {"textRuns": [{"value": subtitle, "textStyle": {"fontSize": "11px", "color": MUTED}}]}]
        self.add("textbox", 16, 8, 1248, 58, objects={"general": [{"properties": {"paragraphs": paragraphs}}]},
                 cont=container(bg=False))

    def note(self, x, y, w, h, title, lines):
        paragraphs = [{"textRuns": [{"value": title, "textStyle": {"fontWeight": "bold", "fontSize": "12px",
                                                                     "color": NAVY}}]}]
        paragraphs += [{"textRuns": [{"value": ln, "textStyle": {"fontSize": "11px", "color": INK}}]} for ln in lines]
        self.add("textbox", x, y, w, h, objects={"general": [{"properties": {"paragraphs": paragraphs}}]})

    def card(self, x, y, w, h, field, label, accent=NAVY):
        self.add("card", x, y, w, h, query={"Values": {"projections": [proj(field)]}},
                 objects={"labels": [{"properties": {"fontSize": L("24D"), "color": color(accent),
                                                     "labelDisplayUnits": L("1D")}}],
                          "categoryLabels": [{"properties": {"show": L("false")}}]},
                 cont=container(label, title_size=10))

    def slicer(self, x, y, w, h, field, title, mode="Dropdown"):
        self.add("slicer", x, y, w, h, query={"Values": {"projections": [proj(field)]}},
                 objects={"data": [{"properties": {"mode": S(mode)}}],
                          "header": [{"properties": {"show": L("false")}}]},
                 cont=container(title, title_size=10))

    def table(self, x, y, w, h, fields, title, sort=None, totals=True):
        self.add("tableEx", x, y, w, h, query={"Values": {"projections": [proj(f, d) for f, d in fields]}},
                 objects={"total": [{"properties": {"totals": L("true" if totals else "false")}}],"grid": [{"properties": {"gridHorizontal": L("true"), "rowPadding": L("3D")}}],
                          "columnHeaders": [{"properties": {"fontColor": color("#FFFFFF"),
                                                            "backColor": color(NAVY), "bold": L("true")}}],
                          "values": [{"properties": {"fontSize": L("9D")}}]},
                 cont=container(title), sort=sort)


def write_report(pages, out):
    rep = out / f"{NAME}.Report"
    (rep / "definition" / "pages").mkdir(parents=True, exist_ok=True)
    (rep / ".platform").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": str(uuid.uuid4())}}, indent=2))
    (rep / "definition.pbir").write_text(json.dumps(
        {"version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}}, indent=2))
    (rep / "definition" / "version.json").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0"}, indent=2))
    report = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
        "themeCollection": {"baseTheme": {"name": "Fluent2-CY26SU10",
                                          "reportVersionAtImport": {"visual": "2.14.0", "report": "3.4.0", "page": "2.3.1"},
                                          "type": "SharedResources"}},
        "objects": {"section": [{"properties": {"verticalAlignment": S("Top")}}],
                    "outspacePane": [{"properties": {"expanded": L("false")}}]},
        "resourcePackages": [{"name": "SharedResources", "type": "SharedResources",
                              "items": [{"name": "Fluent2-CY26SU10", "path": "BaseThemes/Fluent2-CY26SU10.json",
                                         "type": "BaseTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True}}
    (rep / "definition" / "report.json").write_text(json.dumps(report, indent=2))
    if THEME_SRC:
        d = rep / "StaticResources" / "SharedResources" / "BaseThemes"
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(THEME_SRC, d / "Fluent2-CY26SU10.json")
    (rep / "definition" / "pages" / "pages.json").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
        "pageOrder": [p.name for p in pages], "activePageName": pages[0].name}, indent=2))
    for p in pages:
        pd_ = rep / "definition" / "pages" / p.name
        (pd_ / "visuals").mkdir(parents=True, exist_ok=True)
        (pd_ / "page.json").write_text(json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
            "name": p.name, "displayName": p.display, "displayOption": "FitToPage", "height": 720, "width": 1280,
            "objects": {"background": [{"properties": {"color": color(PAGE_BG), "transparency": L("0D")}}],
                        "outspace": [{"properties": {"color": color(PAGE_BG)}}]}}, indent=2))
        for v in p.visuals:
            (pd_ / "visuals" / v["name"]).mkdir(exist_ok=True)
            (pd_ / "visuals" / v["name"] / "visual.json").write_text(json.dumps(v, indent=2))


def write_model(out):
    sm = out / f"{NAME}.SemanticModel"
    (sm / "definition" / "tables").mkdir(parents=True, exist_ok=True)
    (sm / "definition" / "cultures").mkdir(exist_ok=True)
    (sm / ".platform").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": str(uuid.uuid4())}}, indent=2))
    (sm / "definition.pbism").write_text(json.dumps({"version": "4.2", "settings": {}}, indent=2))
    (sm / "definition" / "database.tmdl").write_text("database\n\tcompatibilityLevel: 1606\n\n")
    (sm / "definition" / "cultures" / "en-US.tmdl").write_text("cultureInfo en-US\n\n")
    order = json.dumps(list(TABLES))
    model = ["model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
             "\tsourceQueryCulture: en-US", "\tvalueFilterBehavior: independent", "\tdataAccessOptions",
             "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
             "annotation __PBI_TimeIntelligenceEnabled = 0", "", f"annotation PBI_QueryOrder = {order}", "",
             'annotation PBI_ProTooling = ["DevMode"]', ""]
    model += [f"ref table {t}" for t in TABLES] + ["", "ref cultureInfo en-US", ""]
    (sm / "definition" / "model.tmdl").write_text("\n".join(model) + "\n")
    rel = []
    for ft, fc, tt, tc in RELATIONSHIPS:
        rel += [f"relationship {uuid.uuid4()}", f"\tfromColumn: {ft}.{q(fc)}", f"\ttoColumn: {tt}.{q(tc)}", ""]
    (sm / "definition" / "relationships.tmdl").write_text("\n".join(rel) + "\n")
    for t in TABLES:
        (sm / "definition" / "tables" / f"{t}.tmdl").write_text(table_tmdl(t) + "\n")


# ----------------------------------------------------------------------------- pages
SUB = ("Real procurement data: State of California purchase orders FY2012-15 (16,933 addressable suppliers, "
       "$7.3B/yr), scaled to J&J's public totals (~29,000 suppliers, ~$35B addressable spend)")

p1 = Page("p1overview", "1 Executive Summary")
p1.header("Supplier Rationalization: cut 73% of supplier records, keep 87% of spend", SUB)
cards = [(meas("Suppliers", "Suppliers Today"), "Suppliers today", NAVY),
         (meas("Suppliers", "Suppliers Kept"), "Suppliers kept", TEAL),
         (meas("Suppliers", "Supplier Reduction %"), "Supplier reduction", TEAL),
         (meas("Suppliers", "Spend Retained %"), "Spend retained with kept suppliers", NAVY),
         (meas("Suppliers", "Diverse Spend Retained %"), "Small/diverse active spend retained", NAVY),
         (meas("Scenarios", "Base Run-rate ($M)"), "J&J run-rate savings, base ($M/yr)", TEAL)]
cw = (1248 - 5 * 10) / 6
for i, (f, lab, acc) in enumerate(cards):
    p1.card(int(16 + i * (cw + 10)), 74, int(cw), 92, f, lab, acc)
p1.add("clusteredBarChart", 16, 178, 400, 262,
       query={"Category": {"projections": [{**proj(col("Suppliers", "Decision")), "active": True}]},
              "Y": {"projections": [proj(meas("Suppliers", "Suppliers Today"), "Suppliers")]}},
       objects={"dataPoint": point_colors("Suppliers", "Decision", DECISION_COLORS),
                "labels": [{"properties": {"show": L("true"), "labelDisplayUnits": L("1D")}}],
                "valueAxis": [{"properties": {"show": L("false")}}]},
       cont=container("Suppliers by decision"), sort=(col("Suppliers", "Decision"), "Ascending"))
p1.add("lineChart", 428, 178, 420, 262,
       query={"Category": {"projections": [{**proj(col("Pareto", "Pct Suppliers")), "active": True}]},
              "Y": {"projections": [proj(agg("Pareto", "Pct Spend", 0), "Share of spend")]}},
       objects={"categoryAxis": [{"properties": {"axisType": S("Scalar"), "showAxisTitle": L("true"),
                                                 "titleText": S("Share of suppliers, ranked by spend")}}],
                "valueAxis": [{"properties": {"showAxisTitle": L("true"), "titleText": S("Cumulative share of spend")}}],
                "dataPoint": [{"properties": {"fill": color(NAVY)}}]},
       cont=container("Pareto: top 2% of suppliers hold 70% of spend"))
p1.add("hundredPercentStackedBarChart", 860, 178, 404, 262,
       query={"Category": {"projections": [{**proj(col("Suppliers", "Segment")), "active": True}]},
              "Y": {"projections": [proj(meas("Suppliers", "Suppliers Today"), "Suppliers")]},
              "Series": {"projections": [proj(col("Suppliers", "Decision"))]}},
       objects={"dataPoint": point_colors("Suppliers", "Decision", DECISION_COLORS),
                "legend": [{"properties": {"show": L("true"), "position": S("Top")}}]},
       cont=container("Decision mix by spend segment (A/B/C)"), sort=(col("Suppliers", "Segment"), "Ascending"))
p1.table(16, 452, 820, 252,
         [(col("Rules", "Rule"), "Rule"), (col("Rules", "Decision"), "Decision"), (col("Rules", "Reason"), "Reason"),
          (meas("Suppliers", "Suppliers Today"), "Suppliers"), (meas("Suppliers", "Annual Spend ($M)"), "Spend $M/yr")],
         "Every supplier has one decision and one reason code (rules applied in order R1-R8)",
         sort=(col("Rules", "Rule"), "Ascending"))
p1.slicer(848, 452, 200, 76, col("Suppliers", "Segment"), "Spend segment")
p1.slicer(1064, 452, 200, 76, col("Quadrants", "Quadrant"), "Kraljic quadrant")
p1.slicer(848, 540, 200, 76, col("Suppliers", "Small or Diverse"), "Small or diverse")
p1.slicer(1064, 540, 200, 76, col("Suppliers", "Decision"), "Decision")
p1.note(848, 628, 416, 76, "So what",
        ["8,824 exits are inactive or one-time vendors: the easiest exits to defend.",
         "Strategic (A) suppliers are never cut; they move to partnership agreements."])

p2 = Page("p2categories", "2 Category Strategy")
p2.header("Category strategy: consolidate leverage and non-critical categories, protect bottlenecks",
          "Kraljic matrix of 409 real UNSPSC categories. Value = category spend; supply risk = non-competitive "
          "buying + top-3 concentration + thin supply base (ranked within size bands)")
p2.add("scatterChart", 16, 74, 760, 418,
       query={"Category": {"projections": [{**proj(col("Categories", "Category")), "active": True}]},
              "Series": {"projections": [proj(col("Categories", "Quadrant"))]},
              "X": {"projections": [proj(meas("Categories", "Category Spend ($M)"), "Spend $M/yr")]},
              "Y": {"projections": [proj(meas("Categories", "Avg Risk Score"), "Supply risk score")]},
              "Size": {"projections": [proj(meas("Categories", "Supplier Relationships"), "Suppliers")]}},
       objects={"dataPoint": point_colors("Categories", "Quadrant", QUAD_COLORS),
                "categoryAxis": [{"properties": {"logAxisScale": L("true"), "showAxisTitle": L("true"),
                                                 "titleText": S("Category spend, $M per year (log scale)")}}],
                "valueAxis": [{"properties": {"showAxisTitle": L("true"),
                                              "titleText": S("Supply risk score (0 = low, 1 = high)")}}],
                "legend": [{"properties": {"show": L("true"), "position": S("Top")}}]},
       cont=container("Kraljic matrix: bubble size = number of suppliers"))
p2.table(788, 74, 476, 214,
         [(col("Quadrants", "Quadrant"), "Quadrant"), (meas("Categories", "Categories Count"), "Categories"),
          (meas("Categories", "Share of Spend %"), "Share of spend"),
          (meas("Categories", "Supplier Relationships"), "Suppliers"), (col("Quadrants", "Approach"), "Approach")],
         "Quadrant summary: 59% of spend sits in 20 leverage categories", sort=(col("Quadrants", "Quadrant"), "Ascending"))
p2.add("clusteredBarChart", 788, 298, 476, 194,
       query={"Category": {"projections": [{**proj(col("TopFragmented", "Category")), "active": True}]},
              "Y": {"projections": [proj(agg("TopFragmented", "Suppliers", 0), "Suppliers")]}},
       objects={"dataPoint": [{"properties": {"fill": color(AMBER)}}],
                "labels": [{"properties": {"show": L("true")}}], "valueAxis": [{"properties": {"show": L("false")}}]},
       cont=container("Most fragmented categories: first consolidation targets"),
       sort=(agg("TopFragmented", "Suppliers", 0), "Descending"))
p2.table(16, 504, 1248, 200,
         [(col("Categories", "Category"), "Category"), (col("Categories", "Quadrant"), "Quadrant"),
          (col("Categories", "Agreement"), "Agreement type"), (meas("Categories", "Category Spend ($M)"), "Spend $M/yr"),
          (agg("Categories", "Suppliers", 0), "Suppliers"), (agg("Categories", "Pct Noncompetitive", 1), "% non-competitive"),
          (agg("Categories", "Pct Top 3", 1), "% top-3 suppliers"), (agg("Categories", "Risk Score", 1), "Risk score")],
         "All 409 categories with quadrant and agreement type", sort=(meas("Categories", "Category Spend ($M)"), "Descending"),
         totals=False)

p3 = Page("p3savings", "3 Savings Case")
p3.header("Savings: $366M a year at J&J scale in the base case, but only $86M is measured in the data",
          "Price-gap test on 127 goods items bought from both kept and exiting suppliers; re-tender saving is an "
          "assumption. Scaled to J&J by spend ($35B) and supplier count (29,000).")
cards3 = [(meas("Scenarios", "Base Run-rate ($M)"), "Run-rate savings, base ($M/yr)", TEAL),
          (meas("Scenarios", "Base Measured ($M)"), "Measured in the data ($M/yr)", NAVY),
          (meas("Scenarios", "One-time Cost ($M)"), "One-time cost ($M)", MUTED),
          (meas("Scenarios", "Base NPV ($M)"), "3-year NPV, base ($M)", NAVY),
          (meas("Scenarios", "Re-tender Needed %"), "Re-tender saving needed for $300M goal", RED)]
cw = (1248 - 4 * 10) / 5
for i, (f, lab, acc) in enumerate(cards3):
    p3.card(int(16 + i * (cw + 10)), 74, int(cw), 92, f, lab, acc)
p3.add("lineStackedColumnComboChart", 16, 178, 620, 300,
       query={"Category": {"projections": [{**proj(col("Savings", "Scenario")), "active": True}]},
              "Y": {"projections": [proj(meas("Savings", "Savings ($M/yr)"), "Savings $M/yr")]},
              "Series": {"projections": [proj(col("Savings", "Lever"))]},
              "Y2": {"projections": [proj(meas("Savings", "Goal ($M/yr)"), "Goal $M/yr")]}},
       objects={"dataPoint": point_colors("Savings", "Lever", LEVER_COLORS),
                "labels": [{"properties": {"show": L("true"), "labelDisplayUnits": L("1D"), "labelPrecision": L("0D")}}],
                "legend": [{"properties": {"show": L("true"), "position": S("Top")}}]},
       cont=container("J&J run-rate savings by scenario vs the $300M goal (line)"),
       sort=(col("Savings", "Scenario"), "Ascending"))
p3.add("clusteredBarChart", 648, 178, 616, 300,
       query={"Category": {"projections": [{**proj(col("Quadrants", "Quadrant")), "active": True}]},
              "Y": {"projections": [proj(meas("PriceGap", "Median Price Gap"), "Median price gap")]}},
       objects={"dataPoint": point_colors("Quadrants", "Quadrant", QUAD_COLORS),
                "labels": [{"properties": {"show": L("true")}}]},
       cont=container("Exiting suppliers charge more only in Leverage (+9.8%) and Non-critical (+5.2%)"),
       sort=(col("Quadrants", "Quadrant"), "Ascending"))
p3.table(16, 490, 820, 214,
         [(col("PriceGap", "Item"), "Item"), (col("PriceGap", "Quadrant"), "Quadrant"),
          (agg("PriceGap", "Kept Median Price", 0), "Kept: median unit price"),
          (agg("PriceGap", "Exiting Median Price", 0), "Exiting: median unit price"),
          (agg("PriceGap", "Price Gap", 0), "Gap"), (agg("PriceGap", "Exiting Spend", 0), "Exiting spend, 3 yrs")],
         "Price-gap evidence: same item, kept vs exiting suppliers", sort=(agg("PriceGap", "Exiting Spend", 0), "Descending"),
         totals=False)
p3.note(848, 490, 416, 214, "What has to be true",
        ["Measured savings: $63M price gap on re-routed spend + $23M fewer suppliers to maintain.",
         "The other $280M assumes a 1.5% re-tender saving with kept leverage suppliers.",
         "To reach $300M, that re-tender must deliver at least 1.15%: test it in a pilot sourcing wave first.",
         "Payback is fast: $40M one-time cost; even the low case has a positive NPV ($135M)."])

p4 = Page("p4explorer", "4 Supplier Explorer")
p4.header("Supplier explorer: decision and reason code for all 16,933 suppliers",
          "Filter by decision, rule, segment or quadrant. Spend is annual (3-year total / 3).")
for i, (f, t) in enumerate([(col("Suppliers", "Decision"), "Decision"), (col("Suppliers", "Rule"), "Rule"),
                            (col("Suppliers", "Segment"), "Spend segment"), (col("Quadrants", "Quadrant"), "Kraljic quadrant"),
                            (col("Suppliers", "Small or Diverse"), "Small or diverse")]):
    p4.slicer(16 + i * 252, 74, 240, 70, f, t)
p4.table(16, 156, 1248, 548,
         [(col("Suppliers", "Supplier"), "Supplier"), (col("Suppliers", "Segment"), "Segment"),
          (col("Suppliers", "Category"), "Primary category"), (col("Suppliers", "Quadrant"), "Quadrant"),
          (col("Suppliers", "Decision"), "Decision"), (col("Suppliers", "Rule"), "Rule"),
          (col("Suppliers", "Reason"), "Reason"), (agg("Suppliers", "Spend per Year", 0), "Spend $/yr"),
          (agg("Suppliers", "POs", 0), "POs"), (col("Suppliers", "Last PO"), "Last PO"),
          (agg("Suppliers", "Score", 0), "Score"), (col("Suppliers", "Merge Into"), "Merge into"),
          (col("Suppliers", "Agreement"), "Agreement if kept")],
         "Supplier-level decisions", sort=(agg("Suppliers", "Spend per Year", 0), "Descending"), totals=False)

# ----------------------------------------------------------------------------- write
if ROOT.exists():
    shutil.rmtree(ROOT)
ROOT.mkdir(parents=True)
(ROOT / f"{NAME}.pbip").write_text(json.dumps({"version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
                                               "settings": {"enableAutoRecovery": True}}, indent=2))
(ROOT / ".gitignore").write_text("**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
write_model(ROOT)
write_report([p1, p2, p3, p4], ROOT)
files = sorted(p for p in ROOT.rglob("*") if p.is_file())
print(len(files), "files;", sum(len(p.visuals) for p in [p1, p2, p3, p4]), "visuals")
