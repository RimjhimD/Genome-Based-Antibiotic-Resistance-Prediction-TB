#!/usr/bin/env bash
# Download the CRyPTIC tables this project uses into data/cryptic/.
# Usage: bash scripts/fetch_data.sh [--mutations]
#   --mutations  also fetch MUTATIONS_GPI.csv.gz (261 MB), the feature source
set -euo pipefail

BASE="https://ftp.ebi.ac.uk/pub/databases/cryptic/release_june2022"
TABLES="$BASE/reproducibility/data_tables/cryptic-analysis-group"
OUT="$(cd "$(dirname "$0")/.." && pwd)/data/cryptic"
mkdir -p "$OUT"

fetch() {  # fetch <url> <local-name>
  if [[ -s "$OUT/$2" ]]; then
    echo "have  $2"
  else
    echo "get   $2"
    curl -fL --retry 3 --max-time 3600 -o "$OUT/$2.part" "$1"
    mv "$OUT/$2.part" "$OUT/$2"
  fi
}

fetch "$BASE/reuse/CRyPTIC_reuse_table_20240917.csv" cryptic_reuse.csv
fetch "$TABLES/SAMPLES.csv.gz"         SAMPLES.csv.gz
fetch "$TABLES/MYKROBE_LINEAGE.csv.gz" MYKROBE_LINEAGE.csv.gz
fetch "$TABLES/COUNTRIES_LOOKUP.csv"   COUNTRIES_LOOKUP.csv
fetch "$TABLES/DRUG_CODES.csv"         DRUG_CODES.csv

if [[ "${1:-}" == "--mutations" ]]; then
  fetch "$TABLES/MUTATIONS_GPI.csv.gz" MUTATIONS_GPI.csv.gz
fi

echo "done -> $OUT"
