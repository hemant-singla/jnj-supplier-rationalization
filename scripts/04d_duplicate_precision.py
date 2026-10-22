"""Step 4d · How precise is the duplicate matching at the 0.88 threshold?

Draws a fixed random sample of accepted pairs (seed 42): 50 fuzzy matches (similarity 0.88-0.99, the hard
cases) and 20 exact matches after name normalization. Each pair was judged by hand using the two names, the
supplier's main ZIP code, main category and main buying department. Verdicts are stored in
outputs/step4_duplicate_review_sample.csv (verdict = CORRECT / WRONG; uncertain pairs are counted as WRONG).

Run without arguments to print precision from the stored verdicts. Run with --draw to re-draw the same sample
(it reproduces the pairs in the verdict file).
"""
import sys
from pathlib import Path

import pandas as pd

OUT = Path("outputs")
pairs = pd.read_csv(OUT / "step4_duplicate_pairs_review.csv")
acc = pairs[pairs.is_duplicate]
n_exact, n_fuzzy = int((acc.similarity == 1).sum()), int((acc.similarity < 1).sum())

if "--draw" in sys.argv:
    fz = acc[acc.similarity < 1].sample(50, random_state=42).assign(kind="fuzzy")
    ex = acc[acc.similarity == 1].sample(20, random_state=42).assign(kind="exact")
    print(pd.concat([fz, ex])[["kind", "similarity", "name_a", "name_b"]].to_string(index=False))
    sys.exit()

rev = pd.read_csv(OUT / "step4_duplicate_review_sample.csv")
rows = []
for kind, g in rev.groupby("kind"):
    ok = int((g.verdict == "CORRECT").sum())
    rows.append(dict(kind=kind, sampled=len(g), correct=ok, precision=ok / len(g),
                     precision_if_uncertain_correct=(ok + int(g.uncertain.sum())) / len(g),
                     accepted_pairs=n_exact if kind == "exact" else n_fuzzy))
res = pd.DataFrame(rows).set_index("kind")
overall = (res.precision * res.accepted_pairs).sum() / res.accepted_pairs.sum()
res.loc["all accepted (weighted)"] = [res.sampled.sum(), res.correct.sum(), overall,
                                      (res.precision_if_uncertain_correct * res.accepted_pairs).sum() / res.accepted_pairs.sum(),
                                      res.accepted_pairs.sum()]
res.to_csv(OUT / "step4d_duplicate_precision.csv")
print(res.round(3))
print("\nWrong or uncertain pairs:")
print(rev[rev.verdict == "WRONG"][["kind", "similarity", "name_a", "name_b", "note"]].to_string(index=False))
