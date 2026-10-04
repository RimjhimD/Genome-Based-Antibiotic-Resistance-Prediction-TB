"""Step 6 - result tables, error analysis on South Asian isolates, figures.

Input  results/metrics.csv, results/predictions_sa_holdout.csv,
       data/processed/{isolates.csv, mutations_long.parquet}
Output results/table_*.csv, results/missed_mutations.csv, results/fig_*.png
"""
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
PROC = ROOT / "data" / "processed"
DRUGS = ["INH", "RIF", "EMB", "ETH", "LEV", "MXF", "KAN", "AMI"]
MODELS = ["LR", "RF", "XGB", "MLP"]

# Reference palette, first three categorical slots (validated all-pairs).
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "figure.dpi": 150,
})

m = pd.read_csv(RES / "metrics.csv")
pred = pd.read_csv(RES / "predictions_sa_holdout.csv")
iso = pd.read_csv(PROC / "isolates.csv")

# ---- Table 1: every model, random CV (South Asian subset) vs SA holdout ----------
cols = ["sensitivity", "specificity", "auc", "f1"]
t1 = m[m.test == "South Asia"].pivot_table(index=["drug", "model"], columns="protocol",
                                           values=cols)
t1 = t1.reindex(DRUGS, level=0)
t1.round(3).to_csv(RES / "table_all_models.csv")

# Best ML model per drug chosen on random-CV AUC (all isolates), so the choice
# never looks at the South Asian holdout.
rnd = m[(m.protocol == "random") & (m.test == "all") & m.model.isin(MODELS)]
best = rnd.loc[rnd.groupby("drug").auc.idxmax()].set_index("drug").model.reindex(DRUGS)

rows = []
for d in DRUGS:
    b = best[d]
    get = lambda proto, model, col: m[(m.drug == d) & (m.protocol == proto) &  # noqa: E731
                                      (m.test == "South Asia") & (m.model == model)][col].item()
    rows.append({
        "drug": d, "best_model": b,
        "n_SA": get("sa_holdout", b, "n"), "n_R_SA": get("sa_holdout", b, "n_R"),
        "sens_random": get("random", b, "sensitivity"),
        "sens_holdout": get("sa_holdout", b, "sensitivity"),
        "spec_random": get("random", b, "specificity"),
        "spec_holdout": get("sa_holdout", b, "specificity"),
        "auc_random": get("random", b, "auc"), "auc_holdout": get("sa_holdout", b, "auc"),
        "sens_WHO": get("sa_holdout", "WHO", "sensitivity"),
        "spec_WHO": get("sa_holdout", "WHO", "specificity"),
    })
t2 = pd.DataFrame(rows)
t2["sens_drop"] = t2.sens_random - t2.sens_holdout
t2["auc_drop"] = t2.auc_random - t2.auc_holdout
t2.round(3).to_csv(RES / "table_main.csv", index=False)
print("MAIN TABLE (South Asian isolates; best model per drug chosen on random-CV AUC)")
print(t2.round(3).to_string(index=False))

# ---- Table 3: leave-one-country-out AUC, best model --------------------------------
loco = m[(m.protocol == "loco")]
loco_b = loco[loco.apply(lambda r: r.model == best[r.drug], axis=1)]
t3 = loco_b.pivot_table(index="test", columns="drug", values="auc")[DRUGS]
t3s = loco_b.pivot_table(index="test", columns="drug", values="sensitivity")[DRUGS]
t3.round(3).to_csv(RES / "table_loco_auc.csv")
t3s.round(3).to_csv(RES / "table_loco_sensitivity.csv")
print("\nLEAVE-ONE-COUNTRY-OUT AUC (best model)")
print(t3.round(3).to_string())
print("\nLEAVE-ONE-COUNTRY-OUT sensitivity (best model)")
print(t3s.round(3).to_string())

# ---- Table 4: SA holdout sensitivity by lineage ------------------------------------
lin_rows = []
for d in DRUGS:
    p = pred[(pred.drug == d) & (pred.y == 1)]
    for lin, g in p.groupby("lineage"):
        if len(g) < 10:
            continue
        lin_rows.append({"drug": d, "lineage": lin, "n_R": len(g),
                         "sens_model": (g[best[d]] >= 0.5).mean(), "sens_WHO": g.WHO.mean()})
t4 = pd.DataFrame(lin_rows)
t4.round(3).to_csv(RES / "table_lineage_sensitivity.csv", index=False)
print("\nSA HOLDOUT SENSITIVITY BY LINEAGE")
print(t4.pivot_table(index="drug", columns="lineage", values="sens_model").reindex(DRUGS)
      .round(3).to_string())

