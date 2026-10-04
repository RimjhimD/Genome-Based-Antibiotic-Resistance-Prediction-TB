"""Steps 4-5 - train per-drug models and evaluate under three protocols.

Protocols (all transmission-cluster aware):
  random      5-fold grouped CV over every isolate with a known country.
              Metrics are reported on all isolates and on the South Asian ones.
  sa_holdout  train on non-South-Asian isolates, test on India + Pakistan + Nepal.
  loco        leave-one-country-out, each country with >= 150 labelled isolates.
In sa_holdout and loco, training isolates sharing a transmission cluster with
any test isolate are removed.

The WHO 2023 catalogue is scored on exactly the same test isolates.

Output results/metrics.csv, results/predictions_sa_holdout.csv
"""
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold

sys.path.insert(0, str(Path(__file__).parent))
import who_catalogue as W  # noqa: E402
from common import DRUGS, SEED, models  # noqa: E402

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
RES = ROOT / "results"
RES.mkdir(exist_ok=True)

MIN_COUNTRY = 150


def metrics(y, prob, pred):
    y, pred = np.asarray(y), np.asarray(pred)
    tp = ((pred == 1) & (y == 1)).sum()
    tn = ((pred == 0) & (y == 0)).sum()
    out = {"n": len(y), "n_R": int((y == 1).sum()),
           "sensitivity": tp / max((y == 1).sum(), 1),
           "specificity": tn / max((y == 0).sum(), 1),
           "f1": f1_score(y, pred, zero_division=0),
           "auc": roc_auc_score(y, prob) if prob is not None and len(set(y)) == 2 else np.nan}
    out["very_major_error"] = 1 - out["sensitivity"]  # R called S: the dangerous error
    return out


def fit_predict(Xtr, ytr, Xte):
    pw = (ytr == 0).sum() / max((ytr == 1).sum(), 1)
    out = {}
    for name, m in models(pw).items():
        m.fit(Xtr, ytr)
        out[name] = m.predict_proba(Xte)[:, 1]
    return out


iso = pd.read_csv(PROC / "isolates.csv")
cl = pd.read_csv(PROC / "clusters.csv")
iso = iso.merge(cl[["UNIQUEID", "cluster"]], on="UNIQUEID", how="left")
X_all = sparse.load_npz(PROC / "features_X.npz").tocsr().astype(np.float32)
rows = pd.read_csv(PROC / "features_rows.csv").UNIQUEID
assert (rows.values == iso.UNIQUEID.values).all()

cat = pd.read_csv(ROOT / "data" / "who" / "who_2023_v2.csv")
tokens = W.isolate_tokens(pd.read_parquet(PROC / "mutations_long.parquet"))

known = (iso.country != "UNKNOWN").values
records, sa_preds = [], []


def score(drug, protocol, test_name, test_idx, probs, who_pred):
    y = iso[drug].values[test_idx]
    for name, p in probs.items():
        records.append({"drug": drug, "protocol": protocol, "test": test_name, "model": name,
                        **metrics(y, p, (p >= 0.5).astype(int))})
    records.append({"drug": drug, "protocol": protocol, "test": test_name, "model": "WHO",
                    **metrics(y, None, who_pred)})


def train_test(drug, train_mask, test_mask):
    """Drop training isolates that share a transmission cluster with the test set."""
    test_clusters = set(iso.cluster[test_mask])
    train_mask = train_mask & ~iso.cluster.isin(test_clusters).values
    tr, te = np.where(train_mask)[0], np.where(test_mask)[0]
    probs = fit_predict(X_all[tr], iso[drug].values[tr].astype(int), X_all[te])
    return tr, te, probs


for drug in DRUGS:
    t0 = time.time()
    lab = iso[drug].notna().values
    rules = W.resistance_rules(cat, drug)
    who_all = W.predict(tokens, iso.UNIQUEID, rules).values

    # Protocol 1: random grouped 5-fold CV over all known-country isolates.
    idx = np.where(lab & known)[0]
    y = iso[drug].values[idx].astype(int)
    oof = {k: np.zeros(len(idx)) for k in ["LR", "RF", "XGB", "MLP"]}
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    for tr, te in cv.split(idx, y, groups=iso.cluster.values[idx]):
        probs = fit_predict(X_all[idx[tr]], y[tr], X_all[idx[te]])
        for k, p in probs.items():
            oof[k][te] = p
    sa = iso.south_asia.values[idx]
    score(drug, "random", "all", idx, oof, who_all[idx])
    score(drug, "random", "South Asia", idx[sa], {k: v[sa] for k, v in oof.items()}, who_all[idx[sa]])

    # Protocol 2: South Asia holdout.
    test = lab & iso.south_asia.values
    tr, te, probs = train_test(drug, lab & known & ~iso.south_asia.values, test)
    score(drug, "sa_holdout", "South Asia", te, probs, who_all[te])
    pr = iso.iloc[te][["UNIQUEID", "country", "lineage", "sublineage", drug]].rename(columns={drug: "y"})
    pr["drug"], pr["WHO"], pr["n_train"] = drug, who_all[te], len(tr)
    for k, p in probs.items():
        pr[k] = p
    sa_preds.append(pr)

    # Protocol 3: leave one country out.
    counts = iso[lab & known].country.value_counts()
    for country in counts[counts >= MIN_COUNTRY].index:
        test = lab & (iso.country == country).values
        if iso[drug].values[test].sum() < 10:
            continue
        tr, te, probs = train_test(drug, lab & known & ~test, test)
        score(drug, "loco", country, te, probs, who_all[te])

    pd.DataFrame(records).to_csv(RES / "metrics.csv", index=False)
    pd.concat(sa_preds).to_csv(RES / "predictions_sa_holdout.csv", index=False)
    print(f"{drug} done in {time.time() - t0:.0f}s", flush=True)

m = pd.DataFrame(records)
view = m[m.model.isin(["XGB", "WHO"])].pivot_table(
    index=["drug"], columns=["protocol", "test", "model"], values="sensitivity")
print(view.round(3).to_string())
