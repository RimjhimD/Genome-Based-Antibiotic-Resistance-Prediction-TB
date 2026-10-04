"""Sanity checks on the pipeline outputs. Run after 01-07:

    .venv/bin/python scripts/check_results.py

Exits non-zero if any check fails. The checks test that the results are
right, not only that the scripts ran: counts, leakage between train and test,
the WHO catalogue reproducing published accuracy, metric ranges, and the
report tables agreeing with the raw metrics.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

sys.path.insert(0, str(Path(__file__).parent))
import who_catalogue as W  # noqa: E402
from common import DRUGS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROC, RES = ROOT / "data" / "processed", ROOT / "results"
failures = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}{'  - ' + detail if detail else ''}")
    if not ok:
        failures.append(name)


iso = pd.read_csv(PROC / "isolates.csv")
cl = pd.read_csv(PROC / "clusters.csv")
X = sparse.load_npz(PROC / "features_X.npz")
rows = pd.read_csv(PROC / "features_rows.csv").UNIQUEID
m = pd.read_csv(RES / "metrics.csv")
pred = pd.read_csv(RES / "predictions_sa_holdout.csv")
main = pd.read_csv(RES / "table_main.csv")

# ---- data ---------------------------------------------------------------------
check("12,287 isolates, unique IDs", len(iso) == 12287 and iso.UNIQUEID.is_unique, f"{len(iso)}")
sa = iso[iso.south_asia]
check("2,162 South Asian isolates", len(sa) == 2162, f"{len(sa)}")
check("South Asia = India, Pakistan, Nepal only", set(sa.country) == {"IND", "PAK", "NPL"},
      str(sorted(set(sa.country))))
check("labels are 0, 1 or missing",
      all(set(iso[d].dropna().unique()) <= {0.0, 1.0} for d in DRUGS))

# ---- features -----------------------------------------------------------------
check("feature rows align with isolate table", (rows.values == iso.UNIQUEID.values).all())
check("feature matrix is binary", set(np.unique(X.data)) <= {1})
check("no empty feature columns", (X.getnnz(axis=0) >= 3).all())

# ---- clusters -----------------------------------------------------------------
c = cl.merge(iso[["UNIQUEID", "lineage"]], on="UNIQUEID")
check("every isolate in exactly one cluster", c.UNIQUEID.is_unique and len(c) == len(iso))
multi = c[c.cluster_size > 1]
check("no cluster mixes lineages", (multi.groupby("cluster").lineage.nunique() == 1).all())

# ---- leakage: South Asia holdout ----------------------------------------------
iso_c = iso.merge(cl[["UNIQUEID", "cluster"]], on="UNIQUEID")
known = iso_c.country != "UNKNOWN"
for d in DRUGS:
    lab = iso_c[d].notna()
    test = iso_c[lab & iso_c.south_asia]
    train = iso_c[lab & known & ~iso_c.south_asia & ~iso_c.cluster.isin(set(test.cluster))]
    p = pred[pred.drug == d]
    ok = (not set(train.UNIQUEID) & set(test.UNIQUEID)
          and not set(train.cluster) & set(test.cluster)
          and set(p.UNIQUEID) == set(test.UNIQUEID)
          and p.n_train.iloc[0] == len(train))
    check(f"{d}: holdout train/test share no isolate or cluster", ok,
          f"train {len(train)}, test {len(test)}")

# ---- WHO catalogue reproduces published CRyPTIC accuracy ----------------------
calls = pd.read_parquet(PROC / "mutations_long.parquet")
tok = W.isolate_tokens(calls)
cat = pd.read_csv(ROOT / "data" / "who" / "who_2023_v2.csv")
for d, lo_sens, lo_spec in [("RIF", 0.93, 0.93), ("INH", 0.90, 0.96)]:
    s = iso[iso[d].notna()]
    p = W.predict(tok, s.UNIQUEID, W.resistance_rules(cat, d)).values
    y = s[d].values
    sens = ((p == 1) & (y == 1)).sum() / (y == 1).sum()
    spec = ((p == 0) & (y == 0)).sum() / (y == 0).sum()
    check(f"WHO {d} sens/spec in published range", sens >= lo_sens and spec >= lo_spec,
          f"{sens:.3f} / {spec:.3f}")

# WHO rule grammar on hand-made calls
toy = pd.DataFrame({
    "UNIQUEID": ["a", "b", "c", "d", "e"], "GENE": ["rpoB", "rpoB", "katG", "katG", "rpoB"],
    "MUTATION": ["S450L", "S450W", "1977_indel", "1977_indel", "D435D"],
    "IS_INDEL": [False, False, True, True, False],
    "IS_SYNONYMOUS": [False, False, False, False, True],
    "INDEL_LENGTH": [np.nan, np.nan, -10, -9, np.nan],
    "INDEL_2": [None, None, "1977_del_10", "1977_del_9", None],
})
toy["frameshift"] = toy.IS_INDEL & (toy.INDEL_LENGTH.abs() % 3 != 0)
toy["stop"] = False
tt = W.isolate_tokens(toy)
ids = ["a", "b", "c", "d", "e"]
exact = list(W.predict(tt, ids, [frozenset({"rpoB@S450L"})]))
codon = list(W.predict(tt, ids, [frozenset({"rpoB@S450?"}), frozenset({"rpoB@D435?"})]))
fs = list(W.predict(tt, ids, [frozenset({"katG@*_fs"})]))
indel = list(W.predict(tt, ids, [frozenset({W.normalise("katG@1977_del_aaaaaaaaa")})]))
check("WHO grammar: exact match", exact == [1, 0, 0, 0, 0], str(exact))
check("WHO grammar: codon wildcard, synonymous change ignored", codon == [1, 1, 0, 0, 0], str(codon))
check("WHO grammar: 10-base deletion is frameshift, 9-base is not", fs == [0, 0, 1, 0, 0], str(fs))
check("WHO grammar: specific indel matched by position and length", indel == [0, 0, 0, 1, 0],
      str(indel))

# ---- metrics ------------------------------------------------------------------
vals = m[["sensitivity", "specificity", "f1"]].values
check("all sensitivity/specificity/F1 in [0, 1]", ((vals >= 0) & (vals <= 1)).all())
auc = m.auc.dropna()
check("all AUC in [0, 1]", ((auc >= 0) & (auc <= 1)).all())
rnd = m[(m.protocol == "random") & (m.test == "all") & (m.model != "WHO")]
check("every model beats chance on random split (AUC > 0.8)", (rnd.auc > 0.8).all(),
      f"min {rnd.auc.min():.3f}")
check("every drug has random, holdout and LOCO results",
      all(set(m[m.drug == d].protocol) == {"random", "sa_holdout", "loco"} for d in DRUGS))

# ---- report tables agree with raw metrics -------------------------------------
ok = True
for _, r in main.iterrows():
    h = m[(m.drug == r.drug) & (m.protocol == "sa_holdout") & (m.model == r.best_model)].iloc[0]
    w = m[(m.drug == r.drug) & (m.protocol == "sa_holdout") & (m.model == "WHO")].iloc[0]
    tol = dict(atol=6e-4, rtol=0)  # table_main.csv is rounded to 3 decimals
    ok &= np.isclose(h.sensitivity, r.sens_holdout, **tol) and np.isclose(h.auc, r.auc_holdout, **tol)
    ok &= np.isclose(w.sensitivity, r.sens_WHO, **tol) and int(h.n) == r.n_SA
check("report Table 1 matches metrics.csv", ok)
best_auc = m[(m.protocol == "random") & (m.test == "all") & (m.model != "WHO")]
chosen = best_auc.loc[best_auc.groupby("drug").auc.idxmax()].set_index("drug").model
check("best model chosen on random-split AUC, not on holdout",
      (chosen.reindex(main.drug).values == main.best_model.values).all())
conf = pd.read_csv(RES / "table_confusion.csv")
check("confusion matrices add up to test set size",
      ((conf.TP + conf.FN + conf.FP + conf.TN).values == main.n_SA.values).all())
lin = pd.read_csv(RES / "table_lineage_random_vs_holdout.csv")
check("per-lineage resistant counts do not exceed totals",
      all(lin[lin.drug == d].n_R.sum() <= main.set_index("drug").loc[d, "n_R_SA"] for d in DRUGS))

print(f"\n{len(failures)} failed" if failures else "\nall checks passed")
sys.exit(1 if failures else 0)
