#!/usr/bin/env python3
"""
Kombinert anslag for substantiv/verb-homografer: paradigmeanslaget og bigramanslaget (logg del 59).

    python3 -m sqlite.kombinert                 # validering mot OBT
    python3 -m sqlite.kombinert --ord dør tro   # anslag for enkeltord

To uavhengige anslag for verbandelen v av formen O:
  1. Paradigmet (`decomposer.estimate_wordform_shares`, bokkorpuset): v_P, usikkerhet fra profilen
     (σ per kandidat kalibrert på kunstige homografer, logit-sd = √(σ_V² + σ_S²)).
  2. Bigrammene (`bigram_kontekst.decompose_residual`, NB N-gram): v_B = B_V / r_V / f(O), usikkerhet
     fra spredningen i kontekstraten mellom verb.
Feilkildene er ulike (ordets bøyningsprofil mot ordets kontekster), så vi kombinerer i logit-skala
med invers varians:  logit v_K = (w_P logit v_P + w_B logit v_B) / (w_P + w_B),  w = 1 / sd².

Validering: former der OBT-korpuset gir ett substantiv og ett verb (til sammen ≥ 90 %), og verbet
står i infinitiv eller presens. Fasit = OBTs verbandel av de to. NB: fasiten er fra et annet korpus
(8,4 mill. ord), så noe av avviket er reell forskjell mellom korpusene.
"""

import csv
import math
import re
import statistics as st
from pathlib import Path

import numpy as np

import sqlite.decomposer as dec
from sqlite.bigram_kontekst import cue_rates, decompose_residual
from sqlite.queries import get_conn
from sqlite.tidsserie import calibrate_sigma

ROOT = Path(__file__).resolve().parent.parent
OBT_TSV = ROOT / "resultater" / "dekomponering_obt_former.tsv"
OUT_TSV = ROOT / "resultater" / "kombinert_validering.tsv"
Z80 = 1.2816
EPS = 1e-3
MAX_FORMS = 150


def logit(p: float) -> float:
    p = min(max(p, EPS), 1 - EPS)
    return math.log(p / (1 - p))


