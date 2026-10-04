"""Step 1 - join phenotype labels, country and lineage into one isolate table.

Input  data/cryptic/{cryptic_reuse.csv, SAMPLES.csv.gz, SITES.csv, MYKROBE_LINEAGE.csv.gz}
Output data/processed/isolates.csv   one row per isolate, one label column per drug
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "cryptic"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

DRUGS = ["INH", "RIF", "EMB", "ETH", "LEV", "MXF", "KAN", "AMI"]
SOUTH_ASIA = {"IND", "PAK", "NPL"}
# Sites that only collect locally; their country fills gaps in SAMPLES.
# Sites 03 (Gauting) and 06 (Milan) receive isolates from many countries, so a
# missing country there stays unknown.
SINGLE_COUNTRY_SITES = {"02", "04", "05", "08", "10", "11", "14", "17", "20"}

labels = pd.read_csv(RAW / "cryptic_reuse.csv")
samples = pd.read_csv(RAW / "SAMPLES.csv.gz", dtype=str)
sites = pd.read_csv(RAW / "SITES.csv", dtype=str)
lineage = pd.read_csv(RAW / "MYKROBE_LINEAGE.csv.gz")

samples["key"] = "site." + samples.SITEID + ".subj." + samples.SUBJID + ".lab." + samples.LABID
labels["key"] = labels.UNIQUEID.str.replace(r"\.iso\.\d+$", "", regex=True)
labels["site"] = labels.UNIQUEID.str.split(".").str[1]

df = labels.merge(samples[["key", "COUNTRY_WHERE_SAMPLE_TAKEN"]], on="key", how="left")
site_country = sites.set_index("SITEID").COUNTRY_3_LETTER_CODE
fill = df.site.map(site_country).where(df.site.isin(SINGLE_COUNTRY_SITES))
df["country"] = df.COUNTRY_WHERE_SAMPLE_TAKEN.fillna(fill).fillna("UNKNOWN")
df["south_asia"] = df.country.isin(SOUTH_ASIA)

df = df.merge(lineage, on="UNIQUEID", how="left")
df["lineage"] = df.MYKROBE_LINEAGE_NAME_1.fillna("Unknown")
df["sublineage"] = df.MYKROBE_LINEAGE_NAME_2.fillna("Unknown")

# Label per drug: 1 = R, 0 = S. Intermediate (I), missing and LOW-quality
# readings become NaN and the isolate is skipped for that drug only.
for d in DRUGS:
    pheno = df[f"{d}_BINARY_PHENOTYPE"]
    ok = df[f"{d}_PHENOTYPE_QUALITY"].isin(["HIGH", "MEDIUM"]) & pheno.isin(["R", "S"])
    df[d] = np.where(ok, (pheno == "R").astype(float), np.nan)

cols = ["UNIQUEID", "site", "country", "south_asia", "lineage", "sublineage"] + DRUGS
out = df[cols]
out.to_csv(OUT / "isolates.csv", index=False)

print(f"isolates: {len(out)}")
print(f"country unknown: {(out.country == 'UNKNOWN').sum()}")
print("South Asia:", out[out.south_asia].country.value_counts().to_dict(),
      "total", int(out.south_asia.sum()))
print("\nlineage x region")
print(pd.crosstab(out.lineage, out.south_asia.map({True: "South Asia", False: "rest"})))
print("\nlabels per drug (R / S), rest vs South Asia")
for d in DRUGS:
    r = out[~out.south_asia & (out.country != "UNKNOWN")][d]
    s = out[out.south_asia][d]
    print(f"{d}: rest {int((r == 1).sum())}/{int((r == 0).sum())}   "
          f"SA {int((s == 1).sum())}/{int((s == 0).sum())}")
