# data/

All data in this project is public. No new data was collected, and no patient data is involved:
every row is a bacterial isolate, identified only by a laboratory code.

## Source

**Primary dataset — CRyPTIC consortium, data release June 2022**

- **Who:** the CRyPTIC Consortium (Comprehensive Resistance Prediction for Tuberculosis: an
  International Consortium).
- **Where:** EMBL-EBI public FTP server —
  <https://ftp.ebi.ac.uk/pub/databases/cryptic/release_june2022/>
- **What:** 12,287 *Mycobacterium tuberculosis* clinical isolates, each with
  whole-genome mutation calls and laboratory-measured resistance (binary resistant/susceptible plus
  MIC) to 13 antibiotics, measured on UKMYC microtitre plates.
- **Paper to cite:** The CRyPTIC Consortium. *A data compendium associating the genomes of 12,289
  Mycobacterium tuberculosis isolates with quantitative resistance phenotypes to 13 antibiotics.*
  PLOS Biology 20(8): e3001721, 2022. <https://doi.org/10.1371/journal.pbio.3001721>
- **Terms of use:** the release README says the `reuse/` data is provided for anyone to use for
  their own purposes, and asks that publications cite the consortium's data paper (above).
- **Downloaded:** 20 September 2026 (labels, samples, lineage, lookups) and 4 October 2026
  (mutations, sites, SNP distances).

**Secondary — WHO mutation catalogue, 2nd edition (2023)**

- World Health Organization. *Catalogue of mutations in Mycobacterium tuberculosis complex and
  their association with drug resistance, 2nd ed.* Geneva: WHO, 2023.
- Used in machine-readable (GARC) form from the Oxford group that also runs CRyPTIC:
  <https://github.com/oxfordmmm/tuberculosis_amr_catalogues>, file
  `catalogues/NC_000962.3/NC_000962.3_WHO-UCN-TB-2023.5_v2.1_GARC1_RFUS.csv`.
- Used only as the benchmark the models are compared against, not for training.

## What is in this folder

### `cryptic/` — raw CRyPTIC tables (committed)

Upstream folder for every file except the first:
`https://ftp.ebi.ac.uk/pub/databases/cryptic/release_june2022/reproducibility/data_tables/cryptic-analysis-group/`

| File | Upstream file | Rows | Contents |
|---|---|---:|---|
| `cryptic_reuse.csv` | [`reuse/CRyPTIC_reuse_table_20240917.csv`](https://ftp.ebi.ac.uk/pub/databases/cryptic/release_june2022/reuse/CRyPTIC_reuse_table_20240917.csv) | 12,287 | one row per isolate: resistant/susceptible, MIC and reading quality for 13 drugs — **the labels** |
| `SAMPLES.csv.gz` | `SAMPLES.csv.gz` | 16,669 | country where each sample was taken, site, collection date |
| `MYKROBE_LINEAGE.csv.gz` | `MYKROBE_LINEAGE.csv.gz` | 70,450 | lineage and sub-lineage of each genome |
| `SITES.csv` | `SITES.csv` | 31 | collecting laboratory → city and country |
| `COUNTRIES_LOOKUP.csv` | `COUNTRIES_LOOKUP.csv` | 243 | country codes |
| `DRUG_CODES.csv` | `DRUG_CODES.csv` | 39 | drug abbreviations (INH = isoniazid, …) |

### Not committed — download with `scripts/fetch_data.sh --mutations`

| File | Size | Why not in GitHub | Contents |
|---|---:|---|---|
| `cryptic/MUTATIONS_GPI.csv.gz` | 273 MB | over GitHub's 100 MB file limit | every mutation in every genome — **the feature source** |
| `cryptic/GPI_SNP_DISTANCES_VALUES.npy` | 464 MB | over the 100 MB limit | pairwise genetic distance between all genomes (for transmission clusters) |
| `cryptic/GPI_SNP_DISTANCES_LABELS.npy` | 3.5 MB | belongs with the file above | row/column names of the distance matrix |
| `who/who_2023_v2.csv` | 1.3 MB | its source repository has no licence, so it is linked rather than copied | WHO 2023 catalogue, GARC format |

### `processed/` — built by the project scripts (committed)

These are the exact tables the models were trained and tested on, so results can be checked
without downloading the large files above.

| File | Built by | Contents |
|---|---|---|
| `isolates.csv` | `scripts/01_prepare.py` | 12,287 isolates: country, South Asia flag, lineage, and a 0/1 label for each of the 8 drugs studied |
| `mutations_long.parquet` | `scripts/02_features.py` | 149,422 quality-filtered mutation calls in the 23 resistance genes — a filtered extract of `MUTATIONS_GPI.csv.gz` |
| `features_X.npz` | `scripts/02_features.py` | the 12,287 × 1,021 binary mutation matrix (sparse) |
| `features_rows.csv`, `features_cols.csv` | `scripts/02_features.py` | isolate IDs and mutation names for the matrix |
| `clusters.csv` | `scripts/03_clusters.py` | transmission cluster of every isolate (≤12 SNPs, same lineage) |

## Re-creating everything

```bash
bash scripts/fetch_data.sh --mutations   # downloads every file listed above (~750 MB)
```

Counts, label balance and lineage make-up are in [../docs/03-datasets.md](../docs/03-datasets.md).
