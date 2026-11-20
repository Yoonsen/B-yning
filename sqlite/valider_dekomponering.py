#!/usr/bin/env python3
"""
Validering av dekomponereren (hull 4 i tekst/mons_presentasjon_plan.md).

    python3 -m sqlite.valider_dekomponering

Ideen: i gullstandardene (Sett A for verb og substantiv) er alle kjerneformer entydige, så vi
kjenner fasiten. Vi later som én form er flertydig og anslår den fra resten av paradigmet.

Test 1 (én form holdes ute): hvor nær kommer anslaget for én kategori den faktiske frekvensen?
Test 2 (syntetiske homografer): vi slår sammen en substantivform og en verbform til en kunstig
        flertydig form (som «fisker» = fl ub + pres) og ser hvor godt andelene gjenfinnes.

To metoder sammenlignes:
  regler  – de faste forholdstallene i sqlite/decomposer.py (estimate_from_slots), slik de brukes i dag
  lært    – median av (mål / sum øvrige former) lært på gullstandarden, med 5-delt kryssvalidering
  logreg  – lineær regresjon på log-frekvensene til de øvrige kategoriene, samme kryssvalidering

Alle tall er fra nb_totals, som dekomponereren bruker.
"""

import csv
import math
import random
import statistics as st

import numpy as np
from pathlib import Path

from sqlite.decomposer import estimate_from_slots
from sqlite.queries import get_conn
from sqlite.substantivtyper import load_noun_forms, select_gold
from sqlite.verbtyper import load_verbs, select_sets

ROOT = Path(__file__).resolve().parent.parent
OUT_TSV = ROOT / "resultater" / "dekomponering_validering.tsv"
SEED = 20261120
FOLDS = 5
N_PAIRS = 3000
METHODS = ("regler", "lært", "logreg")

POS = {
    "subst": {"bg": "substantiv", "slots": {1: "ent ub", 2: "ent be", 3: "fl ub", 4: "fl be"}},
    "verb": {"bg": "verb, normal", "slots": {1: "inf", 2: "pres", 4: "pret", 5: "perf-part"}},
}
# Syntetiske homografer: (substantivkategori, verbkategori, eksempel på ekte tilfelle)
HOMOGRAPH_TYPES = [
    (3, 2, "fl ub + pres (fisker, ønsker, møter)"),
    (2, 4, "ent be + pret (landet)"),
    (1, 1, "ent ub + inf (fiske, bade)"),
    (1, 2, "ent ub + pres (dør)"),
]


def load_gold() -> dict[str, list[dict]]:
    conn = get_conn()
    nouns, _ = select_gold(load_noun_forms(conn))
    verbs, _ = select_sets(load_verbs(conn))
    gold = {
        "subst": [{"grunnform": d["grunnform"], "f": dict(d["nb_slot"])} for d in nouns],
        "verb": [{"grunnform": d["grunnform"], "f": dict(d["nb_slot"])} for d in verbs["533"]],
    }
    # Fasit krever at alle kategorier er belagt (ellers er log-feilen udefinert)
    for pos in gold:
        gold[pos] = [d for d in gold[pos] if all(d["f"][s] > 0 for s in POS[pos]["slots"])]
    return gold


def rule_estimate(pos: str, f: dict[int, int], target: int) -> float:
    slot_info = {
        s: {"freq": v, "eff_freq": float(v), "min_lem_cnt": 1, "boy_tekst": POS[pos]["slots"][s]}
        for s, v in f.items() if s != target
    }
    est, _ = estimate_from_slots(POS[pos]["bg"], {target}, slot_info, sum(slot_info[s]["freq"] for s in slot_info))
    return est


def add_estimates(gold: dict[str, list[dict]]) -> None:
    """Legger på d['est'][metode][kategori] for hver lemma og kategori."""
    rng = random.Random(SEED)
    for pos, ds in gold.items():
        idx = list(range(len(ds)))
        rng.shuffle(idx)
        fold = {i: k % FOLDS for k, i in enumerate(idx)}
        for d in ds:
            d["est"] = {"regler": {}, "lært": {}, "logreg": {}}
        for t in POS[pos]["slots"]:
            for k in range(FOLDS):
                train = [ds[i] for i in range(len(ds)) if fold[i] != k]
                ratio = st.median(d["f"][t] / (sum(d["f"].values()) - d["f"][t]) for d in train)
                others = [s for s in POS[pos]["slots"] if s != t]
                X = np.array([[1.0] + [math.log(d["f"][s]) for s in others] for d in train])
                y = np.array([math.log(d["f"][t]) for d in train])
                beta, *_ = np.linalg.lstsq(X, y, rcond=None)
                for i in range(len(ds)):
                    if fold[i] == k:
                        d = ds[i]
                        d["est"]["lært"][t] = ratio * (sum(d["f"].values()) - d["f"][t])
                        d["est"]["logreg"][t] = math.exp(beta @ np.array([1.0] + [math.log(d["f"][s]) for s in others]))
            for d in ds:
                d["est"]["regler"][t] = rule_estimate(pos, d["f"], t)


def factor(x: float) -> str:
    return f"×{x:.2f}".replace(".", ",")


