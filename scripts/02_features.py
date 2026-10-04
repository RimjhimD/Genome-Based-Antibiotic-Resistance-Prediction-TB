"""Step 2 - binary mutation feature matrix over WHO-catalogue resistance genes.

Input  data/cryptic/MUTATIONS_GPI.csv.gz, data/who/who_2023_v2.csv,
       data/processed/isolates.csv
Output data/processed/mutations_long.parquet   filtered calls, one row per isolate x mutation
       data/processed/features.npz             sparse 0/1 matrix + row ids + column names
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "cryptic"
OUT = ROOT / "data" / "processed"

DRUGS = ["INH", "RIF", "EMB", "ETH", "LEV", "MXF", "KAN", "AMI"]
MIN_ISOLATES = 3  # drop mutations carried by fewer isolates than this

# Candidate genes = WHO 2023 catalogue tier 1 and 2 genes for our eight drugs.
genes = {
    "rpoB", "rpoA", "rpoC",                                  # RIF
    "katG", "inhA", "fabG1", "ahpC", "mshA", "ndh", "kasA",  # INH (inhA, fabG1, mshA also ETH)
    "embB", "embA", "embC", "embR", "ubiA",                  # EMB
    "ethA", "ethR",                                          # ETH
    "gyrA", "gyrB",                                          # LEV, MXF
    "rrs", "eis", "whiB7", "tlyA",                           # KAN, AMI
}
print(f"candidate genes ({len(genes)}):", sorted(genes))

isolates = pd.read_csv(OUT / "isolates.csv")
keep_ids = set(isolates.UNIQUEID)

cols = ["UNIQUEID", "GENE", "MUTATION", "IS_INDEL", "IS_SYNONYMOUS",
        "IS_HET", "IS_NULL", "IS_FILTER_PASS", "INDEL_LENGTH", "INDEL_2"]
parts = []
for chunk in pd.read_csv(RAW / "MUTATIONS_GPI.csv.gz", usecols=cols, chunksize=2_000_000,
                         dtype={"GENE": "category"}):
    c = chunk[chunk.GENE.isin(genes) & chunk.UNIQUEID.isin(keep_ids)]
    c = c[c.IS_FILTER_PASS & ~c.IS_NULL & ~c.IS_HET]
    parts.append(c)
    print(".", end="", flush=True)
calls = pd.concat(parts, ignore_index=True)
calls["GENE"] = calls.GENE.astype(str)
print(f"\ncalls kept: {len(calls)}")

# Feature name: gene_mutation for SNPs (e.g. rpoB_S450L, fabG1_c-15t),
# gene_pos_ins/del_len for indels (bases are not given in the table).
calls["feature"] = np.where(calls.IS_INDEL,
                            calls.GENE + "_" + calls.INDEL_2.astype(str),
                            calls.GENE + "_" + calls.MUTATION)
calls["frameshift"] = calls.IS_INDEL & (calls.INDEL_LENGTH.abs() % 3 != 0)
calls["stop"] = ~calls.IS_INDEL & calls.MUTATION.str.endswith("!")
calls.to_parquet(OUT / "mutations_long.parquet", index=False)  # synonymous kept for WHO rules

# Synonymous changes are dropped from the features, except in fabG1: fabG1 L203L
# creates an alternative inhA promoter and is a graded WHO resistance mutation.
calls = calls[~calls.IS_SYNONYMOUS | (calls.GENE == "fabG1")]

# Gene-level loss-of-function: any frameshift or premature stop in the gene.
lof = calls[calls.frameshift | calls.stop][["UNIQUEID", "GENE"]].drop_duplicates()
lof = lof.assign(feature=lof.GENE + "_LoF")[["UNIQUEID", "feature"]]
pairs = pd.concat([calls[["UNIQUEID", "feature"]], lof]).drop_duplicates()

counts = pairs.feature.value_counts()
vocab = sorted(counts[counts >= MIN_ISOLATES].index)
pairs = pairs[pairs.feature.isin(vocab)]

row_ids = isolates.UNIQUEID.tolist()
row_ix = {u: i for i, u in enumerate(row_ids)}
col_ix = {f: j for j, f in enumerate(vocab)}
X = sparse.csr_matrix((np.ones(len(pairs), dtype=np.int8),
                       (pairs.UNIQUEID.map(row_ix), pairs.feature.map(col_ix))),
                      shape=(len(row_ids), len(vocab)))
sparse.save_npz(OUT / "features_X.npz", X)
pd.Series(vocab, name="feature").to_csv(OUT / "features_cols.csv", index=False)
pd.Series(row_ids, name="UNIQUEID").to_csv(OUT / "features_rows.csv", index=False)

print(f"matrix: {X.shape[0]} isolates x {X.shape[1]} mutations, {X.nnz} non-zero")
print(f"isolates with no candidate-gene mutation: {(X.getnnz(axis=1) == 0).sum()}")
print("most common:", counts.head(15).to_dict())
