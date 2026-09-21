# Genome-Based Antibiotic Resistance Prediction in Tuberculosis

**Geographic Transportability of Genome-Based Antibiotic Resistance Prediction in
*Mycobacterium tuberculosis*: A South Asian Evaluation**

Thesis Course research project · Rimjhim Dey

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
| **Test set** | 5,907 isolates from India, Pakistan and Nepal |
| **Features** | Binary mutation matrix (mutation present / absent per isolate) |
| **Models** | Logistic regression, random forest, gradient boosting, shallow neural network — one per drug |
| **Protocols** | Random split (baseline) · leave-one-country-out · South Asia holdout |
| **Leakage control** | Splits aware of lineage and transmission clustering, so near-identical strains never sit on both sides |
| **Benchmark** | WHO mutation catalogue, on the same isolates |
| **Output** | Per-drug accuracy loss, and the resistance mutations missed in lineage 1 and 3 strains |

Everything runs on CPU. No raw sequencing reads are processed.

## Progress

- [x] Topic chosen and submitted — [how and why](docs/00-topic-selection.md)
- [x] Datasets located and verified by download — [details](docs/03-datasets.md)
- [x] Literature reviewed, gap identified — [details](docs/04-literature-and-gap.md)
- [x] Scope and 15-day plan fixed — [details](docs/02-scope-and-plan.md)
- [ ] Step 1 — data preparation: join genotype, phenotype, country, lineage
- [ ] Step 2 — binary mutation feature matrix
- [ ] Step 3 — lineage- and cluster-aware splits
- [ ] Step 4 — per-drug models
- [ ] Step 5 — evaluation across the three protocols + WHO catalogue
- [ ] Step 6 — error analysis on South Asian isolates
- [ ] Step 7 — write-up

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
│   └── fetch_data.sh               re-downloads every dataset used
└── data/                           downloaded data (not committed) — see data/README.md
```

## Reproduce

```bash
git clone https://github.com/RimjhimD/Genome-Based-Antibiotic-Resistance-Prediction-TB.git
cd Genome-Based-Antibiotic-Resistance-Prediction-TB
bash scripts/fetch_data.sh --mutations
```

## Key numbers so far

```
Isolates with resistance labels   12,287
Drugs                                 13
South Asian test isolates          5,907   (India 5,085 · Pakistan 519 · Nepal 303)
Lineage 1 / Lineage 3 records      5,812 / 8,416
Isoniazid   5,907 R / 6,161 S
Rifampicin  4,683 R / 7,414 S
Bedaquiline   109 R            -> dropped, too few resistant cases
```

## Data source

The CRyPTIC Consortium. *A data compendium associating the genomes of 12,289
Mycobacterium tuberculosis isolates with quantitative resistance phenotypes to 13
antibiotics.* PLOS Biology 20(8), 2022. doi:10.1371/journal.pbio.3001721. Data:
<https://ftp.ebi.ac.uk/pub/databases/cryptic/release_june2022/>
