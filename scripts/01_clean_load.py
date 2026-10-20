"""Step 1: clean the real California purchase order data and load it into SQLite.

Source: State of California, Dept. of General Services, Purchase Order Data FY2012-13 to FY2014-15
https://catalog.data.gov/dataset/purchase-order-data  (public, no use restrictions)

Addressable-spend rule (mirrors J&J's definition: spend procurement can negotiate):
  1. Drop acquisition methods that are exempt from procurement ("Services are specifically exempt ...").
  2. Drop payees that are public bodies or health plans receiving pass-through funds
     (counties, cities, state agencies, Medi-Cal health plans, "Unknown").
  3. Drop lines with missing or zero amounts.
Every dropped line keeps a reason code in excluded_lines for audit.
"""
import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd

RAW = Path(sys.argv[1] if len(sys.argv) > 1 else "data/raw/purchase-order-data-2012-2015-.csv")
DB = Path("data/procurement.db")

PUBLIC_OR_PLAN = re.compile(
    r"\b(?:county|city of|state of|calif(?:ornia)? state|ca dept|dept\.? of|department of|regents|"
    r"university|school of law|superior court|commission|health plan|healthplan|health authority|"
    r"health systems|partner plan|partnership plan|health group|alliance for health|caloptima|"
    r"health net|public health rx|state healthcare|prison industry authority|"
    r"delta dental|insurance fund|school district|unified school|water district|transit district)\b",
    re.I,
)


def money(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.str.replace(r"[\$,\s]", "", regex=True), errors="coerce")


def main() -> None:
    df = pd.read_csv(RAW, dtype=str, low_memory=False)
    raw_rows, raw_total = len(df), money(df["Total Price"]).sum()

    df = df.rename(columns=lambda c: re.sub(r"[^a-z0-9]+", "_", c.lower()).strip("_"))
    df["amount_usd"] = money(df["total_price"])
    df["unit_price"] = money(df["unit_price"])
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["creation_date"] = pd.to_datetime(df["creation_date"], format="%m/%d/%Y", errors="coerce")
    df["supplier_name"] = df["supplier_name"].fillna("Unknown").str.strip()

    reason = pd.Series("", index=df.index)
    reason[df["acquisition_method"].fillna("").str.startswith("Services are specifically exempt")] = "exempt_method"
    pub = df["supplier_name"].str.contains(PUBLIC_OR_PLAN) | df["supplier_name"].str.fullmatch("Unknown", case=False)
    reason[(reason == "") & pub] = "public_body_or_health_plan"
    reason[(reason == "") & (df["amount_usd"].isna() | (df["amount_usd"] <= 0))] = "missing_or_zero_amount"

    excluded = df[reason != ""].assign(exclusion_reason=reason[reason != ""])
    lines = df[reason == ""].copy()

    keep = ["creation_date", "fiscal_year", "purchase_order_number", "acquisition_type", "acquisition_method",
            "department_name", "supplier_code", "supplier_name", "supplier_qualifications", "supplier_zip_code",
            "calcard", "item_name", "quantity", "unit_price", "amount_usd", "normalized_unspsc",
            "segment", "segment_title", "family", "family_title", "class", "class_title", "commodity_title"]
    lines = lines[keep]

    DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as con:
        lines.to_sql("spend_lines", con, if_exists="replace", index=False)
        excluded[["supplier_code", "supplier_name", "acquisition_method", "fiscal_year", "amount_usd",
                  "exclusion_reason"]].to_sql("excluded_lines", con, if_exists="replace", index=False)
        con.execute("CREATE INDEX IF NOT EXISTS ix_sup ON spend_lines(supplier_code)")
        con.execute("CREATE INDEX IF NOT EXISTS ix_fy ON spend_lines(fiscal_year)")

    summary = (excluded.groupby("exclusion_reason")["amount_usd"].agg(["count", "sum"]))
    print(f"Raw: {raw_rows:,} lines, ${raw_total/1e9:,.1f}B")
    print("Excluded:\n", summary.assign(sum_B=lambda d: d["sum"] / 1e9).drop(columns="sum"))
    print(f"Addressable: {len(lines):,} lines, ${lines.amount_usd.sum()/1e9:,.2f}B, "
          f"{lines.supplier_code.nunique():,} supplier codes, {lines.supplier_name.nunique():,} names")
    print(lines.groupby("fiscal_year").amount_usd.sum().div(1e9).round(2))


if __name__ == "__main__":
    main()
