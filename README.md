# Genome-Based Antibiotic Resistance Prediction in Tuberculosis

**Geographic Transportability of Genome-Based Antibiotic Resistance Prediction in
*Mycobacterium tuberculosis*: A South Asian Evaluation**

Internship research project (CSE 4001) · Rimjhim Dey

**Paper:** [report/report.pdf](report/report.pdf) · [Word version](report/report.docx)

---

## The question

Machine learning models can predict antibiotic resistance in *Mycobacterium tuberculosis*
directly from its genome, in days instead of the weeks laboratory drug-susceptibility
testing takes. Their reported accuracy is high — but it is measured on the same kind of
strains they were trained on, and those are mostly **lineages 2 and 4**, which dominate
Europe and East Asia. **Lineages 1 and 3 dominate South Asia**, including Bangladesh.

> Do genome-based resistance models still work on South Asian strains — and if not,
> which resistance mutations do they miss?

## In plain words

TB bacteria become resistant to antibiotics through small changes in their DNA. A computer
model can learn which changes mean resistance and read them off a patient's sample. But TB
comes in families, and the models learned mostly from the families common in rich
countries. Ours are different families. This project trains the model on foreign strains,
tests it on South Asian strains, and measures what breaks.

## Approach

| | |
|---|---|
| **Data** | CRyPTIC consortium — 12,287 clinical isolates, laboratory-confirmed resistance for 13 drugs, precomputed genomic variants, country and lineage metadata |
| **Test set** | 2,162 labelled isolates from India (1,476), Pakistan (489) and Nepal (197) |
| **Features** | Binary matrix of 1,021 mutations in 23 WHO-catalogue resistance genes |
| **Models** | Logistic regression, random forest, gradient boosting, shallow neural network — one per drug |
| **Protocols** | Random split (baseline) · leave-one-country-out · South Asia holdout |
| **Leakage control** | Transmission clusters (≤12 SNPs, same lineage) kept on one side of every split |
| **Benchmark** | WHO mutation catalogue, on the same isolates |
| **Output** | Per-drug accuracy loss, and the resistance mutations missed in lineage 1 and 3 strains |

Everything runs on CPU. No raw sequencing reads are processed.

## Progress

- [x] Topic chosen and submitted — [how and why](docs/00-topic-selection.md)
- [x] Datasets located and verified by download — [details](docs/03-datasets.md)
- [x] Literature reviewed, gap identified — [details](docs/04-literature-and-gap.md)
- [x] Scope and 15-day plan fixed — [details](docs/02-scope-and-plan.md)
- [x] Step 1 — data preparation: join genotype, phenotype, country, lineage — `scripts/01_prepare.py`
- [x] Step 2 — binary mutation feature matrix — `scripts/02_features.py`
- [x] Step 3 — transmission clusters for leakage-safe splits — `scripts/03_clusters.py`
- [x] Step 4 — per-drug models (LR, RF, XGBoost, MLP) — `scripts/04_evaluate.py`
- [x] Step 5 — evaluation across the three protocols + WHO catalogue — `scripts/04_evaluate.py`, `scripts/who_catalogue.py`
- [x] Step 6 — error analysis on South Asian isolates, confusion matrices, lineage-as-feature ablation — `scripts/05_analysis.py`, `scripts/06_lineage_check.py`, `scripts/06b_lineage_feature.py`
- [x] Step 7 — write-up — [report/report.pdf](report/report.pdf) (also `.docx` for Word / Google Docs, and `.html`), built by `scripts/07_report.py`

## Main finding

Aggregate accuracy transfers: AUC on South Asian isolates drops by at most 0.018 when South
Asian isolates are withheld from training. **By lineage it does not.** Resistant lineage 1 and
lineage 3 isolates are detected 11–41 percentage points less often than lineage 2 isolates
(levofloxacin: 53.6% on lineage 1 vs 93.8% on lineage 2). The same deficit appears for models
that did see South Asian data and for the WHO 2023 catalogue, so it reflects missing knowledge of
resistance mechanisms in these lineages, not only where the training data came from. A
region-specific failure: ethambutol resistance in a South Asian lineage 2 group carrying
*embC* A387V / *embB* Q445R, mutations absent or nearly absent among resistant training isolates.