# ---- Missed resistance: which mutations do the missed SA isolates carry? -----------
calls = pd.read_parquet(PROC / "mutations_long.parquet")
calls = calls[~calls.IS_SYNONYMOUS | (calls.GENE == "fabG1")]
DRUG_GENES = {
    "INH": ["katG", "inhA", "fabG1", "ahpC", "mshA", "ndh", "kasA"],
    "RIF": ["rpoB", "rpoA", "rpoC"], "EMB": ["embB", "embA", "embC", "embR", "ubiA"],
    "ETH": ["ethA", "ethR", "inhA", "fabG1", "mshA"], "LEV": ["gyrA", "gyrB"],
    "MXF": ["gyrA", "gyrB"], "KAN": ["rrs", "eis", "whiB7", "tlyA"],
    "AMI": ["rrs", "eis", "whiB7", "tlyA"],
}
nonsa = iso[~iso.south_asia & (iso.country != "UNKNOWN")]
miss_rows, summary = [], []
for d in DRUGS:
    p = pred[pred.drug == d]
    missed = p[(p.y == 1) & (p[best[d]] < 0.5)].UNIQUEID
    caught = p[(p.y == 1) & (p[best[d]] >= 0.5)].UNIQUEID
    c = calls[calls.GENE.isin(DRUG_GENES[d])]
    train_r = set(nonsa[nonsa[d] == 1].UNIQUEID)
    train_s = set(nonsa[nonsa[d] == 0].UNIQUEID)
    cm = c[c.UNIQUEID.isin(missed)]
    no_mut = len(set(missed) - set(cm.UNIQUEID))
    summary.append({"drug": d, "missed_R": len(missed), "caught_R": len(caught),
                    "missed_with_no_candidate_mutation": no_mut,
                    "missed_also_missed_by_WHO": int((p[p.UNIQUEID.isin(missed)].WHO == 0).sum())})
    for feat, g in cm.groupby("feature"):
        n_tr_r = c[(c.feature == feat) & c.UNIQUEID.isin(train_r)].UNIQUEID.nunique()
        n_tr_s = c[(c.feature == feat) & c.UNIQUEID.isin(train_s)].UNIQUEID.nunique()
        miss_rows.append({"drug": d, "mutation": feat, "missed_SA_isolates": g.UNIQUEID.nunique(),
                          "lineages": ",".join(sorted(iso.set_index("UNIQUEID").lineage
                                                      .loc[g.UNIQUEID.unique()].unique())),
                          "train_R_carriers": n_tr_r, "train_S_carriers": n_tr_s})
mm = pd.DataFrame(miss_rows).sort_values(["drug", "missed_SA_isolates"], ascending=[True, False])
mm.to_csv(RES / "missed_mutations.csv", index=False)
ms = pd.DataFrame(summary)
ms.to_csv(RES / "table_missed_summary.csv", index=False)
print("\nMISSED RESISTANT SOUTH ASIAN ISOLATES")
print(ms.to_string(index=False))
print("\nTOP MUTATIONS IN MISSED ISOLATES (rare or absent among resistant training isolates)")
rare = mm[(mm.missed_SA_isolates >= 3) & (mm.train_R_carriers < 10)]
print(rare.groupby("drug").head(5).to_string(index=False))

# ---- Figure 1: sensitivity, random CV vs SA holdout vs WHO -------------------------
x = np.arange(len(DRUGS))
w = 0.26
fig, ax = plt.subplots(figsize=(8, 3.8))
for i, (col, lab, color) in enumerate([("sens_random", "Random split (South Asian isolates)", BLUE),
                                       ("sens_holdout", "South Asia holdout", ORANGE),
                                       ("sens_WHO", "WHO 2023 catalogue", AQUA)]):
    ax.bar(x + (i - 1) * w, t2[col], width=w - 0.03, color=color, label=lab)
ax.set_xticks(x, DRUGS)
ax.set_ylim(0, 1.05)
ax.set_ylabel("Sensitivity (resistant cases found)")
ax.set_title("Sensitivity on South Asian isolates by evaluation protocol", loc="left", color=INK)
ax.legend(frameon=False, ncol=3, loc="lower left", bbox_to_anchor=(0, -0.28), fontsize=8.5)
fig.tight_layout()
fig.savefig(RES / "fig_sensitivity_protocols.png", bbox_inches="tight")

# ---- Figure 2: AUC drop per drug ---------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 3.4))
for i, (col, lab, color) in enumerate([("auc_random", "Random split (South Asian isolates)", BLUE),
                                       ("auc_holdout", "South Asia holdout", ORANGE)]):
    ax.bar(x + (i - 0.5) * 0.36, t2[col], width=0.33, color=color, label=lab)
ax.set_xticks(x, DRUGS)
lo = max(0.5, np.floor(t2[["auc_random", "auc_holdout"]].min().min() * 20) / 20 - 0.05)
ax.set_ylim(lo, 1.0)
ax.set_ylabel("AUC")
ax.set_title("AUC on South Asian isolates: seen-region vs unseen-region training", loc="left",
             color=INK)
