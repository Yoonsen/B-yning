#!/usr/bin/env python3
"""
Substantivtyper: gullstandard, bøyningsprofiler og rang-stabilitet (1950–2020).

Motstykke til verbanalysen i rapport_verbtyper.md. Kjør fra repo-roten:

    python3 -m sqlite.substantivtyper            # bygger alt, skriver resultater/substantivtyper.tsv
    python3 -m sqlite.substantivtyper --offline  # bare ordbank + nb_totals, ingen n-gram-kall

Gullstandard (Sett A for substantiv):
  1. pos = 'subst', boy_gruppe = 'substantiv', alle fire kjerneformer finnes (1 ent ub, 2 ent be, 3 fl ub, 4 fl be).
  2. Ingen kjerneform deler ordform med noe annet lemma (ordform_flertydighet.antall_lemma_id = 1).
  3. Internt distinkte: ingen ordform går igjen i to av de fire kategoriene (utelukker f.eks. intetkjønn
     som «hus – hus», der ent ub = fl ub).
  4. Sum av kjerneformene >= MIN_TOTAL i nb_totals.
  5. Hver kategori belagt (> 0) i bokkorpuset 1950–2020. (Ikke i nb_totals: tabellen mangler
     sjeldne ordformer, så kravet der ville fjernet over halvparten av lemmaene.)
Alternative former i samme kategori (døren/døra, epla/eplene) summeres.

Profiler og stabilitet regnes i bokkorpuset (dhlab ngram_book, nob, 1950–2020), som for verbene.
"""

from __future__ import annotations

import argparse
import re
import csv
import sqlite3
from collections import Counter, defaultdict
from itertools import permutations
from pathlib import Path

from sqlite.queries import get_conn

SLOTS = {1: "ent_ub", 2: "ent_be", 3: "fl_ub", 4: "fl_be"}
PERIOD = (1950, 2020)
MIN_TOTAL = 100_000
# Et år teller bare med i stabilitetsmålet hvis lemmaet har minst så mange treff det året.
MIN_YEAR_TOTAL = 50
# Grunnformer som slippes gjennom: bare små bokstaver, minst tre tegn. Fjerner bokstavnavn (j, v, Z),
# forkortelser (TV, PR, SMS) og bindestrekssammensetninger (TV-serie, T-skjorte).
GRUNNFORM_RE = re.compile(r"[a-zæøåéü]{3,}")
# Falske venner funnet ved manuell gjennomgang av lemmaer med > 97 % ent_ub i bokkorpuset: ent ub-formen
# er i praksis et annet ord (riksmål/svensk, personnavn, engelsk tekst eller OCR-feil), så profilen er støy.
FALSKE_VENNER = {
    "nogen", "vor", "slig", "hon", "ukas", "mis",          # riksmål/svensk/dialekt
    "jan", "lian", "kir",                                   # navn
    "used", "during", "being", "half", "double", "unit", "talk", "air", "tee", "country",  # engelsk tekst
    "forst", "ril", "kal", "hodde", "emning", "joner", "vol",  # OCR-feil / forkortelser / uklare
}
OUT_DIR = Path(__file__).resolve().parent.parent / "resultater"


def load_noun_forms(conn: sqlite3.Connection) -> dict[int, dict]:
    """lemma_id -> {grunnform, forms: {slot: {oppslag: nb_freq}}, max_amb, internal_overlap}"""
    rows = conn.execute(
        """
        SELECT DISTINCT lf.lemma_id, lf.grunnform, lf.boy_nummer, lf.oppslag,
               o.antall_lemma_id, COALESCE(n.freq, 0) AS freq
        FROM lemma_former lf
        JOIN ordform_flertydighet o ON o.oppslag = lf.oppslag
        LEFT JOIN nb_totals n ON n.oppslag = lf.oppslag
        WHERE lf.pos = 'subst' AND lf.boy_gruppe = 'substantiv' AND lf.boy_nummer IN (1, 2, 3, 4)
        """
    ).fetchall()
    lemmas: dict[int, dict] = {}
    for lid, gf, slot, form, amb, freq in rows:
        d = lemmas.setdefault(lid, {"lemma_id": lid, "grunnform": gf, "forms": defaultdict(dict), "max_amb": 0})
        d["forms"][slot][form] = int(freq)
        d["max_amb"] = max(d["max_amb"], int(amb))
    for d in lemmas.values():
        seen = Counter(f for slot_forms in d["forms"].values() for f in slot_forms)
        d["internal_overlap"] = any(c > 1 for c in seen.values())
        d["nb_slot"] = {s: sum(d["forms"].get(s, {}).values()) for s in SLOTS}
        d["nb_total"] = sum(d["nb_slot"].values())
    return lemmas


