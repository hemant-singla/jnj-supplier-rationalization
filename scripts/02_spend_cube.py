"""Step 2: run the spend cube SQL and save result tables to outputs/."""
import sqlite3
from pathlib import Path

import pandas as pd

DB = Path("data/procurement.db")
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)


def run(con: sqlite3.Connection, path: str) -> pd.DataFrame:
    """Execute all statements in a .sql file; return the result of the final SELECT."""
    lines = [ln for ln in Path(path).read_text().splitlines() if not ln.strip().startswith("--")]
    *setup, final = [s for s in "\n".join(lines).split(";") if s.strip()]
    con.executescript(";\n".join(setup) + ";")
    return pd.read_sql(final, con)


with sqlite3.connect(DB) as con:
    seg = run(con, "sql/01_pareto_abc.sql")
    frag = run(con, "sql/02_category_fragmentation.sql")

    easy = pd.read_sql("""
        SELECT segment, COUNT(*) AS suppliers,
               SUM(CASE WHEN inactive_18m = 1 OR one_time = 1 THEN 1 ELSE 0 END) AS inactive_or_one_time,
               ROUND(SUM(CASE WHEN inactive_18m = 1 OR one_time = 1 THEN spend_usd ELSE 0 END) / 1e6, 1) AS their_spend_m,
               SUM(CASE WHEN (inactive_18m = 1 OR one_time = 1) AND small_or_diverse = 1 THEN 1 ELSE 0 END)
                   AS of_which_small_or_diverse
        FROM supplier_segments GROUP BY segment ORDER BY segment""", con)

    pareto = pd.read_sql("SELECT spend_rank, cum_share FROM supplier_segments ORDER BY spend_rank", con)
    n = len(pareto)
    curve = pd.DataFrame({"pct_suppliers": [0.5, 1, 2, 3, 5, 7.5, 10, 15, 20, 30, 50, 75, 100]})
    curve["pct_spend"] = [round(100 * pareto.cum_share.iloc[max(1, round(n * p / 100)) - 1], 1)
                          for p in curve.pct_suppliers]

seg.to_csv(OUT / "step2_segment_summary.csv", index=False)
frag.to_csv(OUT / "step2_fragmented_categories.csv", index=False)
curve.to_csv(OUT / "step2_pareto_curve.csv", index=False)
easy.to_csv(OUT / "step2_inactive_or_one_time.csv", index=False)

pd.set_option("display.width", 200)
print(seg.to_string(index=False))
print()
print(frag.to_string(index=False))
