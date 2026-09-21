# How the topic was chosen

A record of the search, including the wrong turn, so the reasoning can be defended later.

## The course brief

The course teacher offered these research areas for a 15-day research project, human or
animal:

1. Antibiotic / antimicrobial resistance (AMR) prediction
2. Plant disease detection using computer vision
3. Drug discovery
4. Bioinformatics — analysis of protein sequences

## First pass (2026-09-14): all four assessed

Constraint that shaped everything: the laptop has no NVIDIA GPU and 15 GB RAM.

| Area | For | Against | Verdict then |
|---|---|---|---|
| AMR prediction | Important problem, high AMR burden in Bangladesh, good journals care | Assumed raw genomes = many GB + a bioinformatics pipeline; easy Kaggle tables too simple to publish; strong paper assumed to need hospital data | Good for a full thesis, bad for 15 days |
| Plant disease CV | Easiest start, many datasets incl. Bangladeshi rice/potato/mango leaf sets | Saturated; PlantVillage 99% is partly fake (models learn the uniform background); CPU training slow | Safest to finish, weak for a journal |
| Drug discovery | Ready tools (RDKit, DeepChem, TDC) | Chemistry learning curve; benchmark-chasing crowded; docking claims without lab work only reach weak venues | Skip |
| Protein sequences | Small files, runs on CPU, pretrained protein language models (ESM-2) give a strong baseline fast | Too broad unless narrowed | Best return for effort |

Recommendation then: **antimicrobial peptide (AMP) prediction** from protein sequences.

## The correction (2026-09-19)

AMP prediction answers "does this peptide kill bacteria?" — that is protein sequence
analysis (topic 4), **not** resistance prediction (topic 1). It only touches AMR as
motivation. The mismatch was caught, and topic 1 was re-examined.

The 14 Sep verdict on AMR rested on one assumption: that it needs raw genome assembly.
It does not. The CRyPTIC consortium publishes **precomputed variant tables** alongside
laboratory resistance labels. Mutation table → feature matrix → classifier. No pipeline,
CPU only. With that, AMR prediction became feasible in 15 days, and it is the literal match
to the teacher's first topic.

AMP data had already been verified before the switch (kept for the record):
DRAMP general set 12,784 sequences, antibacterial subset 28,702, anti-Gram-negative 2,562,
specific-target 6,321; UniProt reviewed non-AMP negatives (10–100 aa, excluding keyword
KW-0929) 55,010 available; ESM-2 35M/150M models available and CPU-runnable.

## Narrowing to a publishable gap

- First-line TB drug prediction is saturated (best AUC 99.1% rifampicin, 97.9% isoniazid).
- MIC regression on CRyPTIC is already published (PLOS Comp Biol 2024).
- Broad cross-country transfer has been touched, mainly by US groups (Harvard Farhat lab,
  GenTB; "Geographic heterogeneity impacts drug resistance predictions", 2020).
- **What remains:** models are trained mostly on lineages 2 and 4, while lineages 1 and 3
  dominate South Asia. China built its own national catalogue for this reason; South Asia
  has not. CRyPTIC holds 5,907 isolates from India, Pakistan and Nepal — enough to test it.

## The Bangladesh question

NCBI holds 1,235 public Bangladeshi *M. tuberculosis* genomes, but none of the records
inspected carry a laboratory drug-susceptibility result, and no public paired dataset was
found. Medical data of this kind is not handed over on request. **Decision: the project
promises nothing that depends on Bangladeshi samples.** Local relevance is argued through
the shared lineage 1 and 3 families.

## Final topic (submitted on the selection form)

**Geographic Transportability of Genome-Based Antibiotic Resistance Prediction in
*Mycobacterium tuberculosis*: A South Asian Evaluation**

See [01-topic.md](01-topic.md).
