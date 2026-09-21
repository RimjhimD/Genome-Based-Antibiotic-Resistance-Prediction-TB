# Thesis Course — Topic Selection

**Chosen topic, submitted on the topic-selection form (2026-09-19/20).**

## Title

**Geographic Transportability of Genome-Based Antibiotic Resistance Prediction in
*Mycobacterium tuberculosis*: A South Asian Evaluation**

Short form, for small fields:

> Testing Genome-Based Tuberculosis Drug-Resistance Prediction Models on South Asian Strains

**Keywords:** antimicrobial resistance · tuberculosis · whole-genome sequencing ·
machine learning · model generalization · South Asia

---

## Description — first person, full

Antibiotic resistance in tuberculosis is normally confirmed by laboratory
drug-susceptibility testing, which takes weeks. Machine learning models can predict it
from the bacterial genome in days, but these models are trained mostly on lineages 2 and
4, which dominate Europe and East Asia, while lineages 1 and 3 predominate in South Asia.
Whether their reported accuracy holds on these strains has not been established.

For this research I will use the public CRyPTIC dataset, which provides genomic variant
tables and laboratory-confirmed resistance labels for 12,287 clinical isolates across 13
anti-tuberculosis drugs.

I will clean and integrate the genotype, phenotype, country and lineage data, and build a
binary mutation feature matrix. I will train resistance-prediction models — logistic
regression, random forest, gradient boosting, and a shallow neural network — separately
for each drug that has enough resistant cases. I will then evaluate them under three
protocols: a standard random split, a leave-one-country-out split, and a South Asia
holdout in which the models are trained only on non-South-Asian isolates and tested on the
5,907 isolates from India, Pakistan and Nepal. Splits will be controlled for lineage and
transmission clustering so that closely related isolates cannot appear in both training
and test sets.

I will report the per-drug accuracy loss between these protocols, benchmark the models
against the WHO mutation catalogue, and identify resistance mutations that are missed in
lineage 1 and lineage 3 strains. The strain families studied are those that predominate in
Bangladesh, making the findings relevant to the national tuberculosis context.

## Description — short (~120 words)

Machine learning models can predict tuberculosis antibiotic resistance from the bacterial
genome in days, replacing laboratory testing that takes weeks. But these models are trained
mostly on lineages 2 and 4, which dominate Europe and East Asia, while lineages 1 and 3
predominate in South Asia.

For this research I will use the public CRyPTIC dataset — 12,287 clinical isolates with
genomic variants and laboratory-confirmed resistance labels for 13 anti-tuberculosis drugs.
I will build a mutation feature matrix, train per-drug classifiers, and test them on the
5,907 South Asian isolates after training only on non-South-Asian ones, with splits
controlled for lineage and transmission clustering. I will report the per-drug accuracy
loss, benchmark against the WHO mutation catalogue, and identify mutations missed in
lineage 1 and 3 strains.

## Description — shortest (~60 words)

Machine learning can predict tuberculosis drug resistance from the bacterial genome, but
existing models are trained mainly on European and East Asian strains. Using the public
CRyPTIC dataset of 12,287 isolates, I will train per-drug resistance classifiers on
non-South-Asian isolates, test them on 5,907 South Asian isolates, measure the accuracy
loss per drug, and identify the resistance mutations they miss.

## Viva one-liner

> "Resistance-prediction models were trained on foreign TB strains. I'm testing whether
> they still work on South Asian strains — and if not, why."

---

## Plain-language version

TB is a bacterial lung disease, common in Bangladesh. Antibiotics treat it, but sometimes
the bacteria are **resistant** and the drug does nothing. Finding out the old way means
growing the bacteria in a dish with the drug — that takes weeks while the patient waits.

The new way: read the bacteria's DNA. Resistance comes from **mutations**, small typos in
the DNA. Certain typos mean resistance to a certain drug. A computer model learns which
typos matter, and answers in days.

The problem: TB bacteria come in families called **lineages**. Lineage 2 and 4 dominate
Europe and China. **Lineage 1 and 3 dominate South Asia — India, Pakistan, Nepal,
Bangladesh.** Almost every model was trained on lineage 2 and 4 DNA, because that is the
data rich countries had. A different family may carry different typos. A model that never
saw them could call a patient's TB treatable when it is not. Nobody has properly checked
this for our region.

What I do: train the model only on foreign isolates, test it only on South Asian isolates,
measure how much worse it gets per drug, and find the typos it missed.
