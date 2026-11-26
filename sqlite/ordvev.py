#!/usr/bin/env python3
"""
Norsk ordvev (bokmål, v1.1.2) koblet til bøyningsprofilene for substantiv.

    python3 -m sqlite.ordvev [--flertall]
    python3 -m sqlite.ordvev --obt      # profiler fra det OBT-taggede bokkorpuset

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
    """grunnform -> liste av ontologiske typer (én per betydning, i Ordvevs rekkefølge), bare fellesnavn."""
    instances = {r[0] for r in _tab("relations") if r[1] == "instanceOf"}
    ont = {r[0]: r[1] for r in _tab("synsets")}
    ont.update({r[0]: r[1] for r in _tab("dummies")})
    words = {r[0]: r[1] for r in _tab("words") if len(r) > 2 and r[2] == "Noun"}
    rows = []
    for r in _tab("wordsenses"):
        wsid, wid, sid = r[0], r[1], r[2]
        if wid in words and sid not in instances and sid in ont:
            rows.append((int(wsid) if wsid.isdigit() else 10**9, words[wid], ont[sid]))
    senses = defaultdict(list)
    for _, w, o in sorted(rows):  # første betydning er som regel hovedbetydningen (arvet fra DanNet)
        senses[w].append(o)
    return senses


def classify(senses: dict[str, list[str]], mode: str = "streng") -> dict[str, tuple[str, int]]:
    """Klasse per lemma.
    streng:   alle betydninger i samme grovklasse, ellers «flertydig».
    flertall: klassen med flest betydninger (uavgjort gir «flertydig»).
    første:   klassen til første betydning (hovedbetydningen); tar med polyseme ord som hånd og øye."""
    out = {}
    for w, onts in senses.items():
        cnt = Counter(coarse(o) for o in onts).most_common()
        if mode == "første":
            out[w] = (coarse(onts[0]), len(onts))
        elif len(cnt) == 1 or (mode == "flertall" and cnt[0][1] > cnt[1][1]):
            out[w] = (cnt[0][0], len(onts))
        else:
            out[w] = ("flertydig", len(onts))
    return out


def run(majority: bool = False):
    cls = classify(load_noun_senses(), "flertall" if majority else "streng")
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


OBT_DB = ROOT / "korpus" / "obt_frekvenser.db"
ORDBANK = ROOT / "sqlite" / "ordbank.db"


def obt_profiles(min_n: float = 50.0) -> list[dict]:
    """Substantivprofiler fra det OBT-taggede bokkorpuset (korpus/obt_frekvenser.db).

    Taggeren har skilt homografene, så også hyppige ord med flertydige former (hånd, by, mann)
    får en profil. Krever minst min_n forekomster i de fire cellene."""
    import sqlite3

    con = sqlite3.connect(OBT_DB)
    con.execute("ATTACH ? AS ob", (str(ORDBANK),))
    q = """SELECT k.lemma_id, k.boy_nummer, SUM(t.n * k.vekt)
           FROM obt_typer t JOIN type_kobling k USING (form, lemma, pos, trekk, partisipp)
           WHERE k.lemma_id IS NOT NULL AND k.boy_nummer BETWEEN 1 AND 4
             AND k.lemma_id IN (SELECT lemma_id FROM ob.lemma_former WHERE boy_gruppe = 'substantiv')
           GROUP BY 1, 2"""
    cells = defaultdict(lambda: [0.0] * 4)
    for lid, b, n in con.execute(q):
        cells[lid][b - 1] += n
    names = dict(con.execute("SELECT DISTINCT lemma_id, grunnform FROM ob.lemma_former WHERE boy_gruppe = 'substantiv'"))
    out = []
    for lid, v in cells.items():
        tot = sum(v)
        if tot >= min_n and len(names[lid]) > 1:  # bokstavnavn (a, r, s …) er OBT-feil for forkortelser
            out.append({"lemma_id": lid, "grunnform": names[lid], "total": tot, "shares": [x / tot for x in v]})
    return out


def run_obt(min_n: float = 50.0, mode: str = "første"):
    cls = classify(load_noun_senses(), mode)
    rows = []
    for p in obt_profiles(min_n):
        c, n = cls.get(p["grunnform"], ("ikke i Ordvev", 0))
        rows.append({"lemma_id": p["lemma_id"], "grunnform": p["grunnform"], "klasse": c, "n_betydninger": n,
                     "obt_total": round(p["total"], 1), **{k: round(s, 4) for k, s in zip(CELLS, p["shares"])},
                     "topp": CELLS[max(range(4), key=lambda i: p["shares"][i])]})
    rows.sort(key=lambda r: -r["obt_total"])
    with OUT_TSV.with_name("ordvev_klasser_obt.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    return rows


def report(rows, weight: str | None = None):
    groups = defaultdict(list)
    for r in rows:
        groups[r["klasse"]].append(r)
    print(f"{len(rows)} substantiv med profil; dekning i Ordvev: "
          f"{sum(r['klasse'] != 'ikke i Ordvev' for r in rows) / len(rows):.1%}")
    print(f"{'klasse':14s} {'N':>5s}  " + "  ".join(f"{k:>6s}" for k in CELLS) + "   flertall  topp: " + " ".join(CELLS))
    for c, rs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        wt = [r[weight] if weight else 1.0 for r in rs]
        mean = [sum(w * r[k] for w, r in zip(wt, rs)) / sum(wt) for k in CELLS]
        top = Counter(r["topp"] for r in rs)
        print(f"{c:14s} {len(rs):5d}  " + "  ".join(f"{100 * m:6.1f}" for m in mean)
              + f"   {100 * (mean[2] + mean[3]):6.1f}   " + " ".join(f"{100 * top[k] / len(rs):5.0f}" for k in CELLS))


if __name__ == "__main__":
    import sys

    if "--obt" in sys.argv:
        rows = run_obt()
        print("Uvektet (snitt per lemma):")
        report(rows)
        print("\nVektet etter forekomster:")
        report(rows, weight="obt_total")
    else:
        report(run(majority="--flertall" in sys.argv))
