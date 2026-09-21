# Scope, Work Plan and Deliverables

Tabular work. No images, no labelling by hand, no GPU. Rows are bacterial isolates,
columns are mutations, the answer is resistant / not resistant, per drug.

## Work plan (15 days)

**Step 1 — Data preparation (days 1–4)**
- Download the CRyPTIC label table (12,287 isolates x 13 drugs) and the precomputed
  mutation table.
- Join genotype to phenotype on isolate ID.
- Attach country from `SAMPLES.csv.gz`, lineage from `MYKROBE_LINEAGE.csv.gz`.
- Drop isolates with `NA` or low-quality phenotype flags (there is a quality column per drug).
- Drop drugs with too few resistant cases — bedaquiline has only 109 R, so it goes.
- Keep: isoniazid, rifampicin, ethambutol, levofloxacin, moxifloxacin, ethionamide,
  kanamycin, amikacin.

**Step 2 — Feature building (days 4–6)**
- Binary mutation matrix: 1 if the isolate carries that mutation, else 0.
- Filter rare mutations (seen in fewer than ~5 isolates) to keep the matrix manageable.
- Optionally add lineage as a feature, then run with and without it — shows whether the
  model is memorising strain family instead of learning resistance.

**Step 3 — The split (days 6–7). This is the core of the paper.**
- Train: all isolates NOT from India, Pakistan, Nepal.
- Test: the 5,907 South Asian isolates.
- Baseline comparison: standard random split.
- Also leave-one-country-out, each country separately.
- Control for transmission clustering — near-identical outbreak strains must not sit on
  both sides. This is the TB equivalent of the CD-HIT rule; the leakage here is
  transmission, not sequence homology.

**Step 4 — Models (days 7–10), one set per drug, all CPU-friendly**
- Logistic regression (baseline, and it names which mutation matters)
- Random forest
- XGBoost / gradient boosting
- Shallow neural network, 2–3 dense layers (optional, covers the "deep learning" box)

**Step 5 — Evaluation (days 10–12)**
- Per drug: sensitivity, specificity, AUC, F1.
- Random split vs South Asian holdout, side by side. **The gap is the result.**
- Run the WHO mutation catalogue rules on the same test set and compare.

**Step 6 — Error analysis (days 12–14)**
- Which South Asian isolates were called susceptible but were actually resistant? Those
  are the dangerous errors.
- Which mutations do those isolates carry that the training data lacked?
- Are errors concentrated in lineage 1 and 3?

**Step 7 — Write-up (days 14–15)**

## Out of scope — stated deliberately

- No raw sequencing reads, no genome assembly, no variant-calling pipeline. Precomputed
  variant tables only.
- No new laboratory data collection.
- **No Bangladeshi isolates in this phase.** See [03-datasets.md](03-datasets.md) — the genomes are public but
  their paired lab resistance results are not.
- No clinical deployment, no tool release.
- No drugs with too few resistant cases.

## Deliverables

1. Cleaned, reproducible dataset joining genotype, phenotype, country and lineage.
2. Trained resistance-prediction models for 8+ anti-TB drugs.
3. Results table: per-drug performance, random split vs South Asia holdout vs per-country
   holdout.
4. Comparison against the WHO mutation catalogue on the same isolates.
5. List of resistance mutations under-represented or missed in South Asian strains.
6. Figures: per-drug performance-drop chart, confusion matrices, lineage breakdown of errors.
7. Code on GitHub, reproducible end to end.
8. Written report / draft paper.

## Rule for anything written on a form

Say "I will" only for work that needs no permission from anyone. Never write "I will
collect", "I will obtain", "I will partner with", or "I will validate on Bangladeshi
samples" — each hands someone else control over whether the work finishes.
