"""Step 3 - transmission clusters from CRyPTIC's precomputed pairwise SNP distances.

Two isolates within THRESHOLD SNPs are linked if both carry the same single
Mykrobe lineage; clusters are the connected components (single linkage).
Mixed-lineage and unknown-lineage samples are never linked: with them as
bridges, single linkage chained lineage 2 and lineage 4 into one 2,539-isolate
"cluster", which is not a transmission chain. Splits later keep a whole cluster on one side, so
near-identical outbreak strains never sit in both training and test data.

Input  data/cryptic/GPI_SNP_DISTANCES_{LABELS,VALUES}.npy, data/processed/isolates.csv
Output data/processed/clusters.csv   UNIQUEID, cluster, cluster_size
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "cryptic"
OUT = ROOT / "data" / "processed"
THRESHOLD = 12  # SNPs; the usual upper bound for recent transmission in TB

labels = np.load(RAW / "GPI_SNP_DISTANCES_LABELS.npy")
n_all = len(labels)
values = np.load(RAW / "GPI_SNP_DISTANCES_VALUES.npy", mmap_mode="r")
print(f"distance matrix: {values.shape} {values.dtype}, labels {n_all}")
if values.ndim == 1:  # stored flat
    values = values.reshape(n_all, n_all)

isolates = pd.read_csv(OUT / "isolates.csv")
pos = pd.Series(np.arange(n_all), index=labels)
present = isolates.UNIQUEID.isin(pos.index)
print(f"isolates with a distance row: {present.sum()} / {len(isolates)}")

ids = isolates.UNIQUEID[present].to_numpy()
ix = pos[ids].to_numpy()
order = np.argsort(ix)  # read the memory-mapped rows in file order
ix_sorted, ids_sorted = ix[order], ids[order]
lin = isolates.set_index("UNIQUEID").lineage.loc[ids_sorted].to_numpy(dtype=object)
code = pd.factorize(lin)[0]
code[np.isin(lin, ["Mixed", "Unknown"])] = -1

rows, cols = [], []
for start in range(0, len(ix_sorted), 500):
    block = np.asarray(values[ix_sorted[start:start + 500]])[:, ix_sorted]
    r, c = np.nonzero(block <= THRESHOLD)
    keep = ((r + start) < c) & (code[r + start] == code[c]) & (code[c] >= 0)
    rows.append(r[keep] + start)
    cols.append(c[keep])
rows, cols = np.concatenate(rows), np.concatenate(cols)
n = len(ids_sorted)
graph = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
n_comp, comp = connected_components(graph, directed=False)

cl = pd.DataFrame({"UNIQUEID": ids_sorted, "cluster": comp})
# Isolates with no distance row get their own singleton cluster.
missing = isolates.UNIQUEID[~present]
cl = pd.concat([cl, pd.DataFrame({"UNIQUEID": missing,
                                  "cluster": np.arange(n_comp, n_comp + len(missing))})])
cl["cluster_size"] = cl.groupby("cluster").UNIQUEID.transform("size")
cl.to_csv(OUT / "clusters.csv", index=False)

sizes = cl.drop_duplicates("cluster").cluster_size
print(f"clusters: {cl.cluster.nunique()}  singletons: {(sizes == 1).sum()}  "
      f"isolates in clusters of 2+: {(cl.cluster_size > 1).sum()}  largest: {sizes.max()}")

m = cl.merge(isolates[["UNIQUEID", "south_asia", "country"]], on="UNIQUEID")
known = m[m.country != "UNKNOWN"]
mixed = known.groupby("cluster").south_asia.nunique()
print(f"clusters spanning South Asia and elsewhere: {(mixed > 1).sum()}, "
      f"isolates in them: {known.cluster.isin(mixed[mixed > 1].index).sum()}")
