"""Step 7 - build the written report (HTML) from the result tables and figures.

Tables are read from results/*.csv so the numbers in the report are the
numbers the pipeline produced. Figures are embedded so the file stands alone.

Output report/report.html, report/report.docx (via pandoc, for Word / Google Docs).
The PDF is printed from the HTML with Chrome - see README.
"""
import base64
import re
from pathlib import Path

import pandas as pd
import pypandoc
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

ROOT = Path(__file__).resolve().parents[1]
RES, PROC, OUT = ROOT / "results", ROOT / "data" / "processed", ROOT / "report"
OUT.mkdir(exist_ok=True)

iso = pd.read_csv(PROC / "isolates.csv")
cl = pd.read_csv(PROC / "clusters.csv")
main = pd.read_csv(RES / "table_main.csv")
lin = pd.read_csv(RES / "table_lineage_random_vs_holdout.csv")
loco = pd.read_csv(RES / "table_loco_sensitivity.csv", index_col=0)
missed = pd.read_csv(RES / "table_missed_summary.csv")
mm = pd.read_csv(RES / "missed_mutations.csv")
allm = pd.read_csv(RES / "metrics.csv")
pred = pd.read_csv(RES / "predictions_sa_holdout.csv")
abl = pd.read_csv(RES / "table_lineage_feature_ablation.csv")

known = iso[iso.country != "UNKNOWN"]
sa = known[known.south_asia]
rest = known[~known.south_asia]
share = lambda df, l: f"{(df.lineage == l).mean():.0%}"  # noqa: E731
sizes = cl.drop_duplicates("cluster").cluster_size


def img(name):
    b64 = base64.b64encode((RES / name).read_bytes()).decode()
    return f'<img src="data:image/png;base64,{b64}" alt="{name}" width="600">'


def pct(x):
    return "" if pd.isna(x) else f"{x:.1%}"


def f3(x):
    return "" if pd.isna(x) else f"{x:.3f}"


# Table 2: main results
t_main = main[["drug", "best_model", "n_SA", "n_R_SA", "sens_random", "sens_holdout",
               "spec_random", "spec_holdout", "auc_random", "auc_holdout", "sens_WHO", "spec_WHO"]].copy()
for c in ["sens_random", "sens_holdout", "spec_random", "spec_holdout", "sens_WHO", "spec_WHO"]:
    t_main[c] = t_main[c].map(pct)
for c in ["auc_random", "auc_holdout"]:
    t_main[c] = t_main[c].map(f3)
t_main.columns = ["Drug", "Model", "Test isolates", "Resistant", "Sens. random", "Sens. holdout",
                  "Spec. random", "Spec. holdout", "AUC random", "AUC holdout", "Sens. WHO",
                  "Spec. WHO"]

# 95% Wilson score intervals for per-lineage sensitivity in the holdout.
def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / d
    return c - h, c + h


lin[["ci_lo", "ci_hi"]] = [wilson(round(r.sens_holdout * r.n_R), r.n_R) for r in lin.itertuples()]
DRUG_NAMES = {"INH": "isoniazid", "RIF": "rifampicin", "EMB": "ethambutol", "ETH": "ethionamide",
              "LEV": "levofloxacin", "MXF": "moxifloxacin", "KAN": "kanamycin", "AMI": "amikacin"}
clear, overlap = [], []
for d in DRUG_NAMES:
    s_ = lin[lin.drug == d].set_index("lineage")
    worst = s_.loc[s_.index.isin(["Lineage 1", "Lineage 3"])].sens_holdout.idxmin()
    (clear if s_.loc[worst, "ci_hi"] < s_.loc["Lineage 2", "ci_lo"] else overlap).append(DRUG_NAMES[d])


def names(xs):
    return ", ".join(xs[:-1]) + " and " + xs[-1]


# Table 3: lineage
t_lin = lin.copy()
t_lin["ci"] = [f"{a:.0%}–{b:.0%}" for a, b in zip(lin.ci_lo, lin.ci_hi)]
for c in ["sens_random", "sens_holdout", "sens_WHO"]:
    t_lin[c] = t_lin[c].map(pct)
t_lin["drop"] = t_lin["drop"].map(lambda v: f"{v * 100:+.1f} pp")
t_lin["lineage"] = t_lin.lineage.str.replace("Lineage ", "L")
t_lin = t_lin[["drug", "lineage", "n_R", "sens_random", "sens_holdout", "ci", "sens_WHO", "drop"]]
t_lin.columns = ["Drug", "Lineage", "Resistant isolates", "Sens. random", "Sens. holdout",
                 "95% CI (holdout)", "Sens. WHO", "Random − holdout"]

# Table 4: LOCO
t_loco = loco.map(lambda v: "" if pd.isna(v) else f"{v:.2f}")
t_loco = t_loco.reset_index().rename(columns={t_loco.index.name or "index": "Held-out country"})

# Table 5: missed summary
t_miss = missed.copy()
t_miss.columns = ["Drug", "Resistant, missed", "Resistant, found",
                  "Missed with no mutation in the drug's genes", "Missed that WHO also misses"]

