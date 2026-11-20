#!/usr/bin/env python3
"""
Verbtyper: gullstandard (Sett A), de seks rangeringstypene og rang-stabilitet (1950–2020).

Gjenskaper tallene i rapport_verbtyper.md §2–4. Hovedkorpus er bokkorpuset 1950–2020 (dhlab ngram_book);
nb_totals brukes til utvalget (100 000-grensen) og vises til sammenligning. Kjør fra repo-roten:

    python3 -m sqlite.verbtyper            # alt, inkl. n-gram for bokkorpuset; skriver resultater/verbtyper.tsv
    python3 -m sqlite.verbtyper --offline  # bare ordbank + nb_totals

Gullstandard:
  1. pos = 'verb', alle fire kjerneformer finnes (1 inf, 2 pres, 4 pret, 5 perf-part).
  2. Internt distinkte: ingen ordform står i to av de fire kategoriene (utelukker -et/-a-verb der pret = perf-part).
  3. inf + pres + pret >= MIN_TOTAL i nb_totals.
  4. inf, pres og pret deler ikke ordform med noe annet lemma (antall_lemma_id = 1)      -> N = 606
  5. ... og heller ikke perf-part                                                      -> N = 580 (Sett A)
  6. ... og hver av de fire kategoriene har minst én form i nb_totals                   -> N = 533
Alternative former i samme kategori (vet/veit, kastet/kasta) summeres.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from sqlite.queries import get_conn

CORE = (1, 2, 4, 5)
TENSE = {1: "inf", 2: "pres", 4: "pret"}
PERIOD = (1950, 2020)
MIN_TOTAL = 100_000
OUT_DIR = Path(__file__).resolve().parent.parent / "resultater"

# Typekoder brukt i rapporten: hovedtype etter 1. plass, A/B etter 2. plass.
TYPE_CODES = {
    (1, 2, 4): "1A", (1, 4, 2): "1B",
    (4, 1, 2): "2A", (4, 2, 1): "2B",
    (2, 1, 4): "3A", (2, 4, 1): "3B",
}

# Verbene i tabellen i rapport_verbtyper.md §4 (Sett A og Sett B).
REPORT_VERBS = [
    "vurdere", "forstå", "oppnå", "utføre", "foreta", "bidra", "diskutere", "forklare", "gjøre", "lese", "spise",
    "undersøke", "innføre", "ta", "kjøpe",
    "overta", "vedta", "forlate", "gjenta", "skjule", "forsøke", "si",
    "forsvinne", "ankomme", "rope", "smile", "omkomme", "komme", "gå",
    "bety", "fungere", "oppleve", "innebære", "anbefale",
    "trenge", "bestå", "foregå", "foreligge", "ha", "vite", "ligge",
]


def load_verbs(conn: sqlite3.Connection) -> dict[int, dict]:
    rows = conn.execute(
        """
        SELECT DISTINCT lf.lemma_id, lf.grunnform, lf.boy_nummer, lf.oppslag, o.antall_lemma_id, n.freq
        FROM lemma_former lf
        JOIN ordform_flertydighet o ON o.oppslag = lf.oppslag
        LEFT JOIN nb_totals n ON n.oppslag = lf.oppslag
        WHERE lf.pos = 'verb' AND lf.boy_nummer IN (1, 2, 4, 5)
        """
    ).fetchall()
    verbs: dict[int, dict] = {}
    for lid, gf, slot, form, amb, freq in rows:
        d = verbs.setdefault(lid, {"lemma_id": lid, "grunnform": gf, "forms": defaultdict(dict), "amb": {}})
        d["forms"][slot][form] = freq  # None = ikke i nb_totals
        d["amb"][form] = int(amb)
    for d in verbs.values():
        all_forms = [f for s in CORE for f in d["forms"].get(s, {})]
        d["internally_distinct"] = len(all_forms) == len(set(all_forms))
        d["nb_slot"] = {s: sum(v or 0 for v in d["forms"].get(s, {}).values()) for s in CORE}
    return verbs


def unambiguous(d: dict, slots) -> bool:
    return all(d["amb"][f] == 1 for s in slots for f in d["forms"][s])


def select_sets(verbs: dict[int, dict]) -> tuple[dict[str, list[dict]], list[tuple[str, int]]]:
    steps = []
    c = [d for d in verbs.values() if all(s in d["forms"] for s in CORE)]
    steps.append(("alle fire kjerneformer finnes", len(c)))
    c = [d for d in c if d["internally_distinct"]]
    steps.append(("internt distinkte (pret != perf-part osv.)", len(c)))
    c = [d for d in c if sum(d["nb_slot"][s] for s in TENSE) >= MIN_TOTAL]
    steps.append((f"inf+pres+pret >= {MIN_TOTAL:,} i nb_totals".replace(",", " "), len(c)))
    n606 = [d for d in c if unambiguous(d, TENSE)]
    steps.append(("inf, pres, pret globalt entydige", len(n606)))
    n580 = [d for d in n606 if unambiguous(d, (5,))]
    steps.append(("+ perf-part entydig (Sett A)", len(n580)))
    n533 = [d for d in n580 if all(any(v for v in d["forms"][s].values()) for s in CORE)]
    steps.append(("+ alle fire kategorier i nb_totals", len(n533)))
    return {"606": n606, "580": n580, "533": n533}, steps


def ranking(freqs: dict[int, float]) -> tuple[int, ...]:
    return tuple(sorted(TENSE, key=lambda s: -freqs[s]))


def type_distribution(ds: list[dict], key: str) -> dict[str, float]:
    cnt = Counter(TYPE_CODES[ranking(d[key])] for d in ds if sum(d[key][s] for s in TENSE) > 0)
    n = sum(cnt.values())
    return {t: cnt[t] / n for t in sorted(TYPE_CODES.values())}


def add_book_profiles(ds: list[dict]) -> None:
    from sqlite.ngram import fetch_ngram_dhlab

    words = sorted({f for d in ds for s in TENSE for f in d["forms"][s]})
    series = fetch_ngram_dhlab(words, period=PERIOD, batch_size=80)
    years = range(PERIOD[0], PERIOD[1] + 1)
    for d in ds:
        yearly = {y: {s: sum(series[f][y] for f in d["forms"][s]) for s in TENSE} for y in years}
        d["book_slot"] = {s: sum(yearly[y][s] for y in years) for s in TENSE}
        valid = [y for y in years if sum(yearly[y].values()) > 0]
        if not valid or sum(d["book_slot"].values()) == 0:
            continue
        r = ranking(d["book_slot"])
        d["book_rank"] = r
        d["n_years"] = len(valid)
        ranks = [ranking(yearly[y]) for y in valid]
        d["top_stab"] = sum(x[0] == r[0] for x in ranks) / len(valid)
        d["full_stab"] = sum(x == r for x in ranks) / len(valid)


def pct(x: float) -> str:
    return f"{100 * x:.1f}".replace(".", ",") + " %"


def print_types(sets: dict[str, list[dict]], key: str) -> None:
    print(f"\nTypefordeling ({key}):")
    dists = {name: type_distribution(ds, key) for name, ds in sets.items()}
    print("  type  " + "  ".join(f"N={name:>4s}" for name in sets))
    for t in sorted(TYPE_CODES.values()):
        print(f"  {t:4s}  " + "  ".join(f"{pct(dists[name][t]):>8s}" for name in sets))
    ds = sets["580"]
    print("\n  Sett A (N = 580): 2. plass innen hver hovedtype")
    for top in TENSE:
        sub = Counter(ranking(d[key])[1] for d in ds if ranking(d[key])[0] == top)
        tot = sum(sub.values())
        print(f"    {TENSE[top]} på topp ({pct(tot / len(ds))}): " + ", ".join(f"{TENSE[s]} {pct(c / tot)}" for s, c in sub.most_common()))
    print("\n  Sett A (N = 580): snittprofil inf / pres / pret per type")
    for code in sorted(TYPE_CODES.values()):
        grp = [d for d in ds if TYPE_CODES[ranking(d[key])] == code]
        avg = [sum(d[key][s] / sum(d[key][x] for x in TENSE) for d in grp) / len(grp) for s in TENSE]
        top_ex = sorted(grp, key=lambda d: -sum(d[key][s] for s in TENSE))[:10]
        print(f"    {code}: {' / '.join(pct(a) for a in avg)}  | {', '.join(d['grunnform'] for d in top_ex)}")


def report_verbs(verbs: dict[int, dict], sett_a: list[dict]) -> list[dict]:
    """Bokprofil og stabilitet for verbene i rapportens §4-tabell (også Sett B-verb)."""
    a_ids = {d["lemma_id"] for d in sett_a}
    out = []
    for gf in REPORT_VERBS:
        cands = [d for d in verbs.values() if d["grunnform"] == gf and all(s in d["forms"] for s in TENSE)]
        if not cands:
            print(f"  {gf}: ikke funnet")
            continue
        d = max(cands, key=lambda x: sum(x["nb_slot"][s] for s in TENSE))
        d["sett"] = "A" if d["lemma_id"] in a_ids else "B"
        out.append(d)
    add_book_profiles(out)
    print("\nVerbene i rapportens §4 (bokkorpuset 1950–2020):")
    print(f"  {'verb':10s} sett type  {'inf':>7s} {'pres':>7s} {'pret':>7s}  {'topp-stab':>9s} {'full-stab':>9s}")
    for d in out:
        b = d["book_slot"]
        t = sum(b.values())
        print(f"  {d['grunnform']:10s}  {d['sett']}   {TYPE_CODES[d['book_rank']]}  "
              + " ".join(f"{pct(b[s] / t):>7s}" for s in TENSE)
              + f"  {pct(d['top_stab']):>9s} {pct(d['full_stab']):>9s}  ({d['n_years']} år)")
    return out


def write_tsv(sett_a: list[dict]) -> Path:
    OUT_DIR.mkdir(exist_ok=True)
    path = OUT_DIR / "verbtyper.tsv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["lemma_id", "grunnform", "inf", "pres", "pret", "perf_part",
                    "nb_inf", "nb_pres", "nb_pret", "type_nb",
                    "book_inf", "book_pres", "book_pret", "type_book", "n_aar", "topp_stab", "full_stab"])
        for d in sorted(sett_a, key=lambda d: -sum(d["nb_slot"][s] for s in TENSE)):
            forms = [",".join(sorted(d["forms"][s])) for s in CORE]
            book = d.get("book_slot", {})
            w.writerow([d["lemma_id"], d["grunnform"], *forms,
                        *(d["nb_slot"][s] for s in TENSE), TYPE_CODES[ranking(d["nb_slot"])],
                        *(int(book.get(s, 0)) for s in TENSE),
                        TYPE_CODES[d["book_rank"]] if "book_rank" in d else "",
                        d.get("n_years", 0), round(d.get("top_stab", 0), 3), round(d.get("full_stab", 0), 3)])
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="bare nb_totals, ingen n-gram-kall")
    args = ap.parse_args()
    conn = get_conn()
    conn.row_factory = None
    verbs = load_verbs(conn)
    sets, steps = select_sets(verbs)
    print("Utvalg:")
    for label, n in steps:
        print(f"  {label:45s} {n:6d}")
    if args.offline:
        print_types(sets, "nb_slot")
        return
    add_book_profiles(sets["606"])  # 580 og 533 er delmengder og deler objektene
    print_types({k: [d for d in v if "book_rank" in d] for k, v in sets.items()}, "book_slot")
    full = [d for d in sets["580"] if "book_rank" in d and d["n_years"] == 71]
    if full:
        print(f"\nSett A i bokkorpuset: {len(full)} verb belagt alle 71 år.")
        print(f"  samme 1. plass alle år: {sum(d['top_stab'] == 1 for d in full)}  "
              f"samme hele rangering alle år: {sum(d['full_stab'] == 1 for d in full)}")
    report_verbs(verbs, sets["580"])
    print("\n--- Til sammenligning: samme utvalg i nb_totals (hele NB-korpuset) ---")
    print_types(sets, "nb_slot")
    print(f"\nSkrev {write_tsv(sets['580'])}")


if __name__ == "__main__":
    main()
