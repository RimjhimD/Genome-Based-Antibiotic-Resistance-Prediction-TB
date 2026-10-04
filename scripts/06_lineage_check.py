"""Step 6b - is the lineage gap caused by foreign training data, or are those
lineages hard for every method?

For each drug, the best model is re-run under the random grouped CV, its
out-of-fold predictions on South Asian isolates are kept, and sensitivity per
lineage is set beside (a) the South Asia holdout and (b) the WHO catalogue,
which uses no training data at all.

Output results/table_lineage_random_vs_holdout.csv, results/fig_lineage_sensitivity.png
"""
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.model_selection import StratifiedGroupKFold

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
import common as ev  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROC, RES = ROOT / "data" / "processed", ROOT / "results"
DRUGS = ev.DRUGS
LINEAGES = ["Lineage 1", "Lineage 2", "Lineage 3", "Lineage 4"]

iso = pd.read_csv(PROC / "isolates.csv").merge(pd.read_csv(PROC / "clusters.csv")[["UNIQUEID", "cluster"]],
                                               on="UNIQUEID")
X = sparse.load_npz(PROC / "features_X.npz").tocsr().astype(np.float32)
pred = pd.read_csv(RES / "predictions_sa_holdout.csv")
best = pd.read_csv(RES / "table_main.csv").set_index("drug").best_model
known = (iso.country != "UNKNOWN").values

rows = []
for d in DRUGS:
    idx = np.where(iso[d].notna().values & known)[0]
    y = iso[d].values[idx].astype(int)
    oof = np.zeros(len(idx))
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=ev.SEED)
    for tr, te in cv.split(idx, y, groups=iso.cluster.values[idx]):
        pw = (y[tr] == 0).sum() / max((y[tr] == 1).sum(), 1)
        m = ev.models(pw)[best[d]]
        m.fit(X[idx[tr]], y[tr])
        oof[te] = m.predict_proba(X[idx[te]])[:, 1]
    r = iso.iloc[idx].assign(p=oof, y=y)
    r = r[r.south_asia & (r.y == 1)]
    h = pred[(pred.drug == d) & (pred.y == 1)]
    for lin in LINEAGES:
        a, b = r[r.lineage == lin], h[h.lineage == lin]
        if len(b) < 10:
            continue
        rows.append({"drug": d, "lineage": lin, "n_R": len(b),
                     "sens_random": (a.p >= 0.5).mean(), "sens_holdout": (b[best[d]] >= 0.5).mean(),
                     "sens_WHO": b.WHO.mean()})
    print(d, "done", flush=True)

t = pd.DataFrame(rows)
t["drop"] = t.sens_random - t.sens_holdout
t.round(3).to_csv(RES / "table_lineage_random_vs_holdout.csv", index=False)
print(t.round(3).to_string(index=False))

# Figure: small multiples, one panel per drug, lineages on x.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#e4e3df", "grid.linewidth": 0.6,
                     "axes.axisbelow": True, "axes.edgecolor": "#52514e",
                     "xtick.color": "#52514e", "ytick.color": "#52514e", "figure.dpi": 150})
fig, axes = plt.subplots(2, 4, figsize=(10, 5), sharey=True)
for ax, d in zip(axes.flat, DRUGS):
    s = t[t.drug == d].set_index("lineage").reindex(LINEAGES)
    x = np.arange(len(LINEAGES))
    for i, (col, lab, c) in enumerate([("sens_random", "Random split", BLUE),
                                       ("sens_holdout", "South Asia holdout", ORANGE),
                                       ("sens_WHO", "WHO catalogue", AQUA)]):
        ax.bar(x + (i - 1) * 0.27, s[col], width=0.24, color=c, label=lab)
    ax.set_xticks(x, ["L1", "L2", "L3", "L4"])
    ax.set_xlim(-0.6, 3.6)
    ax.set_title(d, loc="left", fontsize=10)
    ax.set_ylim(0, 1.05)
axes[0, 0].set_ylabel("Sensitivity")
axes[1, 0].set_ylabel("Sensitivity")
h, lab = axes[0, 0].get_legend_handles_labels()
fig.legend(h, lab, frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.02))
fig.suptitle("Sensitivity on resistant South Asian isolates, by lineage", x=0.01, ha="left")
fig.tight_layout(rect=(0, 0.05, 1, 1))
fig.savefig(RES / "fig_lineage_sensitivity.png", bbox_inches="tight")