def select_gold(lemmas: dict[int, dict]) -> tuple[list[dict], list[tuple[str, int]]]:
    steps = []
    cand = [d for d in lemmas.values() if all(s in d["forms"] for s in SLOTS)]
    steps.append(("alle fire kjerneformer finnes", len(cand)))
    cand = [d for d in cand if GRUNNFORM_RE.fullmatch(d["grunnform"]) and d["grunnform"] not in FALSKE_VENNER]
    steps.append(("vanlig grunnform, ikke falsk venn", len(cand)))
    cand = [d for d in cand if d["max_amb"] == 1]
    steps.append(("ingen form deles med annet lemma", len(cand)))
    cand = [d for d in cand if not d["internal_overlap"]]
    steps.append(("internt distinkte kategorier", len(cand)))
    cand = [d for d in cand if d["nb_total"] >= MIN_TOTAL]
    steps.append((f">= {MIN_TOTAL:,} treff i nb_totals".replace(",", " "), len(cand)))
    return sorted(cand, key=lambda d: -d["nb_total"]), steps


def ranking(slot_freqs: dict[int, float]) -> tuple[int, ...]:
    return tuple(sorted(SLOTS, key=lambda s: -slot_freqs[s]))


def rank_label(r: tuple[int, ...]) -> str:
    return " > ".join(SLOTS[s] for s in r)


def add_book_profiles(gold: list[dict]) -> None:
    from sqlite.ngram import fetch_ngram_dhlab

    words = [f for d in gold for s in SLOTS for f in d["forms"][s]]
    series = fetch_ngram_dhlab(words, period=PERIOD, batch_size=80)
    years = range(PERIOD[0], PERIOD[1] + 1)
    for d in gold:
        yearly = {y: {s: sum(series[f][y] for f in d["forms"][s]) for s in SLOTS} for y in years}
        tot = {s: sum(yearly[y][s] for y in years) for s in SLOTS}
        d["book_slot"] = tot
        d["book_total"] = sum(tot.values())
        if d["book_total"] == 0:
            continue
        d["rank"] = ranking(tot)
        valid = [y for y in years if sum(yearly[y].values()) >= MIN_YEAR_TOTAL]
        d["n_years"] = len(valid)
        if valid:
            ranks = [ranking(yearly[y]) for y in valid]
            d["top_stab"] = sum(r[0] == d["rank"][0] for r in ranks) / len(valid)
            d["top2_stab"] = sum(r[:2] == d["rank"][:2] for r in ranks) / len(valid)
            d["full_stab"] = sum(r == d["rank"] for r in ranks) / len(valid)


def pct(x: float) -> str:
    return f"{100 * x:5.1f} %"


