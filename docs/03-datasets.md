# Datasets — verified 2026-09-19/20

Everything below was checked by actually downloading or querying, not by reading a claim.

## Primary: CRyPTIC (tuberculosis) — open, no registration

Base URL: `https://ftp.ebi.ac.uk/pub/databases/cryptic/release_june2022/`

| File | Size | Contents | Status |
|---|---|---|---|
| `reuse/CRyPTIC_reuse_table_20240917.csv` | 5.4 MB | 12,287 isolates x 13 drugs, binary R/S + MIC + quality flag | **in `data/cryptic/`** |
| `reproducibility/data_tables/cryptic-analysis-group/MUTATIONS_GPI.csv.gz` | 261 MB | precomputed per-genome mutations — no pipeline needed | verified, not yet pulled |
| `.../MUTATIONS.csv.gz` | 1.4 GB | full variant table | verified |
| `.../SAMPLES.csv.gz` | 250 KB | country, site, collection date, smear, HIV | **in `data/cryptic/`** |
| `.../MYKROBE_LINEAGE.csv.gz` | 518 KB | lineage per isolate, 70,450 rows | **in `data/cryptic/`** |
| `.../COUNTRIES_LOOKUP.csv`, `DRUG_CODES.csv` | small | lookups | **in `data/cryptic/`** |
| per-sample masked VCF | ~25 KB each, ~300 MB total | fallback if the mutation table disappoints | one verified |

### Label balance, counted from the file

```
INH  5,907 R / 6,161 S / 218 NA      RIF  4,683 R / 7,414 S / 188 NA
EMB  2,261 R / 1,559 I / 8,336 S     LEV  2,145 R / 10,016 S
BDQ    109 R / 11,957 S  <- too rare, drop this drug
```

### Country spread, from `SAMPLES.csv.gz` (16,669 rows)

```
IND 5085   PER 3451   ZAF 2272   CHN 1535   VNM 1112
DEU  851   ITA  538   PAK  519   BRA  404   NPL  303
TKM  258   SWE  102   BFA   78   NGA   33   UKR   30
```

India + Pakistan + Nepal = 5,907 *samples* in `SAMPLES.csv.gz`. **Correction (2026-10-04):**
that counts every sample, labelled or not. Isolates that also carry a resistance phenotype in the
reuse table number **2,162** (India 1,476 · Pakistan 489 · Nepal 197), after filling missing
countries from single-country sites. That is the real test set.
Note: no USA isolates in CRyPTIC.

### Lineages

```
L4 35,465   L2 18,217   L3 8,416   L1 5,812   Mixed 1,077
```
L1 and L3 are the South Asian families, and the ones under-represented in training data
worldwide.

## Secondary, all live

- **BV-BRC AMR API** — `https://www.bv-brc.org/api/genome_amr/` — 2,519,349 phenotype
  records, many species. Works, tested. Genomes are the heavy part.
- **CARD** — `https://card.mcmaster.ca/latest/data` — reference resistance-gene database.
- **NCBI eutils** — used for the counts below.

## Rejected

- **DRIAMS (MALDI-TOF)** — 144.8 GB on Dryad. Laptop has 107 GB free. Dead.

## Bangladesh — read this before promising anything

- NCBI holds **1,235 Bangladeshi *M. tuberculosis* BioSamples / 1,268 SRA runs**, public.
- Opened five records directly: they carry country, strain, isolation source — **no
  drug-susceptibility phenotype**. DNA without the lab answer cannot train a model.
- Searched for a public Bangladeshi dataset pairing genome with lab resistance result:
  **none found.** icddr,b studies did run the lab testing (LJ proportion method, INH/RIF/
  EMB/STR/ETH/KAN/OFX) but no paired release was located.
- Also in NCBI from Bangladesh, if the topic ever shifts: E. coli 4,699 · Klebsiella
  pneumoniae 2,454 · S. Typhi 680.

**Consequence:** the project must not depend on Bangladeshi samples. India, Pakistan and
Nepal carry the same lineage 1 and 3 families, and that data is already in hand. Local
relevance is argued through lineage, not through local sampling.

## Rejected alternative topic (kept for the record)

**Antimicrobial peptide (AMP) prediction** — the 14 Sep pick, before AMR was confirmed
feasible. Data verified working: DRAMP general 12,784 seqs, antibacterial subset 28,702,
anti-Gram-negative 2,562, specific-target 6,321; UniProt reviewed negatives 10–100 aa
excluding KW-0929 = 55,010 available; ESM-2 35M/150M on HuggingFace, CPU-runnable.
Dropped because it is *antimicrobial peptide* prediction, not *antimicrobial resistance*
prediction — it does not match what the teacher asked for.
