# State of the field, and where the gap is

Searched 2026-09-19/20. The point of this file: know what is already taken, so the claim
made in the thesis survives a reviewer.

## What is already solved — do not claim it

- **First-line drugs are done.** Best published models reach AUC 99.1% rifampicin, 97.9%
  isoniazid. 13 of 18 models report >=90% sensitivity on isoniazid. Another CNN on INH/RIF
  is an instant reject.
- **WHO mutation catalogue** v1 2021, v2 2023 — the clinical standard. TB-Profiler and
  Mykrobe are the standard tools.
- **MIC regression is taken.** PLOS Comp Biol 2024 did 13 drugs on 10,859 CRyPTIC isolates,
  >=90% essential agreement. Usable as a feature, not as the headline claim.
- **2026 is benchmark year.** A July 2026 translational benchmark (bioRxiv) and TB-Bench
  (April 2026, second-line drugs) both landed. A BMC systematic review covering 15 studies
  / 20 models also 2026.
- **US work is heavy.** Harvard Farhat lab's GenTB (RF + wide-and-deep net, 13 drugs,
  benchmarked on 20,408 isolates). The same group published "Geographic heterogeneity
  impacts drug resistance predictions in M. tuberculosis" (bioRxiv 2020) — closest prior
  work to this project. USA also holds 67,574 Mtb genomes in NCBI vs India's 13,740.
- **Lineage bias is known and half-treated.** FW-RF (Bioinformatics 2023) reweights
  features for lineage dependency. China built its own *national* catalogue (Lancet Microbe
  2024) because the global one underperformed locally.

## The opening

> "Current knowledge on resistance-conferring determinants is biased toward globally
> dominant lineages 2 and 4, while lineages 1 and 3 are predominant in India."

China noticed and built a national catalogue. **South Asia has not.** Bangladesh is L1/L3
country, same as India.

So: broad "cross-country transfer" is claimed. What survives is the **South Asia / lineage
1 and 3 specific** evaluation, and **Bangladesh, where nothing exists at all** — the search
for ML resistance studies on Bangladeshi TB genomes returned none.

Also named by the July 2026 benchmark as the field's own open problem: *"bedaquiline,
delamanid, linezolid, and clofazimine remained persistently difficult to predict"* plus XDR
cases. High value, but CRyPTIC has only 109 BDQ-resistant isolates — good as a section,
bad as a whole thesis.

## Sources

- July 2026 benchmark — https://www.biorxiv.org/content/10.64898/2026.07.03.736369v1
- TB-Bench 2026 — https://www.biorxiv.org/content/10.64898/2026.04.08.717138v1.full
- BMC systematic review 2026 — https://link.springer.com/article/10.1186/s12879-026-14318-y
- FW-RF, lineage bias — https://academic.oup.com/bioinformatics/article/39/7/btad428/7222183
- China national catalogue — https://www.thelancet.com/journals/lanmic/article/PIIS2666-5247(24)00131-9/fulltext
- MIC regression, PLOS Comp Biol — https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1012260
- GenTB (Farhat lab) — https://link.springer.com/article/10.1186/s13073-021-00953-4
- Geographic heterogeneity (Farhat group, 2020) — https://www.biorxiv.org/content/10.1101/2020.09.17.301226.full.pdf
- India lineage study — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9241780/
- CRyPTIC FTP — https://ftp.ebi.ac.uk/pub/databases/cryptic/release_june2022/reuse/

## Publication target

IEEE ICCIT, or a BMC / Frontiers venue. 15 days gives a pilot result, not a paper. Carried
through the thesis semester, a conference paper is realistic.
