# data/

Everything in here is downloaded, not committed. Re-create it with:

```bash
bash scripts/fetch_data.sh              # labels, country, lineage (~6 MB)
bash scripts/fetch_data.sh --mutations  # + MUTATIONS_GPI.csv.gz (261 MB)
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

Counts and label balance are in [../docs/03-datasets.md](../docs/03-datasets.md).