# Table 6: mutations in missed isolates rare among resistant training isolates
rare = mm[(mm.missed_SA_isolates >= 3) & (mm.train_R_carriers < 10)].copy()
rare.columns = ["Drug", "Mutation", "Missed SA isolates carrying it", "Lineage(s)",
                "Resistant training carriers", "Susceptible training carriers"]

# Table 6: lineage-as-feature ablation
t_abl = abl.copy()
for c in ["auc_random_all", "auc_holdout"]:
    t_abl[c] = t_abl[c].map(f3)
for c in ["sens_holdout", "spec_holdout", "sens_holdout_1", "sens_holdout_3"]:
    t_abl[c] = t_abl[c].map(pct)
t_abl.columns = ["Drug", "Model", "Features", "AUC random (all)", "AUC holdout", "Sens. holdout",
                 "Spec. holdout", "Sens. holdout L1", "Sens. holdout L3"]
abl_w = abl.pivot_table(index="drug", columns="features", values=["auc_holdout", "sens_holdout_1"])
auc_shift = (abl_w["auc_holdout"]["mutations + lineage"] - abl_w["auc_holdout"]["mutations only"]).abs().max()

# Table A1: all models
t_all = allm[allm.test == "South Asia"].pivot_table(index=["drug", "model"], columns="protocol",
                                                     values=["auc", "sensitivity", "specificity"])
t_all = t_all.reindex(["INH", "RIF", "EMB", "ETH", "LEV", "MXF", "KAN", "AMI"], level=0)
NICE = {"auc": "AUC", "sensitivity": "Sens.", "specificity": "Spec.",
        "random": "random", "sa_holdout": "holdout"}
t_all.columns = [f"{NICE[a]} {NICE[b]}" for a, b in t_all.columns]
t_all = t_all.map(lambda v: "" if pd.isna(v) else f"{v:.3f}").reset_index()
t_all.columns = ["Drug", "Model"] + list(t_all.columns[2:])


def table(df, caption, index=False):
    return (f'<figure class="tbl"><figcaption>{caption}</figcaption>'
            + df.to_html(index=index, border=0, escape=False) + "</figure>")


g = lambda d, col: main.set_index("drug").loc[d, col]  # noqa: E731
L = lambda d, l, col: lin[(lin.drug == d) & (lin.lineage == l)][col].item()  # noqa: E731
n_known = len(known)