Day-by-day record: [research-log/](research-log/)

## Repository layout

```
.
├── README.md
├── docs/
│   ├── 00-topic-selection.md       how the topic was chosen, including the wrong turn
│   ├── 01-topic.md                 title, form descriptions, plain-language version
│   ├── 02-scope-and-plan.md        15-day plan, out-of-scope list, deliverables
│   ├── 03-datasets.md              every data source, verified counts
│   └── 04-literature-and-gap.md    what is already published, where the gap is
├── research-log/                   one file per working day
├── scripts/
│   ├── fetch_data.sh               re-downloads every dataset used
│   ├── 01_prepare.py … 07_report.py  the pipeline, run in order
│   ├── common.py                   shared model settings
│   ├── check_results.py            sanity checks: counts, leakage, WHO accuracy, report vs metrics
│   └── who_catalogue.py            applies the WHO 2023 catalogue to mutation calls
├── results/                        metrics, tables (CSV), figures (PNG), logs
├── report/                         the written report: PDF, DOCX, HTML
└── data/                           CRyPTIC tables + processed tables; sources in data/README.md
```

## Reproduce

```bash
git clone https://github.com/RimjhimD/Genome-Based-Antibiotic-Resistance-Prediction-TB.git
cd Genome-Based-Antibiotic-Resistance-Prediction-TB
bash scripts/fetch_data.sh --mutations
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # also needs LibreOffice and Google Chrome
for s in 01_prepare 02_features 03_clusters 04_evaluate 05_analysis 06_lineage_check 06b_lineage_feature 07_report; do
  .venv/bin/python scripts/$s.py
done
.venv/bin/python scripts/check_results.py   # 31 checks on the outputs; exits non-zero on failure
```

Tested end to end from a fresh clone in a new environment (Python 3.12, CPU only, 15 GB RAM).
Seeds are fixed: a rerun from a fresh clone reproduced every metric and table in `results/` exactly
(random-forest probabilities differ only at the 16th decimal, from parallel summation).


## Key numbers

```
Isolates with resistance labels   12,287
Drugs                                 13
South Asian isolates with labels   2,162   (India 1,476 · Pakistan 489 · Nepal 197)
Lineages in South Asia             L1 13% · L2 34% · L3 37% · L4 14%
Lineages in the rest               L1  4% · L2 37% · L3  2% · L4 56%
Isoniazid   5,907 R / 6,161 S
Rifampicin  4,683 R / 7,414 S
Bedaquiline   109 R            -> dropped, too few resistant cases
```

## Data source

All data are public; nothing was collected for this project and no patient information is involved.

- **Dataset:** CRyPTIC consortium, data release June 2022 — 12,287 *M. tuberculosis* isolates with
  genome mutation calls and laboratory resistance results for 13 antibiotics.
  Downloaded from the EMBL-EBI public FTP server:
  <https://ftp.ebi.ac.uk/pub/databases/cryptic/release_june2022/>
- **Cite as:** The CRyPTIC Consortium. *A data compendium associating the genomes of 12,289
  Mycobacterium tuberculosis isolates with quantitative resistance phenotypes to 13 antibiotics.*
  PLOS Biology 20(8): e3001721, 2022. <https://doi.org/10.1371/journal.pbio.3001721>
- **Benchmark:** WHO mutation catalogue, 2nd edition (2023), machine-readable version from
  <https://github.com/oxfordmmm/tuberculosis_amr_catalogues>
- **In this repository:** the raw CRyPTIC tables under 100 MB and every processed table the models
  used are in [`data/`](data/). [`data/README.md`](data/README.md) lists each file, its exact
  upstream path, download date and terms of use. The two large files (273 MB and 464 MB) exceed
  GitHub's file limit; `bash scripts/fetch_data.sh --mutations` downloads them.
