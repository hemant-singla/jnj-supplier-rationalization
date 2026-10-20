"""Step 4a · Duplicate supplier detection (the project's ML piece: entity resolution).

1. Normalize names: lowercase, strip punctuation and legal suffixes (inc, llc, corp, co, dba ...).
2. Exact match on the normalized name  -> duplicate (similarity 1.0).
3. Fuzzy match: TF-IDF on character 3-4-grams of the normalized name + cosine nearest neighbours.
   A pair counts as a duplicate when cosine similarity >= THRESHOLD and both names share the same
   first word (guards against "Pacific Electric" vs "Pacific Engineering").
4. Union-find groups chained matches; the highest-spend record in a group is the master.

Output: supplier_duplicates table (supplier_code -> master_code, similarity) and a review CSV.
"""
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

DB, OUT = Path("data/procurement.db"), Path("outputs")
THRESHOLD = float(sys.argv[1]) if len(sys.argv) > 1 else 0.88

SUFFIXES = (r"\b(inc|incorporated|llc|l l c|llp|lp|ltd|limited|corp|corporation|co|company|the|dba|"
            r"d b a|pc|p c|plc|group|enterprises?|of california|ca|usa|us|na)\b")


def normalize(name: str) -> str:
    s = name.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(SUFFIXES, " ", s)
    return re.sub(r"\s+", " ", s).strip()


with sqlite3.connect(DB) as con:
    sup = pd.read_sql("SELECT supplier_code, supplier_name, spend_usd FROM supplier_segments", con)

sup["norm"] = sup.supplier_name.map(normalize)
sup = sup[sup.norm.str.len() > 0].reset_index(drop=True)
sup["first"] = sup.norm.str.split().str[0]

vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4), min_df=2, sublinear_tf=True)
X = vec.fit_transform(sup.norm)
nn = NearestNeighbors(n_neighbors=6, metric="cosine").fit(X)
dist, idx = nn.kneighbors(X)

pairs = []
for i in range(len(sup)):
    for d, j in zip(dist[i, 1:], idx[i, 1:]):
        sim = 1 - d
        if j <= i or sim < 0.70:
            continue
        pairs.append((i, j, round(float(sim), 3)))
pairs = pd.DataFrame(pairs, columns=["i", "j", "similarity"])
pairs["same_first_word"] = sup["first"].values[pairs.i] == sup["first"].values[pairs.j]
pairs["exact_norm"] = sup.norm.values[pairs.i] == sup.norm.values[pairs.j]
pairs.loc[pairs.exact_norm, "similarity"] = 1.0
pairs["name_a"] = sup.supplier_name.values[pairs.i]
pairs["name_b"] = sup.supplier_name.values[pairs.j]
pairs["is_duplicate"] = pairs.exact_norm | ((pairs.similarity >= THRESHOLD) & pairs.same_first_word)

# union-find over accepted pairs
parent = list(range(len(sup)))


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


for i, j in pairs.loc[pairs.is_duplicate, ["i", "j"]].itertuples(index=False):
    parent[find(i)] = find(j)

sup["group"] = [find(i) for i in range(len(sup))]
master = sup.sort_values("spend_usd", ascending=False).groupby("group").supplier_code.first()
sup["master_code"] = sup.group.map(master)
dups = sup[sup.supplier_code != sup.master_code][["supplier_code", "supplier_name", "master_code", "spend_usd"]]
dups = dups.merge(sup[["supplier_code", "supplier_name"]].rename(
    columns={"supplier_code": "master_code", "supplier_name": "master_name"}), on="master_code")

with sqlite3.connect(DB) as con:
    dups.to_sql("supplier_duplicates", con, if_exists="replace", index=False)

OUT.mkdir(exist_ok=True)
pairs.sort_values("similarity", ascending=False)[
    ["name_a", "name_b", "similarity", "same_first_word", "is_duplicate"]].to_csv(
    OUT / "step4_duplicate_pairs_review.csv", index=False)

groups = sup[sup.group.duplicated(keep=False)].groupby("group")
print(f"threshold {THRESHOLD}: {len(dups):,} duplicate records in {groups.ngroups:,} groups; "
      f"spend on duplicate records ${dups.spend_usd.sum()/1e6:,.1f}M")

if "--sample" in sys.argv:
    pd.set_option("display.width", 200, "display.max_colwidth", 45)
    for lo, hi in [(0.95, 0.999), (0.88, 0.95), (0.85, 0.88), (0.80, 0.85), (0.75, 0.80)]:
        s = pairs[(pairs.similarity >= lo) & (pairs.similarity < hi) & pairs.same_first_word]
        print(f"\n--- similarity {lo}-{hi}: {len(s)} pairs (same first word) ---")
        print(s.sample(min(10, len(s)), random_state=1)[["name_a", "name_b", "similarity"]].to_string(index=False))