def report(gold: list[dict], steps: list[tuple[str, int]], key: str) -> None:
    print("Utvalg (Sett A, substantiv):")
    for label, n in steps:
        print(f"  {label:40s} {n:6d}")
    ranked = [d for d in gold if d.get(key)]
    n = len(ranked)
    print(f"\nProfiler regnet på: {key} (N = {n})")

    if key == "book_slot":
        for d in ranked:
            d["_rank"] = d["rank"]
    else:
        for d in ranked:
            d["_rank"] = ranking(d["nb_slot"])

    tops = Counter(d["_rank"][0] for d in ranked)
    print("\nHovedtype (1. plass):")
    for s in SLOTS:
        print(f"  {SLOTS[s]:7s} {tops[s]:5d}  {pct(tops[s] / n)}")

    print("\nSekundær rangering (1. > 2.) innen hver hovedtype:")
    for s in SLOTS:
        sub = Counter(d["_rank"][1] for d in ranked if d["_rank"][0] == s)
        tot = sum(sub.values()) or 1
        print(f"  {SLOTS[s]} på topp: " + ", ".join(f"{SLOTS[t]} {pct(c / tot).strip()}" for t, c in sub.most_common()))

    full = Counter(d["_rank"] for d in ranked)
    print(f"\nFull rangering (av {len(list(permutations(SLOTS)))} mulige; {len(full)} belagt):")
    for r, c in full.most_common():
        ex = [d["grunnform"] for d in ranked if d["_rank"] == r][:8]
        avg = {s: sum(d[key][s] / sum(d[key].values()) for d in ranked if d["_rank"] == r) / c for s in SLOTS}
        prof = " / ".join(f"{100 * avg[s]:.1f}" for s in SLOTS)
        print(f"  {rank_label(r):36s} {c:4d} {pct(c / n)}  snitt {prof}  | {', '.join(ex)}")

    sg = sum(d[key][1] + d[key][2] for d in ranked) / sum(sum(d[key].values()) for d in ranked)
    print(f"\nEntall samlet (tokenvektet): {pct(sg)}")
    sg_lemmas = sum((d[key][1] + d[key][2]) > (d[key][3] + d[key][4]) for d in ranked)
    print(f"Lemmaer der entall > flertall: {sg_lemmas} av {n} ({pct(sg_lemmas / n).strip()})")

    if key == "book_slot":
        stab = [d for d in ranked if d.get("n_years", 0) >= 60]
        print(f"\nStabilitet 1950–2020 (lemmaer med >= 60 år med >= {MIN_YEAR_TOTAL} treff: N = {len(stab)})")
        for k, label in (("top_stab", "1. plass"), ("top2_stab", "1. og 2. plass"), ("full_stab", "hele rangeringen")):
            vals = sorted(d[k] for d in stab)
            med = vals[len(vals) // 2]
            full100 = sum(v == 1.0 for v in vals)
            print(f"  {label:18s} median {pct(med)}; 100 % av årene for {full100} lemmaer ({pct(full100 / len(stab)).strip()})")
        best = sorted(stab, key=lambda d: (-d["full_stab"], -d["book_total"]))[:25]
        print("  Mest stabile (hele rangeringen):")
        for d in best:
            print(f"    {d['grunnform']:14s} {rank_label(d['rank']):36s} full {pct(d['full_stab'])}  ({d['n_years']} år)")


def sett_b_profiles(conn: sqlite3.Connection, words: list[str]) -> None:
    """Profiler for kjente eksempelord som ikke er i Sett A, med kollisjonene angitt."""
    from sqlite.ngram import fetch_ngram_dhlab

    lemmas = load_noun_forms(conn)
    print("\nSett B / eksempelord (bokkorpuset 1950–2020):")
    for w in words:
        cands = [d for d in lemmas.values() if d["grunnform"] == w and all(s in d["forms"] for s in SLOTS)]
        if not cands:
            print(f"  {w}: ikke funnet")
            continue
        d = max(cands, key=lambda x: x["nb_total"])
        forms = [f for s in SLOTS for f in d["forms"][s]]
        ser = fetch_ngram_dhlab(forms, period=PERIOD)
        tot = {s: sum(sum(ser[f].values()) for f in d["forms"][s]) for s in SLOTS}
        t = sum(tot.values()) or 1
        coll = conn.execute(
            f"SELECT oppslag, antall_lemma_id FROM ordform_flertydighet WHERE oppslag IN ({','.join('?' * len(forms))}) AND antall_lemma_id > 1",
            forms,
        ).fetchall()
        prof = " / ".join(f"{SLOTS[s]} {100 * tot[s] / t:.1f}" for s in SLOTS)
        intern = " INTERN SYNKRETISME (samme form i flere kategorier, telt i hver)" if d["internal_overlap"] else ""
        print(f"  {w:10s} {rank_label(ranking(tot)):36s} {prof}  kollisjon: {', '.join(c[0] for c in coll) or '-'}{intern}")


def write_tsv(gold: list[dict]) -> Path:
    OUT_DIR.mkdir(exist_ok=True)
    path = OUT_DIR / "substantivtyper.tsv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["lemma_id", "grunnform", "former", "nb_total", "book_total",
                    "book_ent_ub", "book_ent_be", "book_fl_ub", "book_fl_be",
                    "rangering", "n_aar", "topp_stab", "topp2_stab", "full_stab"])
        for d in gold:
            if not d.get("book_total"):
                continue
            forms = "|".join(",".join(sorted(d["forms"][s])) for s in SLOTS)
            w.writerow([d["lemma_id"], d["grunnform"], forms, d["nb_total"], int(d["book_total"]),
                        *(int(d["book_slot"][s]) for s in SLOTS), rank_label(d["rank"]),
                        d.get("n_years", 0), *(round(d.get(k, 0), 3) for k in ("top_stab", "top2_stab", "full_stab"))])
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="bare nb_totals, ingen n-gram-kall")
    args = ap.parse_args()
    conn = get_conn()
    conn.row_factory = None
    gold, steps = select_gold(load_noun_forms(conn))
    if args.offline:
        gold = [d for d in gold if all(d["nb_slot"][s] > 0 for s in SLOTS)]
        steps.append(("hver kategori belagt i nb_totals", len(gold)))
        report(gold, steps, "nb_slot")
        return
    add_book_profiles(gold)
    gold = [d for d in gold if d.get("book_total") and all(d["book_slot"][s] > 0 for s in SLOTS)]
    steps.append(("hver kategori belagt i bokkorpuset", len(gold)))
    report(gold, steps, "book_slot")
    print(f"\nSkrev {write_tsv(gold)}")
    sett_b_profiles(conn, ["eple", "buss", "bil", "bok", "hus", "dag", "fisk", "sol", "kirke", "politi"])


if __name__ == "__main__":
    main()