ax.legend(frameon=False, ncol=2, loc="lower left", bbox_to_anchor=(0, -0.28), fontsize=8.5)
fig.tight_layout()
fig.savefig(RES / "fig_auc_protocols.png", bbox_inches="tight")

# ---- Figure 3: LOCO sensitivity heatmap (sequential blue) --------------------------
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

seq = LinearSegmentedColormap.from_list("blue", ["#cde2fb", "#6da7ec", "#256abf", "#0d366b"])
fig, ax = plt.subplots(figsize=(7.5, 0.42 * len(t3s) + 1.2))
im = ax.imshow(t3s.values, cmap=seq, vmin=0.0, vmax=1.0, aspect="auto")
ax.set_xticks(range(len(DRUGS)), DRUGS)
ax.set_yticks(range(len(t3s)), t3s.index)
ax.grid(False)
for i in range(t3s.shape[0]):
    for j in range(t3s.shape[1]):
        v = t3s.values[i, j]
        if not np.isnan(v):
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8,
                    color="white" if v > 0.55 else INK)
ax.set_title("Leave-one-country-out sensitivity (held-out country)", loc="left", color=INK)
fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
fig.tight_layout()
fig.savefig(RES / "fig_loco_sensitivity.png", bbox_inches="tight")

# ---- Figure 4: lineage make-up, South Asia vs rest ---------------------------------
known = iso[iso.country != "UNKNOWN"].copy()
known["region"] = np.where(known.south_asia, "South Asia\n(test)", "Rest of world\n(training)")
lin_order = ["Lineage 1", "Lineage 2", "Lineage 3", "Lineage 4"]
known["lin"] = known.lineage.where(known.lineage.isin(lin_order), "Other / mixed")
share = pd.crosstab(known.region, known.lin, normalize="index")[lin_order + ["Other / mixed"]]
colors = [BLUE, "#eda100", ORANGE, AQUA, "#b9b8b3"]
fig, ax = plt.subplots(figsize=(7.5, 2.4))
left = np.zeros(len(share))
for lin, color in zip(share.columns, colors):
    ax.barh(share.index, share[lin], left=left, color=color, label=lin,
            edgecolor="white", linewidth=1.5)
    for k, v in enumerate(share[lin]):
        if v > 0.06:
            ax.text(left[k] + v / 2, k, f"{v:.0%}", ha="center", va="center", fontsize=8,
                    color=INK)
    left += share[lin].values
ax.set_xlim(0, 1)
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
ax.grid(False)
ax.set_title("Lineage composition of labelled isolates", loc="left", color=INK)
ax.legend(frameon=False, ncol=5, loc="lower left", bbox_to_anchor=(0, -0.45), fontsize=8)
fig.tight_layout()
fig.savefig(RES / "fig_lineage_composition.png", bbox_inches="tight")
print("\nfigures written to results/")

# ---- Figure 5: confusion matrices, South Asia holdout, best model per drug ---------
conf_rows = []
fig, axes = plt.subplots(2, 4, figsize=(10, 5.2))
for ax, d in zip(axes.flat, DRUGS):
    p = pred[pred.drug == d]
    y, yhat = p.y.astype(int).values, (p[best[d]] >= 0.5).astype(int).values
    cm = np.array([[((y == 1) & (yhat == 1)).sum(), ((y == 1) & (yhat == 0)).sum()],
                   [((y == 0) & (yhat == 1)).sum(), ((y == 0) & (yhat == 0)).sum()]])
    conf_rows.append({"drug": d, "model": best[d], "TP": cm[0, 0], "FN": cm[0, 1],
                      "FP": cm[1, 0], "TN": cm[1, 1]})
    share_row = cm / cm.sum(axis=1, keepdims=True)
    ax.imshow(share_row, cmap=seq, vmin=0, vmax=1)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm[i, j]:,}\n{share_row[i, j]:.0%}", ha="center", va="center",
                    fontsize=8.5, color="white" if share_row[i, j] > 0.55 else INK)
    ax.set_xticks([0, 1], ["Pred R", "Pred S"])
    ax.set_yticks([0, 1], ["True R", "True S"])
    ax.grid(False)
    ax.set_title(f"{d} ({best[d]})", loc="left", fontsize=10)
fig.suptitle("Confusion matrices, South Asia holdout (row percentages)", x=0.01, ha="left")
fig.tight_layout()
fig.savefig(RES / "fig_confusion_matrices.png", bbox_inches="tight")
pd.DataFrame(conf_rows).to_csv(RES / "table_confusion.csv", index=False)
print("\nCONFUSION (South Asia holdout, best model)")
print(pd.DataFrame(conf_rows).to_string(index=False))