def pct(x: float) -> str:
    return f"{100 * x:.0f} %"


def test1(gold: dict[str, list[dict]]) -> list[dict]:
    print("\nTEST 1: én kategori holdes ute og anslås fra resten av paradigmet")
    print("  skjevhet = median anslag/fasit; typisk avvik = median av |log| som faktor;")
    print("  andel innen ×1,5 og ×2 av fasit\n")
    print(f"  {'':5s} {'kategori':10s} {'metode':7s} {'N':>5s} {'skjevhet':>9s} {'typisk':>8s} {'≤×1,5':>7s} {'≤×2':>6s}")
    rows = []
    for pos, ds in gold.items():
        for t, lab in POS[pos]["slots"].items():
            for m in METHODS:
                lr = [math.log2(d["est"][m][t] / d["f"][t]) if d["est"][m][t] > 0 else -10 for d in ds]
                bias = 2 ** st.median(lr)
                typ = 2 ** st.median(abs(x) for x in lr)
                w15 = sum(abs(x) <= math.log2(1.5) for x in lr) / len(lr)
                w2 = sum(abs(x) <= 1 for x in lr) / len(lr)
                print(f"  {pos:5s} {lab:10s} {m:7s} {len(ds):5d} {factor(bias):>9s} {factor(typ):>8s} {pct(w15):>7s} {pct(w2):>6s}")
                rows.append({"pos": pos, "kategori": lab, "metode": m, "n": len(ds), "skjevhet": bias,
                             "typisk_faktor": typ, "innen_1_5": w15, "innen_2": w2})
    return rows


def test2(gold: dict[str, list[dict]]) -> list[dict]:
    rng = random.Random(SEED + 1)
    print("\nTEST 2: syntetiske homografer (substantivform + verbform med kjent fasit)")
    print("  feil = anslått minus faktisk substantivandel, i prosentpoeng; «balansert» = fasit mellom 20 og 80 %")
    print("  sum/obs = sum av ukappede anslag delt på observert frekvens\n")
    out = []
    for ns, vs, label in HOMOGRAPH_TYPES:
        pairs = [(rng.choice(gold["subst"]), rng.choice(gold["verb"])) for _ in range(N_PAIRS)]
        print(f"  {label}")
        for m in METHODS:
            errs, errs_bal, ratios, majority = [], [], [], []
            for n, v in pairs:
                tn, tv = n["f"][ns], v["f"][vs]
                obs = tn + tv
                en, ev = n["est"][m][ns], v["est"][m][vs]
                ratios.append((en + ev) / obs)
                if m == "regler":  # dekomponereren kapper hvert anslag ved observert frekvens
                    en, ev = min(en, obs), min(ev, obs)
                true_share = tn / obs
                est_share = en / (en + ev) if en + ev > 0 else 0.5
                e = 100 * (est_share - true_share)
                errs.append(e)
                majority.append((est_share > 0.5) == (true_share > 0.5))
                if 0.2 <= true_share <= 0.8:
                    errs_bal.append(e)
                out.append({"type": label, "metode": m, "subst": n["grunnform"], "verb": v["grunnform"],
                            "fasit_subst": true_share, "anslag_subst": est_share, "feil_pp": e, "sum_obs": (en + ev) / obs})
            ab = [abs(x) for x in errs]
            abb = [abs(x) for x in errs_bal]
            q = st.quantiles(ratios, n=4)
            print(f"    {m:7s} median |feil| {st.median(ab):4.1f} pp, 90-pers. {st.quantiles(ab, n=10)[-1]:4.1f} pp, "
                  f"innen 10 pp {pct(sum(x <= 10 for x in ab) / len(ab))}, rett flertallsleksem {pct(sum(majority) / len(majority))}, skjevhet {st.median(errs):+5.1f} pp | "
                  f"balansert (N={len(abb)}): median |feil| {st.median(abb):4.1f} pp, innen 10 pp {pct(sum(x <= 10 for x in abb) / len(abb))} | "
                  f"sum/obs median {st.median(ratios):.2f} (IQR {q[0]:.2f}–{q[2]:.2f})")
    return out


def write_tsv(rows1: list[dict], rows2: list[dict]) -> Path:
    OUT_TSV.parent.mkdir(exist_ok=True)
    with OUT_TSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["test", "type", "metode", "subst", "verb", "fasit_subst", "anslag_subst", "feil_pp", "sum_obs"])
        for r in rows2:
            w.writerow(["2", r["type"], r["metode"], r["subst"], r["verb"], f"{r['fasit_subst']:.4f}",
                        f"{r['anslag_subst']:.4f}", f"{r['feil_pp']:.2f}", f"{r['sum_obs']:.3f}"])
    return OUT_TSV


def main() -> None:
    gold = load_gold()
    print(f"Gullstandard: {len(gold['subst'])} substantiv, {len(gold['verb'])} verb (alle kategorier belagt i nb_totals)")
    add_estimates(gold)
    rows1 = test1(gold)
    rows2 = test2(gold)
    print(f"\nSkrev {write_tsv(rows1, rows2)}")


if __name__ == "__main__":
    main()
