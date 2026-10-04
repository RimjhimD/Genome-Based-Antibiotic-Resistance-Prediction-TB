# data/

Everything in here is downloaded, not committed. Re-create it with:

```bash
bash scripts/fetch_data.sh              # labels, country, lineage (~6 MB)
bash scripts/fetch_data.sh --mutations  # + mutations, SNP distances, WHO catalogue (~730 MB)
```

Source: CRyPTIC consortium, `https://ftp.ebi.ac.uk/pub/databases/cryptic/release_june2022/`

| Local file | Upstream | Contents |
|---|---|---|
| `cryptic/cryptic_reuse.csv` | `reuse/CRyPTIC_reuse_table_20240917.csv` | 12,287 isolates x 13 drugs: R/S, MIC, quality |
| `cryptic/SAMPLES.csv.gz` | `reproducibility/data_tables/cryptic-analysis-group/` | country, site, collection date |
| `cryptic/MYKROBE_LINEAGE.csv.gz` | same | lineage per isolate |
| `cryptic/COUNTRIES_LOOKUP.csv` | same | country codes |
| `cryptic/DRUG_CODES.csv` | same | drug abbreviations |
| `cryptic/MUTATIONS_GPI.csv.gz` | same | per-genome mutations (feature source) |
| `cryptic/SITES.csv` | same | collecting site to country |
| `cryptic/GPI_SNP_DISTANCES_{LABELS,VALUES}.npy` | same | pairwise SNP distances (transmission clusters) |
| `who/who_2023_v2.csv` | github.com/oxfordmmm/tuberculosis_amr_catalogues | WHO 2023 catalogue, GARC grammar |
| `processed/` | built by `scripts/01`–`03` | isolate table, feature matrix, clusters |

Counts and label balance are in [../docs/03-datasets.md](../docs/03-datasets.md).
