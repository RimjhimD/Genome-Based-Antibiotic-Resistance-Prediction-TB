"""Apply the WHO 2023 mutation catalogue (GARC grammar) to CRyPTIC mutation calls.

An isolate is called resistant to a drug if it carries any mutation graded R
(groups 1-2) for that drug; otherwise susceptible. Rules for minor alleles
(":N" suffix) are folded into the main rule because het calls are excluded
upstream. Whole-gene deletions ("del_1.0") cannot be seen in the mutation table
and never match.
"""
import re

import pandas as pd

AA_WILDCARD = re.compile(r"^([A-Z!])(-?\d+)\?$")      # rpoB@S450?  any change at codon
ANY_INDEL = re.compile(r"^(-?\d+)_indel$")            # rpoB@1296_indel
SPECIFIC_INDEL = re.compile(r"^(-?\d+)_(ins|del)_([acgtz]+)$")  # rpoB@1296_ins_ttc


def isolate_tokens(calls: pd.DataFrame) -> pd.Series:
    """Map UNIQUEID -> set of tokens a rule component can match against."""
    c = calls
    snp = c[~c.IS_INDEL]
    indel = c[c.IS_INDEL]
    pos = indel.INDEL_2.astype(str).str.split("_").str[0]
    kind = indel.INDEL_2.astype(str).str.split("_").str[1]
    length = indel.INDEL_LENGTH.abs().astype(int).astype(str)
    nonsyn = snp[~snp.IS_SYNONYMOUS]
    codon = nonsyn.MUTATION.str.extract(r"^([A-Z!]-?\d+)[A-Z!]$")[0].dropna()
    tok = pd.concat([
        snp.UNIQUEID.to_frame().assign(t=snp.GENE + "@" + snp.MUTATION),
        nonsyn.loc[codon.index, ["UNIQUEID"]].assign(t=nonsyn.loc[codon.index, "GENE"] + "@" + codon + "?"),
        indel.UNIQUEID.to_frame().assign(t=indel.GENE + "@" + pos + "_indel"),
        indel.UNIQUEID.to_frame().assign(t=indel.GENE + "@" + pos + "_" + kind + "_" + length),
        c[c.frameshift].UNIQUEID.to_frame().assign(t=c[c.frameshift].GENE + "@*_fs"),
        c[c.stop].UNIQUEID.to_frame().assign(t=c[c.stop].GENE + "@*!"),
    ])
    return tok.groupby("UNIQUEID").t.agg(set)


def normalise(component: str) -> str | None:
    """Rewrite one rule component into the token form produced above."""
    gene, mut = component.split("@", 1)
    mut = re.sub(r":\d+$", "", mut)
    if mut.startswith("del_"):
        return None
    if AA_WILDCARD.match(mut) or ANY_INDEL.match(mut):
        return f"{gene}@{mut}"
    m = SPECIFIC_INDEL.match(mut)
    if m:
        return f"{gene}@{m.group(1)}_{m.group(2)}_{len(m.group(3))}"
    return f"{gene}@{mut}"


def resistance_rules(catalogue: pd.DataFrame, drug: str) -> list[frozenset]:
    rules = set()
    for rule in catalogue[(catalogue.DRUG == drug) & (catalogue.PREDICTION == "R")].MUTATION:
        parts = [normalise(p) for p in rule.split("&")]
        # fabG1@L203L&fabG1@g609a names one change twice; the table records the codon form.
        parts = [p for p in parts if p and not re.match(r"^fabG1@g609a$", p)]
        if parts:
            rules.add(frozenset(parts))
    return list(rules)


def predict(tokens: pd.Series, ids, rules) -> pd.Series:
    out = []
    for u in ids:
        t = tokens.get(u, set())
        out.append(int(any(r <= t for r in rules)))
    return pd.Series(out, index=list(ids))
