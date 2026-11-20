#!/usr/bin/env python3
"""
Gullstandard for adjektiv, brukt som ankre i dekomponereren (hull 5 i tekst/mons_presentasjon_plan.md).

    python3 -m sqlite.adjektiv_gold

Bakgrunn: «døde» er både preteritum av *dø* og bestemt/flertall av adjektivet *død*. For å trekke
fra adjektivet trenger dekomponereren en modell for -e-formen av et adjektiv ut fra resten av
paradigmet. Vi bruker de vanlige adjektivene (boy_gruppe 'adjektiv') der alle positivformene er
entydige i hele ordbanken, og lærer log-regresjon på dem.

Kategorier (boy_gruppe 'adjektiv'): 1 = m/f ub ent (*stor*), 2/3 = fl og be ent (*store*, samme
form, slått sammen til «e-form»), 4 = nøyt ub ent (*stort*).

Skriptet skriver ut hvor godt e-formen kan anslås med kryssvalidering, med begge ankre (m/f og
nøytrum) og med bare nøytrum (som er det eneste entydige ankeret for *død*, fordi «død» også er et
substantiv).
"""

import math
import random
import re
import sqlite3
import statistics as st

import numpy as np

from sqlite.queries import get_conn

BG = "adjektiv"
SLOTS = {1: "m/f", 2: "e-form", 4: "nøyt"}
MIN_NB_TOTAL = 1000  # forhåndsfilter i nb_totals, så vi ikke henter tusenvis av sjeldne former
GRUNNFORM_RE = re.compile(r"[a-zæøå]+")
SEED = 20261120
FOLDS = 5


def select_adjective_gold(conn: sqlite3.Connection) -> list[dict]:
    """Adjektiv der m/f, e-form og nøytrum finnes, er innbyrdes ulike og helt entydige i ordbanken."""
    rows = conn.execute(
        """
        SELECT lf.lemma_id, lf.grunnform, lf.boy_nummer, lf.oppslag, ofl.antall_lemma_id
        FROM lemma_former lf JOIN ordform_flertydighet ofl ON ofl.oppslag = lf.oppslag
        WHERE lf.boy_gruppe = ? AND lf.boy_nummer IN (1, 2, 3, 4)
        """,
        (BG,),
    ).fetchall()
    lemmas: dict[int, dict] = {}
    for lid, gf, bnr, w, amb in rows:
        d = lemmas.setdefault(lid, {"lemma_id": lid, "grunnform": gf, "raw": {1: set(), 2: set(), 3: set(), 4: set()}, "max_amb": 1})
        d["raw"][bnr].add(w)
        d["max_amb"] = max(d["max_amb"], amb)
    gold = []
    for d in lemmas.values():
        r = d["raw"]
        if not (r[1] and r[2] and r[4]) or r[2] != r[3] or d["max_amb"] > 1:
            continue
        if not GRUNNFORM_RE.fullmatch(d["grunnform"]):
            continue
        if r[1] & r[2] or r[1] & r[4] or r[2] & r[4]:  # f.eks. ubøyelige adjektiv (*bra*)
            continue
        d["forms"] = {1: sorted(r[1]), 2: sorted(r[2]), 4: sorted(r[4])}
        gold.append(d)
    words = [w for d in gold for s in SLOTS for w in d["forms"][s]]
    nb = {}
    for i in range(0, len(words), 500):
        chunk = words[i:i + 500]
        q = f"SELECT oppslag, freq FROM nb_totals WHERE oppslag IN ({','.join('?' * len(chunk))})"
        nb.update(conn.execute(q, chunk).fetchall())
    gold = [d for d in gold if sum(nb.get(w, 0) for s in SLOTS for w in d["forms"][s]) >= MIN_NB_TOTAL]
    return sorted(gold, key=lambda d: d["grunnform"])


def cross_validate(profiles: list[dict[int, float]], anchors: tuple[int, ...], target: int = 2) -> dict:
    """5-delt kryssvalidering av log-regresjonen; returnerer skjevhet og typisk avvik (faktorer)."""
    rng = random.Random(SEED)
    idx = list(range(len(profiles)))
    rng.shuffle(idx)
    fold = {i: k % FOLDS for k, i in enumerate(idx)}
    lr = [0.0] * len(profiles)
    for k in range(FOLDS):
        train = [p for i, p in enumerate(profiles) if fold[i] != k]
        X = np.array([[1.0] + [math.log(p[a]) for a in anchors] for p in train])
        y = np.array([math.log(p[target]) for p in train])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        for i, p in enumerate(profiles):
            if fold[i] == k:
                est = math.exp(beta @ np.array([1.0] + [math.log(p[a]) for a in anchors]))
                lr[i] = math.log2(est / p[target])
    return {
        "n": len(profiles),
        "skjevhet": 2 ** st.median(lr),
        "typisk": 2 ** st.median(abs(x) for x in lr),
        "innen_2": sum(abs(x) <= 1 for x in lr) / len(lr),
        "p90": 2 ** st.quantiles([abs(x) for x in lr], n=10)[-1],
    }


def main() -> None:
    from sqlite.decomposer import gold_profiles

    conn = get_conn()
    print(f"Adjektiv-gullstandard (før korpusfilter): {len(select_adjective_gold(conn))} lemmaer")
    for corpus in ("book", "nb_totals"):
        prof = gold_profiles(BG, corpus, conn)
        ratios = sorted(p[2] / p[4] for p in prof)
        q = st.quantiles(ratios, n=4)
        print(f"\n{corpus}: N = {len(prof)} med alle tre kategorier belagt")
        print(f"  e-form / nøytrum: median {st.median(ratios):.1f} (IQR {q[0]:.1f}–{q[2]:.1f})")
        for anchors in ((1, 4), (4,)):
            r = cross_validate(prof, anchors)
            names = " + ".join(SLOTS[a] for a in anchors)
            print(f"  e-form fra {names:11s}: skjevhet ×{r['skjevhet']:.2f}, typisk avvik ×{r['typisk']:.2f}, "
                  f"innen ×2 {100 * r['innen_2']:.0f} %, 90-pers. ×{r['p90']:.1f}")


if __name__ == "__main__":
    main()
