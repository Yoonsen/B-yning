#!/usr/bin/env python3
"""
Norsk ordvev (bokmål, v1.1.2) koblet til bøyningsprofilene for substantiv.

    python3 -m sqlite.ordvev [--flertall]

Ordvev er en wordnet oversatt fra DanNet (lisens: DanNet 1.0, se LICENCE_dannet.txt i
datamappen; rådataene ligger utenfor Git). Hver betydning (synset) har en ontologisk type fra
EuroWordNet, f.eks. «Natural+Substance» eller «Animal+Object». Vi grovklassifiserer typene og ser
om bøyningsprofilen (ent ub / ent be / fl ub / fl be i bokkorpuset, resultater/substantivtyper.tsv)
avhenger av semantisk klasse: masse vs. telling, person, dyr, sted, kroppsdel, abstrakt.

Et lemma får en klasse bare når alle betydningene i Ordvev faller i samme grovklasse
(ellers «flertydig»). Navngitte enheter (synset med instanceOf) er utelatt.
"""

import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DAT = ROOT / "norsk_ordvev_nob_1.1.2" / "dat"
PROFILES = ROOT / "resultater" / "substantivtyper.tsv"
OUT_TSV = ROOT / "resultater" / "ordvev_klasser.tsv"
CELLS = ["ent_ub", "ent_be", "fl_ub", "fl_be"]

# Rekkefølgen betyr noe: første treff vinner
COARSE = [
    ("substans", ("Substance", "Liquid", "Gas")),
    ("kroppsdel", ("BodyPart",)),
    ("person", ("Human",)),
    ("dyr", ("Animal",)),
    ("plante", ("Plant",)),
    ("sted/bygning", ("Place", "Building")),
    ("tid", ("Time",)),
    ("egenskap", ("Property",)),
    ("hendelse", ("Event", "Dynamic", "Static")),
    ("gjenstand", ("Artifact", "Object", "Comestible", "Garment", "Container", "Instrument", "Vehicle")),
    ("abstrakt", ("3rdOrderEntity", "Mental", "Communication")),
]


def _tab(name):
    with (DAT / f"{name}.tab").open(encoding="utf-8") as f:
        for line in f:
            yield line.rstrip("\n").split("\t")


def coarse(ont: str) -> str:
    parts = set(ont.replace("(", "+").replace(")", "").split("+"))
    for cls, keys in COARSE:
        if any(k in part for k in keys for part in parts):  # «Event» treffer Bounded-/UnboundedEvent
            return cls
    return "annet"


def load_noun_senses() -> dict[str, list[str]]:
    """grunnform -> liste av ontologiske typer (én per betydning), bare fellesnavn."""
    instances = {r[0] for r in _tab("relations") if r[1] == "instanceOf"}
    ont = {r[0]: r[1] for r in _tab("synsets")}
    ont.update({r[0]: r[1] for r in _tab("dummies")})
    words = {r[0]: r[1] for r in _tab("words") if len(r) > 2 and r[2] == "Noun"}
    senses = defaultdict(list)
    for r in _tab("wordsenses"):
        wid, sid = r[1], r[2]
        if wid in words and sid not in instances and sid in ont:
            senses[words[wid]].append(ont[sid])
    return senses


def classify(senses: dict[str, list[str]], majority: bool = False) -> dict[str, tuple[str, int]]:
    """Klasse per lemma. Streng: alle betydninger i samme grovklasse. majority=True: klassen med
    flest betydninger (uavgjort gir «flertydig»), som tar med hyppige, polyseme ord som hånd og hode."""
    out = {}
    for w, onts in senses.items():
        cnt = Counter(coarse(o) for o in onts).most_common()
        if len(cnt) == 1 or (majority and cnt[0][1] > cnt[1][1]):
            out[w] = (cnt[0][0], len(onts))
        else:
            out[w] = ("flertydig", len(onts))
    return out


def run(majority: bool = False):
    cls = classify(load_noun_senses(), majority)
    rows = []
    with PROFILES.open(encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            tot = float(r["book_total"])
            if tot <= 0:
                continue
            c, n = cls.get(r["grunnform"], ("ikke i Ordvev", 0))
            shares = [float(r[f"book_{k}"]) / tot for k in CELLS]
            rows.append({"lemma_id": r["lemma_id"], "grunnform": r["grunnform"], "klasse": c, "n_betydninger": n,
                         "book_total": int(tot), **{k: round(s, 4) for k, s in zip(CELLS, shares)},
                         "topp": CELLS[max(range(4), key=lambda i: shares[i])]})
    with (OUT_TSV.with_name(OUT_TSV.stem + "_flertall.tsv") if majority else OUT_TSV).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    return rows


def report(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[r["klasse"]].append(r)
    print(f"{len(rows)} substantiv med profil; dekning i Ordvev: "
          f"{sum(r['klasse'] != 'ikke i Ordvev' for r in rows) / len(rows):.1%}")
    print(f"{'klasse':14s} {'N':>5s}  " + "  ".join(f"{k:>6s}" for k in CELLS) + "   flertall  topp: " + " ".join(CELLS))
    for c, rs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        mean = [sum(r[k] for r in rs) / len(rs) for k in CELLS]
        top = Counter(r["topp"] for r in rs)
        print(f"{c:14s} {len(rs):5d}  " + "  ".join(f"{100 * m:6.1f}" for m in mean)
              + f"   {100 * (mean[2] + mean[3]):6.1f}   " + " ".join(f"{100 * top[k] / len(rs):5.0f}" for k in CELLS))


if __name__ == "__main__":
    import sys

    report(run(majority="--flertall" in sys.argv))
