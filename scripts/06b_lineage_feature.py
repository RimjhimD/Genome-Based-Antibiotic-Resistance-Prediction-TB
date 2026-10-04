"""Step 6c - ablation: add the isolate's lineage as a feature.

If lineage as a feature lifts random-split scores but not the South Asia
holdout, the model is using strain family as a shortcut rather than learning
resistance. Best model per drug, same splits as 04_evaluate.py.

Output results/table_lineage_feature_ablation.csv
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold

sys.path.insert(0, str(Path(__file__).parent))
from common import DRUGS, SEED, models  # noqa: E402

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
PROC, RES = ROOT / "data" / "processed", ROOT / "results"
LINEAGES = ["Lineage 1", "Lineage 2", "Lineage 3", "Lineage 4"]

iso = pd.read_csv(PROC / "isolates.csv").merge(
    pd.read_csv(PROC / "clusters.csv")[["UNIQUEID", "cluster"]], on="UNIQUEID")
X = sparse.load_npz(PROC / "features_X.npz").tocsr().astype(np.float32)
lin_cols = [(iso.lineage == l).astype(np.float32).values for l in LINEAGES]
lin_cols.append((~iso.lineage.isin(LINEAGES)).astype(np.float32).values)
X_lin = sparse.hstack([X, sparse.csr_matrix(np.column_stack(lin_cols))]).tocsr()
best = pd.read_csv(RES / "table_main.csv").set_index("drug").best_model
known = (iso.country != "UNKNOWN").values
sa_mask = iso.south_asia.values


def fit(Xm, d, tr, te):
    y = iso[d].values[tr].astype(int)
    m = models((y == 0).sum() / max((y == 1).sum(), 1))[best[d]]
    m.fit(Xm[tr], y)
    return m.predict_proba(Xm[te])[:, 1]


rows = []
for d in DRUGS:
    lab = iso[d].notna().values
    idx = np.where(lab & known)[0]
    y = iso[d].values[idx].astype(int)
    test = lab & sa_mask
    train = lab & known & ~sa_mask & ~iso.cluster.isin(set(iso.cluster[test])).values
    tr, te = np.where(train)[0], np.where(test)[0]
    yte = iso[d].values[te].astype(int)
    for name, Xm in [("mutations only", X), ("mutations + lineage", X_lin)]:
        oof = np.zeros(len(idx))
        cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
        for a, b in cv.split(idx, y, groups=iso.cluster.values[idx]):
            oof[b] = fit(Xm, d, idx[a], idx[b])
        p = fit(Xm, d, tr, te)
        row = {"drug": d, "model": best[d], "features": name,
               "auc_random_all": roc_auc_score(y, oof),
               "auc_holdout": roc_auc_score(yte, p),
               "sens_holdout": ((p >= 0.5) & (yte == 1)).sum() / (yte == 1).sum(),
               "spec_holdout": ((p < 0.5) & (yte == 0)).sum() / (yte == 0).sum()}
        for l in ["Lineage 1", "Lineage 3"]:
            r = (iso.lineage.values[te] == l) & (yte == 1)
            row[f"sens_holdout_{l[-1]}"] = (p[r] >= 0.5).mean() if r.sum() >= 10 else np.nan
        rows.append(row)
    print(d, "done", flush=True)

t = pd.DataFrame(rows)
t.round(3).to_csv(RES / "table_lineage_feature_ablation.csv", index=False)
print(t.round(3).to_string(index=False))