def inv_logit(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def verb_cell(conn, form: str, verb: str) -> int | None:
    cells = {r[0] for r in conn.execute(
        "SELECT boy_nummer FROM lemma_former WHERE oppslag = ? AND grunnform = ? AND boy_gruppe = 'verb, normal'",
        (form, verb))}
    return 1 if 1 in cells else (2 if 2 in cells else None)


def noun_cell(conn, form: str, noun: str) -> int | None:
    cells = sorted(r[0] for r in conn.execute(
        "SELECT boy_nummer FROM lemma_former WHERE oppslag = ? AND grunnform = ? AND pos = 'subst'", (form, noun)))
    return cells[0] if cells else None


def paradigm_estimate(form: str, noun: str, verb: str, sigma: dict, conn) -> dict | None:
    est = dec.estimate_wordform_shares(form, conn=conn, corpus="book")
    by = {(c["grunnform"], c["pos"]): c for c in est["candidates"]}
    n, v = by.get((noun, "subst")), by.get((verb, "verb"))
    if n is None or v is None or n["raw_est"] + v["raw_est"] <= 0:
        return None
    p = v["raw_est"] / (n["raw_est"] + v["raw_est"])
    sd = math.sqrt(sigma.get(v["method_used"], 0.93) ** 2 + sigma.get(n["method_used"], 0.93) ** 2)
    return {"v": p, "sd": sd, "calibration": est["calibration"]}


def bigram_estimate(form: str, noun: str, verb: str, ncell: int, vcell: int, rates: dict) -> dict:
    cells = [(f"{noun} (subst)", noun, ("subst", ncell)), (f"{verb} (verb)", verb, ("verb", vcell))]
    r = decompose_residual(form, cells, rates)
    lo, hi = logit(r["lo"]), logit(r["hi"])
    return {"v": r["verb_share"], "sd": max((hi - lo) / (2 * Z80), 0.05), "lb": r["lower_bound"], "ub": r["upper_bound"]}


# Skalering av usikkerheten (logg del 59): sd fra kalibreringen på kunstige homografer (paradigmet) og
# fra spredningen i kontekstraten (bigram) var for smal mot OBT; fasiten lå innenfor 80 %-intervallet i
# 46 og 42 % av formene. Faktorene er satt slik at 80 % av OBT-fasitene faller innenfor (samme 150 former,
# altså ikke testet på nye data). Avviket inkluderer også forskjellen mellom korpusene.
SD_SCALE = {"P": 2.31, "B": 4.34}


def scaled(e: dict | None, key: str) -> dict | None:
    return None if e is None else {**e, "sd": e["sd"] * SD_SCALE[key]}


# Empirisk usikkerhet for bigramanslaget mot OBT (150 former): median 5,0 pp, 80-persentil 14,5 pp;
# for jevnt fordelte former (OBT-verbandel 20–80 %, N = 47) median 12,8 pp og 80-persentil 29 pp.
BIGRAM_ERR_PP = {"alle": (5.0, 14.5), "jevne": (12.8, 29.0)}


def best_estimate(est_p: dict | None, est_b: dict | None) -> dict | None:
    """
    Anbefalt anslag (logg del 59): bigramanslaget når det finnes, ellers paradigmet. Kombinasjonen med
    invers varians ble dårligere enn bigrammene alene når usikkerheten var kalibrert (median 5,4 mot
    5,0 pp, 90-persentil 31,5 mot 24,5 pp), fordi paradigmeanslaget har tunge haler.
    """
    if est_b is not None:
        half = BIGRAM_ERR_PP["jevne" if 0.2 <= est_b["v"] <= 0.8 else "alle"][1] / 100
        return {"v": est_b["v"], "lo": max(0.0, est_b["v"] - half), "hi": min(1.0, est_b["v"] + half), "kilde": "bigram"}
    if est_p is not None:
        lo, hi = interval(scaled(est_p, "P"))
        return {"v": est_p["v"], "lo": lo, "hi": hi, "kilde": "paradigme"}
    return None


def combine(est_p: dict | None, est_b: dict | None) -> dict | None:
    est_p, est_b = scaled(est_p, "P"), scaled(est_b, "B")
    parts = [e for e in (est_p, est_b) if e is not None]
    if not parts:
        return None
    w = [1 / e["sd"] ** 2 for e in parts]
    x = sum(wi * logit(e["v"]) for wi, e in zip(w, parts)) / sum(w)
    sd = 1 / math.sqrt(sum(w))
    return {"v": inv_logit(x), "sd": sd, "lo": inv_logit(x - Z80 * sd), "hi": inv_logit(x + Z80 * sd)}


def interval(e: dict) -> tuple[float, float]:
    x = logit(e["v"])
    return inv_logit(x - Z80 * e["sd"]), inv_logit(x + Z80 * e["sd"])


def select_forms(conn) -> list[dict]:
    pat = re.compile(r"(.+?) \((\w+)\) (\d+)")
    out = []
    for r in csv.DictReader(OBT_TSV.open(encoding="utf-8"), delimiter="\t"):
        if float(r["obt_innhold"]) < 0.9:
            continue
        lex = [m.groups() for m in (pat.match(x.strip()) for x in r["obt"].split(",")) if m]
        if len(lex) < 2:
            continue
        (g1, p1, s1), (g2, p2, s2) = lex[:2]
        if {p1, p2} != {"subst", "verb"} or int(s1) + int(s2) < 90:
            continue
        noun, verb = (g1, g2) if p1 == "subst" else (g2, g1)
        sv = int(s1 if p1 == "verb" else s2)
        vc, nc = verb_cell(conn, r["form"], verb), noun_cell(conn, r["form"], noun)
        if vc is None or nc is None:
            continue
        out.append({"form": r["form"], "n": float(r["n"]), "noun": noun, "verb": verb, "ncell": nc, "vcell": vc,
                    "obt_v": sv / (int(s1) + int(s2))})
    return sorted(out, key=lambda d: -d["n"])[:MAX_FORMS]


def validate() -> None:
    conn = get_conn()
    sigma, rates = calibrate_sigma(), cue_rates()
    forms = select_forms(conn)
    print(f"Validering: {len(forms)} substantiv/verb-homografer (OBT ≥ 90 % på de to, verb i inf/pres)\n")
    res = []
    for d in forms:
        try:
            p = paradigm_estimate(d["form"], d["noun"], d["verb"], sigma, conn)
            b = bigram_estimate(d["form"], d["noun"], d["verb"], d["ncell"], d["vcell"], rates)
        except Exception as e:  # noqa: BLE001 – enkeltord med manglende data skal ikke stoppe valideringen
            print(f"  hopper over {d['form']}: {e}")
            continue
        k = combine(p, b)
        res.append({**d, "P": p, "B": b, "K": k})
    with OUT_TSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["form", "n_obt", "subst", "verb", "obt_verb", "paradigme_verb", "paradigme_sd", "bigram_verb",
                    "bigram_sd", "kombinert_verb", "kombinert_lo", "kombinert_hi"])
        for r in res:
            w.writerow([r["form"], f"{r['n']:.0f}", r["noun"], r["verb"], f"{r['obt_v']:.3f}",
                        f"{r['P']['v']:.3f}" if r["P"] else "", f"{r['P']['sd']:.2f}" if r["P"] else "",
                        f"{r['B']['v']:.3f}", f"{r['B']['sd']:.2f}", f"{r['K']['v']:.3f}",
                        f"{r['K']['lo']:.3f}", f"{r['K']['hi']:.3f}"])
    both = [r for r in res if r["P"] is not None]
    # Faktor som gir 80 % dekning: 80-persentilen av |z| / 1,2816
    need = {}
    for key in ("P", "B"):
        z = [abs(logit(r["obt_v"]) - logit(r[key]["v"])) / r[key]["sd"] for r in both]
        need[key] = float(np.percentile(z, 80)) / Z80
    print(f"Skaleringsfaktor for 80 % dekning: paradigme {need['P']:.2f}, bigram {need['B']:.2f} (i bruk: {SD_SCALE})\n")
    print("| metode | former | median avvik | 90-persentil | riktig flertallsleksem | fasit innenfor 80 %-intervall |")
    print("|---|---|---|---|---|---|")
    for name, key in (("paradigme", "P"), ("bigram", "B"), ("kombinert", "K")):
        err = [abs(r[key]["v"] - r["obt_v"]) * 100 for r in both]
        maj = [(r[key]["v"] > 0.5) == (r["obt_v"] > 0.5) for r in both]
        cov = []
        for r in both:
            lo, hi = interval(scaled(r[key], key)) if key != "K" else (r["K"]["lo"], r["K"]["hi"])
            cov.append(lo <= r["obt_v"] <= hi)
        print(f"| {name} | {len(both)} | {st.median(err):.1f} pp | {np.percentile(err, 90):.1f} pp | "
              f"{100 * sum(maj) / len(maj):.0f} % | {100 * sum(cov) / len(cov):.0f} % |")
    print(f"\nSkrev {OUT_TSV}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--ord", nargs="*")
    a = ap.parse_args()
    if a.ord:
        conn, sigma, rates = get_conn(), calibrate_sigma(), cue_rates()
        spec = {"dør": ("dør", "dø", 1, 2), "tro": ("tro", "tro", 1, 1)}
        for w in a.ord:
            noun, verb, nc, vc = spec[w]
            p = paradigm_estimate(w, noun, verb, sigma, conn)
            b = bigram_estimate(w, noun, verb, nc, vc, rates)
            k = combine(p, b)
            be = best_estimate(p, b)
            print(f"«{w}» anbefalt ({be['kilde']}): verb {100 * be['v']:.0f} % ({100 * be['lo']:.0f}–{100 * be['hi']:.0f})")
            print(f"«{w}» verbandel: paradigme {100 * p['v']:.0f} % (sd {p['sd']:.2f}), bigram {100 * b['v']:.0f} % "
                  f"(sd {b['sd']:.2f}), kombinert {100 * k['v']:.0f} % ({100 * k['lo']:.0f}–{100 * k['hi']:.0f})")
    else:
        validate()