html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Geographic Transportability of Genome-Based Antibiotic Resistance Prediction in M. tuberculosis</title>
<style>
  body {{ font-family: "Times New Roman", Georgia, serif; font-size: 12pt; line-height: 1.5;
         max-width: 820px; margin: 40px auto; padding: 0 24px; color: #111; }}
  h1 {{ font-size: 19pt; line-height: 1.25; margin-bottom: 6px; }}
  h2 {{ font-size: 14pt; margin-top: 28px; border-bottom: 1px solid #ccc; padding-bottom: 3px; }}
  h3 {{ font-size: 12pt; margin-top: 18px; }}
  .meta {{ color: #444; margin-bottom: 18px; }}
  .abstract {{ background: #f6f6f4; padding: 12px 16px; border-left: 3px solid #2a78d6; }}
  table {{ border-collapse: collapse; font-size: 9.5pt; font-family: Arial, sans-serif;
           margin: 6px 0 4px; width: 100%; }}
  th, td {{ border-bottom: 1px solid #ddd; padding: 3px 6px; text-align: right; }}
  td {{ white-space: nowrap; }}
  th {{ background: #f0efec; }}
  td:first-child, th:first-child {{ text-align: left; }}
  figure {{ margin: 16px 0; page-break-inside: avoid; }}
  figcaption {{ font-size: 10pt; color: #333; margin-bottom: 4px; }}
  figure img {{ max-width: 100%; }}
  .fig figcaption {{ margin-top: 4px; }}
  code {{ font-size: 10pt; }}
  .small {{ font-size: 10pt; color: #444; }}
  h2, h3, figcaption {{ page-break-after: avoid; break-after: avoid; }}
  tr {{ page-break-inside: avoid; break-inside: avoid; }}
  .newpage {{ page-break-before: always; break-before: page; }}
  .cover {{ text-align: center; page-break-after: always; break-after: page; padding-top: 70px; }}
  .cover h1 {{ font-size: 24pt; margin: 18px 0 10px; }}
  .cover .kind {{ font-size: 13pt; letter-spacing: 2px; text-transform: uppercase; color: #444; }}
  .cover .sub {{ font-size: 12pt; color: #444; margin-bottom: 90px; }}
  .cover .label {{ font-size: 11pt; text-transform: uppercase; letter-spacing: 1px; color: #666;
                  margin: 34px 0 4px; }}
  .cover .who {{ font-size: 13pt; margin: 0; }}
  .cover .date {{ margin-top: 70px; font-size: 12pt; }}
</style></head><body>

<div class="cover">
<p class="kind">Research Report</p>
<h1>Geographic Transportability of Genome-Based Antibiotic Resistance Prediction in
<i>Mycobacterium tuberculosis</i>: A South Asian Evaluation</h1>
<p class="sub">Research Track</p>
<p class="label">Submitted to</p>
<p class="who"><b>Imtiaz Riad</b><br>Co-Founder<br>Authentic Four Technology</p>
<p class="label">Submitted by</p>
<p class="who"><b>Rimjhim Dey</b></p>
<p class="date">4 October 2026</p>
</div>
<!--PAGEBREAK-->

<div class="abstract"><b>Abstract.</b>
Machine learning models predict antibiotic resistance in <i>M. tuberculosis</i> from the genome in
days rather than the weeks laboratory testing needs, but they are trained mostly on lineage 2 and 4
strains, while lineages 1 and 3 dominate South Asia. Using the public CRyPTIC dataset of
{len(iso):,} isolates with laboratory-confirmed resistance, we built a binary feature matrix of
{pd.read_csv(PROC / 'features_cols.csv').shape[0]:,} mutations in 23 WHO-catalogue resistance genes
and trained logistic regression, random forest, gradient boosting and a shallow neural network for
eight drugs. Models were evaluated with a random split, a South Asia holdout (trained only on
non-South-Asian isolates, tested on {len(sa):,} isolates from India, Pakistan and Nepal) and
leave-one-country-out, with transmission clusters kept on one side of every split, and benchmarked
against the WHO 2023 mutation catalogue. Aggregate performance transferred well: AUC on South Asian
isolates fell by at most {main.auc_drop.max():.3f} when South Asian data were withheld from
training. Stratifying by lineage told a different story. Resistant lineage 1 and lineage 3 isolates
were detected less often than lineage 2 isolates, with non-overlapping 95% confidence intervals
for {names(clear)} (for example levofloxacin sensitivity
{pct(L('LEV', 'Lineage 1', 'sens_holdout'))} on lineage 1 against {pct(L('LEV', 'Lineage 2', 'sens_holdout'))}
on lineage 2), and this deficit was shared by models that had seen South Asian data and by the WHO
catalogue, which uses no training data at all. The weakness is therefore in what is known about
resistance in these lineages, not only in where the training data came from. Region-specific
failures were also found: ethambutol resistance in a South Asian lineage 2 group carrying
<i>embC</i> A387V and <i>embB</i> Q445R, mutations absent or nearly absent among resistant training isolates, was
missed in {mm[(mm.drug == 'EMB') & (mm.mutation == 'embC_A387V')].missed_SA_isolates.item()} isolates.
</div>
<p class="small"><b>Keywords:</b> antimicrobial resistance · tuberculosis · whole-genome sequencing ·
machine learning · lineage · model generalisation · South Asia</p>

<div class="abstract"><b>Summary in plain language.</b>
Tuberculosis (TB) bacteria can become resistant to antibiotics through small changes (mutations)
in their DNA. Computer models can read these mutations and say which drugs will fail, in days
instead of the weeks a laboratory test takes. TB bacteria come in families called lineages.
Most models were built from lineages 2 and 4, common in Europe and East Asia, while South Asia
(including Bangladesh) has mostly lineages 1 and 3. We asked: do these models still work on South
Asian TB? We trained four kinds of model only on isolates from outside South Asia
({pred.n_train.min():,}–{pred.n_train.max():,} per drug) and tested them on {len(sa):,} isolates
from India, Pakistan and Nepal. <b>Overall they worked about
as well as usual. But for lineage 1 and lineage 3 bacteria they missed many more resistant cases</b>
— for levofloxacin, about half of resistant lineage 1 cases were missed, against about 6% for
lineage 2. The official WHO mutation list misses the same cases, so the problem is that the
resistance mutations of these South Asian lineages are not yet well known. Missing a resistant
case means a patient may get a drug that will not work, so South Asia needs resistance knowledge
built from its own lineages.
</div>

<h2>1. Introduction</h2>
<p>Tuberculosis remains among the leading infectious causes of death, and drug resistance is the
main obstacle to treating it. Culture-based drug-susceptibility testing takes weeks. Whole-genome
sequencing offers a faster route: resistance in <i>M. tuberculosis</i> arises almost entirely from
chromosomal mutations, so a model that knows which mutations matter can read resistance off the
genome. The WHO mutation catalogue (2021, updated 2023) [2] and machine learning classifiers built
on large collections such as CRyPTIC [1] report high accuracy for first-line drugs [11].</p>
<p>That accuracy is measured on strains like those the models were built from. The <i>M.
tuberculosis</i> complex is divided into lineages with distinct geography: lineages 2 and 4
dominate East Asia, Europe and the Americas, while lineages 1 and 3 predominate in South Asia,
including India [8]. Resistance knowledge is biased toward the globally dominant
lineages [8], and China built a national catalogue because the global one under-performed locally
[6]. No comparable evaluation exists for South Asia.</p>
<p><b>Research question.</b> Do genome-based resistance models still work on South Asian strains,
and if not, which resistance cases do they miss? This report presents the full pilot study: data
preparation, feature construction, leakage-controlled evaluation under three protocols, a WHO
catalogue benchmark and an error analysis by lineage.</p>

<h2>2. Related work</h2>
<p>First-line prediction is mature: published models reach AUC of about 0.99 for rifampicin and
0.98 for isoniazid, and most report at least 90% sensitivity for isoniazid [11]. The WHO catalogue
[2] is the clinical reference, implemented in tools such as TB-Profiler and Mykrobe. MIC
regression on CRyPTIC has been published for 13 drugs [7]. The Farhat group's GenTB [3] and their
study of geographic heterogeneity [4] are the closest prior work on cross-region transfer.
Lineage dependence has been addressed by feature reweighting (FW-RF) [5] and by China's national
catalogue [6]. Recent benchmarks [9, 10] name second-line and newer drugs as the open
problems. What remains untested is a lineage-resolved evaluation on South Asian isolates with
transmission-aware splits, and that is the contribution here.</p>

<h2>3. Data</h2>
<p><b>Source.</b> CRyPTIC consortium, release June 2022 [1], public EBI FTP. We used the reuse table of {len(iso):,} isolates with binary resistant/susceptible phenotypes
from UKMYC microtitre plates, the per-isolate mutation table (<code>MUTATIONS_GPI</code>), sample
metadata for country, Mykrobe lineage calls and the consortium's precomputed pairwise SNP
distances.</p>
<p><b>Labels.</b> Phenotypes with LOW reading quality, intermediate (I) calls and missing values
were excluded per drug. Eight drugs had enough resistant isolates in both regions: isoniazid (INH),
rifampicin (RIF), ethambutol (EMB), ethionamide (ETH), levofloxacin (LEV), moxifloxacin (MXF),
kanamycin (KAN) and amikacin (AMI). Bedaquiline, delamanid, linezolid and clofazimine were dropped
for too few resistant cases.</p>
<p><b>Country.</b> Country of sampling was taken from the sample table, falling back to the
collecting site where that site only serves its own country. Isolates collected by the
multi-country reference laboratories in Gauting and Milan without a recorded country
({(iso.country == 'UNKNOWN').sum():,}) were excluded from every protocol, leaving {n_known:,}.
The South Asian test set is {len(sa):,} isolates: India {(sa.country == 'IND').sum():,},
Pakistan {(sa.country == 'PAK').sum():,} and Nepal {(sa.country == 'NPL').sum():,}.</p>
<p class="small"><b>Correction to the topic form.</b> The topic form quoted 5,907 South Asian
isolates. That figure counted every South Asian sample in the CRyPTIC metadata, including samples
with no resistance phenotype. The isolates with laboratory resistance labels number
{len(sa):,}, and all results here use that set.</p>
<p><b>Lineage shift.</b> The two populations differ sharply (Figure 1). Lineages 1 and 3 make up
{share(sa, 'Lineage 1')} and {share(sa, 'Lineage 3')} of South Asian isolates, against
{share(rest, 'Lineage 1')} and {share(rest, 'Lineage 3')} of the rest; lineage 4 is
{share(rest, 'Lineage 4')} of the rest but {share(sa, 'Lineage 4')} of South Asia.</p>
<figure class="fig">{img('fig_lineage_composition.png')}
<figcaption>Figure 1. Lineage composition of labelled isolates with a known country.</figcaption></figure>

<h2>4. Methods</h2>
<h3>4.1 Features</h3>
<p>Candidate genes were the WHO 2023 catalogue tier 1 and 2 genes for the eight drugs (23 genes:
<i>rpoB, rpoA, rpoC, katG, inhA, fabG1, ahpC, mshA, ndh, kasA, embB, embA, embC, embR, ubiA, ethA,
ethR, gyrA, gyrB, rrs, eis, whiB7, tlyA</i>, including promoter regions). Calls failing the
variant filter, null calls and heterozygous calls were removed, as were synonymous changes except
in <i>fabG1</i>, where L203L is a graded resistance mutation. Each remaining mutation became one
binary feature, with indels encoded by position, direction and length, plus one loss-of-function
feature per gene (any frameshift or premature stop). Mutations seen in fewer than three isolates
were dropped, giving {pd.read_csv(PROC / 'features_cols.csv').shape[0]:,} features. No raw reads
were processed.</p>
<h3>4.2 Leakage control</h3>
<p>Closely related isolates on both sides of a split inflate accuracy. Isolates within 12 SNPs of
each other were linked using CRyPTIC's precomputed distances, and transmission clusters were taken
as connected components. Links were only allowed between isolates of the same single Mykrobe
lineage: with mixed-lineage samples acting as bridges, single linkage had chained lineage 2 and
lineage 4 into one 2,539-isolate component, which cannot be a transmission chain. The final
grouping has {cl.cluster.nunique():,} clusters ({(sizes == 1).sum():,} singletons, largest
{sizes.max()}). In every protocol whole clusters are kept on one side; in the holdout protocols
any training isolate sharing a cluster with a test isolate is removed.</p>
<h3>4.3 Models</h3>
<p>Four classifiers were trained per drug: L2 logistic regression (class-balanced), random forest
(300 trees, class-balanced), gradient-boosted trees (XGBoost, 300 trees, depth 4, positive-class
weighting) and a shallow neural network (two hidden layers of 64 and 32 units, early stopping).
Hyperparameters were fixed in advance, not tuned on test data, and the decision threshold was 0.5.
All training ran on a CPU.</p>
<h3>4.4 Evaluation protocols</h3>
<ol>
<li><b>Random split.</b> Five-fold cross-validation over all {n_known:,} isolates with a known
country, stratified by label and grouped by transmission cluster. Out-of-fold predictions are
scored on all isolates and on the South Asian subset. This is the setting in which South Asian
strains are represented in training.</li>
<li><b>South Asia holdout.</b> Train only on non-South-Asian isolates and test on the South Asian
isolates. Comparing this with the South Asian subset of protocol 1 gives the cost of never having
seen the region, measured on the same isolates.</li>
<li><b>Leave-one-country-out.</b> Each country with at least 150 labelled isolates is held out in
turn.</li>
</ol>
<p>The best model per drug was chosen by random-split AUC on all isolates, so the choice never
looks at the holdout. Metrics are sensitivity (share of resistant isolates detected; its complement
is the very major error rate, the clinically dangerous miss), specificity, AUC and F1.</p>
<h3>4.5 WHO catalogue benchmark</h3>
<p>The WHO 2023 catalogue [2] (v2, in the GARC grammar maintained by the Oxford group behind
CRyPTIC) was applied to the same mutation calls: an isolate is called resistant if it carries any mutation
graded group 1 or 2 for that drug, including codon wildcards, gene-level frameshift and stop rules,
and indel rules. Applied to all isolates, our implementation gives sensitivity/specificity of
about 96%/95% for rifampicin and 93%/98% for isoniazid, in line with published CRyPTIC figures.</p>

<h2>5. Results</h2>
<h3>5.1 Aggregate performance transfers</h3>
<p>Table 1 compares, on the same South Asian isolates, models that saw South Asian data in training
(random split) with models that did not (holdout). AUC moved by at most {main.auc_drop.max():.3f}.
Sensitivity dropped most for ethambutol ({main.set_index('drug').loc['EMB', 'sens_drop'] * 100:.1f}
percentage points) and ethionamide ({main.set_index('drug').loc['ETH', 'sens_drop'] * 100:.1f}
points), and by two points or less for isoniazid, rifampicin and the fluoroquinolones. For kanamycin and
amikacin the holdout models raised sensitivity but lost about 10 points of specificity with
unchanged AUC: the ranking of isolates stayed the same while the operating point shifted, a
calibration effect rather than lost knowledge. Against the WHO catalogue, the models were within
1.5 points of its sensitivity for isoniazid, rifampicin and the fluoroquinolones (the catalogue
slightly ahead), and clearly more sensitive for ethambutol, ethionamide, kanamycin and amikacin
(by 1.5 to 14 points), at a cost in specificity for the aminoglycosides.</p>
{table(t_main, 'Table 1. Performance on South Asian isolates. "Random" = random split (South Asian isolates represented in training); "holdout" = trained only on non-South-Asian isolates. Best model per drug chosen on random-split AUC.')}
<figure class="fig">{img('fig_sensitivity_protocols.png')}
<figcaption>Figure 2. Sensitivity on South Asian isolates under the three settings.</figcaption></figure>
<p>Figure 3 gives the full confusion matrices for the holdout. The clinically dangerous cell is
true resistant predicted susceptible (top right): 5% to 6% of resistant isolates for isoniazid and
rifampicin, rising to about a quarter for ethionamide and amikacin. For kanamycin and amikacin the
larger error by count is the opposite one, susceptible isolates called resistant (bottom left), which is
the specificity loss described above.</p>
<figure class="fig">{img('fig_confusion_matrices.png')}
<figcaption>Figure 3. Confusion matrices for the South Asia holdout, best model per drug. Counts
with row percentages.</figcaption></figure>

<h3>5.2 Lineages 1 and 3 are where resistance is missed</h3>
<p>The aggregate hides a consistent pattern (Table 2, Figure 4). For every drug the
worst-detected lineage was lineage 1 or lineage 3, and for six of the eight drugs lineage 2 was
detected best. In the holdout,
isoniazid sensitivity was {pct(L('INH', 'Lineage 1', 'sens_holdout'))} on lineage 1 against
{pct(L('INH', 'Lineage 2', 'sens_holdout'))} on lineage 2; levofloxacin
{pct(L('LEV', 'Lineage 1', 'sens_holdout'))} against {pct(L('LEV', 'Lineage 2', 'sens_holdout'))};
moxifloxacin {pct(L('MXF', 'Lineage 1', 'sens_holdout'))} against
{pct(L('MXF', 'Lineage 2', 'sens_holdout'))}; ethionamide {pct(L('ETH', 'Lineage 3', 'sens_holdout'))}
on lineage 3; and amikacin {pct(L('AMI', 'Lineage 3', 'sens_holdout'))} on lineage 3. Some of these
groups are small, so Table 2 gives 95% confidence intervals (Wilson score). For {names(clear)}
the interval for the worst lineage does not overlap the lineage 2 interval, so the gap is clear.
For {names(overlap)} the gap points the same way but the intervals overlap, so it is suggestive
rather than established.</p>
<p>The deciding comparison is between the three columns. If the deficit came from training on
foreign strains, the random-split models, which did see South Asian lineage 1 and 3 isolates,
should recover it. They mostly do not: lineage 1 levofloxacin sensitivity is
{pct(L('LEV', 'Lineage 1', 'sens_random'))} with South Asian data in training, and the WHO
catalogue, which has no training step, reaches {pct(L('LEV', 'Lineage 1', 'sens_WHO'))}. The low
sensitivity on lineages 1 and 3 is shared by all three, so it reflects the resistance mutations
that are known, not only the origin of the training data. Training on foreign strains adds a
smaller, drug-specific loss on top: moxifloxacin on lineage 1
({L('MXF', 'Lineage 1', 'drop') * 100:+.1f} points, but only
{L('MXF', 'Lineage 1', 'n_R')} resistant isolates), and ethambutol and ethionamide on lineage 2
({L('EMB', 'Lineage 2', 'drop') * 100:+.1f} and {L('ETH', 'Lineage 2', 'drop') * 100:+.1f} points).</p>
{table(t_lin, 'Table 2. Sensitivity on resistant South Asian isolates by lineage (lineages with at least 10 resistant isolates). "Random − holdout" is the loss from withholding South Asian isolates from training.')}
<figure class="fig">{img('fig_lineage_sensitivity.png')}
<figcaption>Figure 4. Sensitivity on resistant South Asian isolates by lineage under each setting.</figcaption></figure>

<h3>5.3 Leave-one-country-out</h3>
<p>Holding out one country at a time (Table 3, Figure 5) shows the same geography of failure.
Isoniazid and rifampicin transfer to every country at 0.83 or above, while ethambutol falls to
{loco.loc['PER', 'EMB']:.2f} for Peru. Second-line sensitivity collapses
for Vietnam (levofloxacin {loco.loc['VNM', 'LEV']:.2f}, moxifloxacin {loco.loc['VNM', 'MXF']:.2f},
amikacin {loco.loc['VNM', 'AMI']:.2f}), which also has a sizeable lineage 1 population, and is weak
for China, Pakistan and India on the injectable drugs. The South Asian countries sit in the middle:
India and Nepal transfer well for first-line drugs, while Pakistan loses ground on ethionamide,
the fluoroquinolones and the aminoglycosides. Small held-out sets (for example amikacin in Brazil)
give unstable estimates.</p>
{table(t_loco, 'Table 3. Leave-one-country-out sensitivity of the best model (blank: fewer than 10 resistant isolates).')}
<figure class="fig">{img('fig_loco_sensitivity.png')}
<figcaption>Figure 5. Leave-one-country-out sensitivity.</figcaption></figure>

<h3>5.4 What the missed isolates carry</h3>
<p>Most resistant South Asian isolates the models missed were also missed by the WHO catalogue
(Table 4), which again points to a gap in known determinants rather than a modelling failure. For
kanamycin and amikacin, about 70% of missed isolates carried no mutation at all in the
drugs' candidate genes, consistent with mechanisms outside these genes or with phenotyping error
near the breakpoint.</p>
{table(t_miss, 'Table 4. Resistant South Asian isolates missed by the best model in the holdout.')}
<p>Table 5 lists mutations carried by at least three missed isolates but by fewer than ten
resistant training isolates. Two are clearly regional. <i>embC</i> A387V
({mm[(mm.drug == 'EMB') & (mm.mutation == 'embC_A387V')].missed_SA_isolates.item()} missed
isolates) and <i>embB</i> Q445R
({mm[(mm.drug == 'EMB') & (mm.mutation == 'embB_Q445R')].missed_SA_isolates.item()}) occur in a
South Asian lineage 2 group and are absent or near-absent among resistant training isolates; they
likely account for much of the ethambutol loss on lineage 2. <i>embB</i> Q445R is carried by
only four resistant and no susceptible training isolates. Lineage 1 fluoroquinolone misses carry
<i>gyrA</i> A384V and <i>gyrB</i> M291I, which appear in hundreds of susceptible training
isolates: these are lineage 1 markers, not resistance mutations. The WHO catalogue also misses
{missed.set_index('drug').loc['LEV', 'missed_also_missed_by_WHO']} of the
{missed.set_index('drug').loc['LEV', 'missed_R']} levofloxacin-resistant isolates the model missed,
so for most of them no graded resistance mutation is present.
Isoniazid misses in lineages 1 and 3 include <i>ahpC</i> t-76a and <i>katG</i> T380I, unseen in
training.</p>
{table(rare.groupby('Drug').head(6), 'Table 5. Mutations in missed South Asian isolates that are rare among resistant training isolates.')}

<h3>5.5 Robustness: lineage as a feature</h3>
<p>If the models were using strain family as a shortcut, or if knowing an isolate's lineage let
them correct for it, adding lineage as an explicit feature should change the results. It barely
does (Table 6): holdout AUC moves by at most {auc_shift:.3f}, and lineage 1 sensitivity is
unchanged for every drug. Lineage 3 sensitivity moves a few points either way, up for the
fluoroquinolones and down for ethionamide, kanamycin and amikacin. Telling the model the lineage
does not close the gap, which supports the reading that the missing piece is the resistance
mutations themselves.</p>
{table(t_abl, 'Table 6. Best model per drug with and without lineage as a feature (South Asia holdout; L1/L3 = resistant isolates of that lineage, shown where at least 10).')}

<h2>6. Discussion</h2>
<p>The study set out to test whether genome-based resistance models trained outside South Asia
transfer to South Asian strains. On aggregate they do: for every drug, AUC on South Asian isolates
was essentially unchanged when South Asian data were withheld, and isoniazid and rifampicin
sensitivity stayed near 95%. A study reporting only aggregate metrics would conclude that transportability is not a
problem.</p>
<p>The lineage breakdown contradicts that conclusion where it matters. Resistant lineage 1 and 3
isolates, which make up half of the South Asian isolates here but only a few percent of the training
population,
are detected 11 to 41 percentage points less often than lineage 2 isolates, depending on the
drug; the gap is statistically clear for {names(clear)}.
Because the deficit appears with and without South Asian training data and in the WHO catalogue
alike, more training data from the same genes alone is unlikely to fix it. The resistance mechanisms of these lineages
are less well characterised. That is the same reasoning that led China to build a national
catalogue, and these results argue for a lineage-aware South Asian equivalent. The relevance to
Bangladesh follows from lineage rather than from local sampling, since lineages 1 and 3 are also
reported to predominate in Bangladesh.</p>
<p>Two practical points follow. Evaluations of resistance predictors should report sensitivity by
lineage, because aggregate figures are dominated by lineages 2 and 4. And region-specific
mutations such as <i>embC</i> A387V and <i>embB</i> Q445R show that some failures do come from
geography: a model never shown a local resistant clade cannot learn its mutations.</p>

<h2>7. Limitations</h2>
<ul>
<li>Lineage 1 resistant counts are small for some drugs (13 for moxifloxacin, 23 for ethambutol),
so those per-lineage estimates carry wide 95% intervals (Table 2), and for {names(overlap)} the
lineage gap is not statistically established.</li>
<li>South Asian isolates come mainly from one Mumbai referral centre and from referral
laboratories, and are enriched for drug resistance; they are not a population sample.</li>
<li>Features are restricted to 23 known resistance genes. Resistance outside them cannot be
learned, which is part of what is being measured but also caps the models.</li>
<li>Transmission clusters were derived from distances over CRyPTIC's gene panel, and single
linkage was restricted to same-lineage pairs; other thresholds could change the grouping.</li>
<li>Hyperparameters were fixed rather than tuned, and the 0.5 threshold was not recalibrated per
setting, which explains the kanamycin and amikacin specificity shift.</li>
<li>Phenotypes come from a single plate-based method; errors near the breakpoint count as model
errors.</li>
<li>No Bangladeshi isolates were used: public Bangladeshi genomes carry no paired laboratory
phenotype.</li>
</ul>

<h2>8. Conclusion and future work</h2>
<p>Genome-based resistance prediction in <i>M. tuberculosis</i> transfers to South Asian isolates
on aggregate, but systematically under-detects resistance in lineages 1 and 3, the families that
dominate the region, and this weakness is shared by the WHO catalogue. Next steps for the thesis
semester: larger lineage 1 and 3 samples to settle the drugs where the gap is not yet
statistically clear; genome-wide features to look
for determinants outside the candidate genes in missed lineage 1 and 3 isolates; lineage-aware
reweighting (as in FW-RF); threshold recalibration per region; and, if a paired Bangladeshi genome
and phenotype set becomes available through collaboration, direct validation.</p>

<h2>References</h2>
<ol class="small">
<li>The CRyPTIC Consortium. A data compendium associating the genomes of 12,289
<i>Mycobacterium tuberculosis</i> isolates with quantitative resistance phenotypes to 13
antibiotics. <i>PLOS Biology</i> 20(8): e3001721, 2022. doi:10.1371/journal.pbio.3001721</li>
<li>World Health Organization. Catalogue of mutations in <i>Mycobacterium tuberculosis</i>
complex and their association with drug resistance, 2nd edition, 2023. GARC version:
github.com/oxfordmmm/tuberculosis_amr_catalogues</li>
<li>GenTB, genome-based TB resistance predictor (Farhat lab). <i>Genome Medicine</i>, 2021.
https://link.springer.com/article/10.1186/s13073-021-00953-4</li>
<li>Geographic heterogeneity impacts drug resistance predictions in <i>Mycobacterium
tuberculosis</i>. bioRxiv, 2020. https://www.biorxiv.org/content/10.1101/2020.09.17.301226</li>
<li>FW-RF, lineage-dependent feature weighting. <i>Bioinformatics</i> 39(7): btad428, 2023.
https://academic.oup.com/bioinformatics/article/39/7/btad428/7222183</li>
<li>National catalogue of <i>M. tuberculosis</i> resistance mutations, China. <i>Lancet
Microbe</i>, 2024. https://www.thelancet.com/journals/lanmic/article/PIIS2666-5247(24)00131-9/fulltext</li>
<li>MIC prediction on CRyPTIC isolates. <i>PLOS Computational Biology</i>, 2024.
doi:10.1371/journal.pcbi.1012260</li>
<li>Lineage distribution of <i>M. tuberculosis</i> in India. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9241780/</li>
<li>TB-Bench, second-line resistance benchmark. bioRxiv, April 2026.
https://www.biorxiv.org/content/10.64898/2026.04.08.717138v1</li>
<li>Translational benchmark of genome-based TB resistance prediction. bioRxiv, July 2026.
https://www.biorxiv.org/content/10.64898/2026.07.03.736369v1</li>
<li>Systematic review of machine learning for TB drug resistance. <i>BMC Infectious Diseases</i>,
2026. https://link.springer.com/article/10.1186/s12879-026-14318-y</li>
</ol>

<!--PAGEBREAK-->
<h2 class="newpage">Appendix A. All models</h2>
{table(t_all, 'Table A1. Every model on South Asian isolates under the random split and the South Asia holdout.')}

<h2>Resources</h2>
<ul>
<li><b>Code repository</b> (all scripts, results, figures and this report):
<a href="https://github.com/RimjhimD/Genome-Based-Antibiotic-Resistance-Prediction-TB">https://github.com/RimjhimD/Genome-Based-Antibiotic-Resistance-Prediction-TB</a></li>
<li><b>Dataset:</b> CRyPTIC consortium, release June 2022 —
<a href="https://ftp.ebi.ac.uk/pub/databases/cryptic/release_june2022/">https://ftp.ebi.ac.uk/pub/databases/cryptic/release_june2022/</a></li>
<li><b>WHO mutation catalogue</b> (2023, v2, GARC format) —
<a href="https://github.com/oxfordmmm/tuberculosis_amr_catalogues">https://github.com/oxfordmmm/tuberculosis_amr_catalogues</a></li>
</ul>
<p class="small"><b>Reproducing the results.</b> <code>bash scripts/fetch_data.sh --mutations</code>
downloads the data; <code>pip install -r requirements.txt</code> installs the exact library
versions; scripts <code>01_prepare.py</code> to <code>07_report.py</code> run in order on a CPU
(under 15 minutes of training on a 15 GB laptop), and <code>check_results.py</code> runs 31
checks on the outputs (counts, train/test leakage, WHO accuracy, report tables). Seeds are fixed,
and a run from a fresh clone reproduced every result.</p>
</body></html>
"""
(OUT / "report.html").write_text(html)
print(f"wrote {OUT / 'report.html'} ({len(html) / 1e6:.1f} MB)")


# ---- Word version ---------------------------------------------------------------
# Pandoc gives clean paragraphs, lists and images; tables then get full page width
# and a smaller font so numbers do not wrap. Captions go above tables.
src = re.sub(r"<title>.*?</title>", "", html).replace("<!--PAGEBREAK-->", "<p>PAGEBREAK</p>")
src = re.sub(r'<figure class="tbl"><figcaption>(.*?)</figcaption>(.*?)</figure>',
             r"<p><b>\1</b></p>\2", src, flags=re.S)
docx_path = OUT / "report.docx"
pypandoc.convert_text(src, "docx", format="html", outputfile=str(docx_path))

doc = Document(str(docx_path))
pars = doc.paragraphs
first_break = next(i for i, p_ in enumerate(pars) if p_.text.strip() == "PAGEBREAK")
for i, par in enumerate(pars[:first_break]):  # cover page
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_after = Pt(6)
    text = par.text.strip()
    if text == "Research Report":
        par.paragraph_format.space_before = Pt(80)
    if text in ("Submitted to", "Submitted by"):
        par.paragraph_format.space_before = Pt(36)
        for run in par.runs:
            run.font.size = Pt(10)
            run.font.all_caps = True
    if text == "Research Track":
        par.paragraph_format.space_after = Pt(60)
    if text == "4 October 2026":
        par.paragraph_format.space_before = Pt(70)
for par in pars:
    if par.text.strip() == "PAGEBREAK":
        for run in par.runs:
            run.text = ""
        (par.runs[0] if par.runs else par.add_run()).add_break(WD_BREAK.PAGE)
    style = par.style.name if par.style is not None else ""
    is_caption = par.text.startswith("Table ") and any(r.font.bold for r in par.runs)
    has_image = bool(par._p.xpath(".//pic:pic"))
    if style.startswith("Heading") or style == "Title" or is_caption or has_image:
        par.paragraph_format.keep_with_next = True
for t in doc.tables:
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_pr = t._tbl.tblPr
    for tag in ("w:tblW", "w:tblLayout", "w:tblBorders"):
        for el in tbl_pr.findall(qn(tag)):
            tbl_pr.remove(el)
    width = OxmlElement("w:tblW")
    width.set(qn("w:type"), "pct")
    width.set(qn("w:w"), "5000")  # 100% of the text width
    tbl_pr.append(width)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "bottom", "insideH"):
        b = OxmlElement(f"w:{edge}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:color"), "BBBBBB")
        borders.append(b)
    tbl_pr.append(borders)
    for row in t.rows:
        for cell in row.cells:
            for par in cell.paragraphs:
                par.paragraph_format.space_after = Pt(0)
                for run in par.runs:
                    run.font.size = Pt(8)
    for cell in t.rows[0].cells:
        for par in cell.paragraphs:
            for run in par.runs:
                run.font.bold = True
doc.save(str(docx_path))
print(f"wrote {docx_path}")

