#!/usr/bin/env python3
"""
Stabilitet over tid i bøyningsprofiler: n-gram for bøker, med flertydige former fordelt etter
OBT-taggingen per tiår.

Fremgangsmåte for hvert eksempellemma (leksem = grunnform + ordklasse; homografer slått sammen):
  1. Kjernekategoriene i paradigmet (verb: inf, pres, pret, perf-part, imp; subst: ent/fl ub/be).
     Kategorier som deler form innen leksemet (f.eks. inf/imp), slås sammen.
  2. Entydige former (bare dette leksemet i Ordbanken): årlige frekvenser rett fra NBs n-gram for
     bøker (bokmål, 1950–2020, `sqlite/ngram.fetch_ngram_dhlab`).
  3. Flertydige former: n-gram-frekvensen × leksemets andel av formen i det OBT-taggede korpuset,
     regnet ut fra BØKENE (skjønn- og faglitteratur) i samme tiår. Har et tiår færre enn
     MIN_OBT_N koblede forekomster av formen, brukes andelen for hele perioden (flagget `samlet`).
     95 %-intervall (Wilson) per andel.

Varianter som sammenlignes:
  obt_tiaar   andel per tiår fra OBT (hovedvarianten)
  obt_fast    én andel for hele perioden fra OBT (antar at fordelingen ikke endrer seg)
  decomposer  decomposer (`method="regler"`) per tiår på n-gram-tallene for bøker
  naiv        rå formfrekvens uten fordeling

Stabilitet: gjennomsnittlig endring (total variasjonsavstand, prosentpoeng) mellom profilene i
påfølgende tiår, og største avvik fra gjennomsnittsprofilen.

Kjøres fra repo-roten (henter n-gram fra api.nb.no første gang, mellomlagres i sqlite/ngram_cache.db):
    python -m sqlite.stabilitet_obt
Skriver resultater/stabilitet_obt_andeler.tsv og resultater/stabilitet_obt_profiler.tsv.
"""

import argparse
import csv
import math
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlite.korpus_profiler import DEFAULT_SHARED_DB, ORDBANK_DB_PATH, _ro_uri, load_metadata
from sqlite.ngram import fetch_ngram_dhlab
from sqlite.valider_dekomponering_obt import _cell_groups, candidate_lexemes, lexeme_map

LEMMAS = [("fisk", "subst"), ("fisker", "subst"), ("dør", "subst"), ("krone", "subst"),
          ("dø", "verb"), ("gå", "verb"), ("svare", "verb"), ("sette", "verb"), ("bygge", "verb")]
PERIOD = (1950, 2020)
BOOK_TYPES = {"skjonnlitteratur", "faglitteratur"}
MIN_OBT_N = 30
DECADES = ["1950-1959", "1960-1969", "1970-1979", "1980-1989", "1990-1999", "2000-2009",
           "2010-2019", "2020-2026"]
VARIANTS = ["obt_tiaar", "obt_fast", "decomposer", "naiv"]
RESULT_DIR = Path(__file__).resolve().parent.parent / "resultater"


def decade_of(year: int) -> str:
    return DECADES[min((year - 1950) // 10, len(DECADES) - 1)]


def wilson(k: float, n: float, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


# ---------------------------------------------------------------------------
# 1. Andeler fra OBT per tiår (bøker)
# ---------------------------------------------------------------------------

def obt_counts(kconn, forms: list[str], lex: dict[int, tuple[str, str]],
               meta: dict[str, dict[str, str]]) -> dict[str, dict[str, dict[tuple, float]]]:
    """{form: {tiår eller 'alle': {leksem: n}}} for bøkene i det taggede korpuset (koblede analyser)."""
    out: dict[str, dict[str, dict[tuple, float]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    q = f"""
        SELECT t.doc_id, t.form, k.lemma_id, SUM(t.n * k.vekt)
        FROM obt_typer t JOIN type_kobling k USING (form, lemma, pos, trekk, partisipp)
        WHERE k.lemma_id IS NOT NULL AND t.form IN ({','.join('?' * len(forms))})
        GROUP BY 1, 2, 3
    """
    for doc, form, lid, n in kconn.execute(q, forms):
        m = meta.get(doc)
        if not m or m["teksttype"] not in BOOK_TYPES or lid not in lex:
            continue
        out[form][m["tiaar"]][lex[lid]] += n
        out[form]["alle"][lex[lid]] += n
    return out


def obt_share(counts: dict[str, dict[tuple, float]], lexeme: tuple, decade: str) -> dict[str, Any]:
    pooled = counts.get("alle", {})
    d = counts.get(decade, {})
    n_dec = sum(d.values())
    use, src = (d, "tiår") if n_dec >= MIN_OBT_N else (pooled, "samlet")
    n = sum(use.values())
    k = use.get(lexeme, 0.0)
    lo, hi = wilson(k, n)
    return {"andel": k / n if n else 0.0, "lav": lo, "hoy": hi, "n": n, "n_tiaar": n_dec, "kilde": src}


# ---------------------------------------------------------------------------
# 2. Decomposer per tiår på n-gram for bøker
# ---------------------------------------------------------------------------

def decomposer_shares(forms_ambig: list[str], ngram: dict[str, dict[int, float]], ordbank_path) -> dict:
    """{(form, tiår): {leksem: andel}} med decomposer (regler) på n-gram-tallene for tiåret."""
    from sqlite.decomposer import estimate_wordform_shares

    conn = sqlite3.connect(_ro_uri(ordbank_path), uri=True)
    conn.row_factory = sqlite3.Row
    out = {}
    try:
        conn.execute("CREATE TEMP TABLE nb_totals (oppslag TEXT PRIMARY KEY, freq REAL)")
        for dec in DECADES:
            conn.execute("DELETE FROM nb_totals")
            rows = [(w, sum(f for y, f in ys.items() if decade_of(y) == dec)) for w, ys in ngram.items()]
            conn.executemany("INSERT INTO nb_totals VALUES (?, ?)", rows)
            for form in forms_ambig:
                est = estimate_wordform_shares(form, conn=conn, corpus="nb_totals", method="regler")
                dist: dict[tuple, float] = defaultdict(float)
                for c in est["candidates"]:
                    dist[(c["grunnform"], c["pos"])] += c["share"]
                out[(form, dec)] = dict(dist)
    finally:
        conn.close()
    return out


def paradigm_forms_of_candidates(oconn, forms: list[str]) -> set[str]:
    """Alle former i paradigmene til kandidatene for de gitte formene (decomposer trenger dem)."""
    ids = {r[0] for f in forms for r in oconn.execute("SELECT DISTINCT lemma_id FROM lemma_former WHERE oppslag = ?", (f,))}
    out = set()
    for lid in ids:
        out |= {r[0] for r in oconn.execute("SELECT DISTINCT oppslag FROM lemma_former WHERE lemma_id = ?", (lid,))}
    return out


# ---------------------------------------------------------------------------
# 3. Profiler og stabilitet
# ---------------------------------------------------------------------------

def tvd(p: dict, q: dict) -> float:
    return 50 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in set(p) | set(q))


def stability(profiles: dict[str, dict[str, float]]) -> dict[str, float]:
    decs = [d for d in DECADES if d in profiles]
    steps = [tvd(profiles[a], profiles[b]) for a, b in zip(decs, decs[1:])]
    cats = {c for p in profiles.values() for c in p}
    mean = {c: sum(profiles[d].get(c, 0.0) for d in decs) / len(decs) for c in cats}
    return {"snitt_endring_pp": sum(steps) / len(steps) if steps else 0.0,
            "maks_fra_snitt_pp": max(tvd(profiles[d], mean) for d in decs)}


def run(kdb: str | Path, ordbank_path=ORDBANK_DB_PATH) -> tuple[list, list, list]:
    kconn = sqlite3.connect(_ro_uri(kdb), uri=True)
    oconn = sqlite3.connect(_ro_uri(ordbank_path), uri=True)
    lex = lexeme_map(oconn)
    meta = load_metadata()

    plan = []  # (lemma, pos, groups, ambiguous forms)
    all_forms, ambig_all = set(), set()
    for g, pos in LEMMAS:
        _, groups = _cell_groups(oconn, g, pos)
        amb = {f for gr in groups for f in gr["former"] if candidate_lexemes(oconn, f) != {(g, pos)}}
        plan.append((g, pos, groups, amb))
        all_forms |= {f for gr in groups for f in gr["former"]}
        ambig_all |= amb
    extra = paradigm_forms_of_candidates(oconn, sorted(ambig_all))
    ngram = fetch_ngram_dhlab(sorted(all_forms | extra), period=PERIOD, corpus="book", lang="nob")
    counts = obt_counts(kconn, sorted(ambig_all), lex, meta)
    dec_shares = decomposer_shares(sorted(ambig_all), ngram, ordbank_path)

    share_rows, prof_rows, summary = [], [], []
    for g, pos, groups, amb in plan:
        lexeme = (g, pos)
        for f in sorted(amb):
            for dec in DECADES:
                s = obt_share(counts.get(f, {}), lexeme, dec)
                share_rows.append({"lemma": g, "pos": pos, "form": f, "tiaar": dec, **s,
                                   "decomposer_andel": dec_shares.get((f, dec), {}).get(lexeme, 0.0)})
        pooled = {f: obt_share(counts.get(f, {}), lexeme, "alle")["andel"] for f in amb}

        def share(f, dec, variant):
            if f not in amb or variant == "naiv":
                return 1.0
            if variant == "obt_tiaar":
                return obt_share(counts.get(f, {}), lexeme, dec)["andel"]
            if variant == "obt_fast":
                return pooled[f]
            return dec_shares.get((f, dec), {}).get(lexeme, 0.0)

        profiles: dict[str, dict[str, dict[str, float]]] = {v: {} for v in VARIANTS}
        for v in VARIANTS:
            for dec in DECADES:
                years = [y for y in range(PERIOD[0], PERIOD[1] + 1) if decade_of(y) == dec]
                cells = {gr["kategori"]: sum(ngram.get(f, {}).get(y, 0.0) * share(f, dec, v)
                                             for f in gr["former"] for y in years) for gr in groups}
                tot = sum(cells.values())
                if tot <= 0:
                    continue
                profiles[v][dec] = {c: n / tot for c, n in cells.items()}
                for c, n in cells.items():
                    prof_rows.append({"lemma": g, "pos": pos, "variant": v, "tiaar": dec, "kategori": c,
                                      "n": n, "andel": n / tot})
        row = {"lemma": f"{g} ({pos})", "flertydige": ", ".join(sorted(amb))}
        for v in VARIANTS:
            st_ = stability(profiles[v])
            row[f"{v}_snitt"] = st_["snitt_endring_pp"]
            row[f"{v}_maks"] = st_["maks_fra_snitt_pp"]
        row["profiler"] = profiles
        summary.append(row)
    kconn.close()
    oconn.close()
    return share_rows, prof_rows, summary


def _write_tsv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})


def _f(v: float) -> str:
    return f"{v:.1f}".replace(".", ",")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Stabilitet over tid med OBT-fordeling av flertydige former.")
    p.add_argument("--db", default=str(DEFAULT_SHARED_DB))
    p.add_argument("--ut", default=str(RESULT_DIR))
    args = p.parse_args(argv)

    shares, profs, summary = run(args.db)
    ut = Path(args.ut)
    _write_tsv(shares, ut / "stabilitet_obt_andeler.tsv")
    _write_tsv(profs, ut / "stabilitet_obt_profiler.tsv")

    print("## Stabilitet: snitt endring mellom tiår / maks avvik fra snittprofil (pp)\n")
    print("| lemma | flertydige former | " + " | ".join(VARIANTS) + " |")
    print("|---|---|" + "---|" * len(VARIANTS))
    for r in summary:
        print(f"| {r['lemma']} | {r['flertydige']} | " +
              " | ".join(f"{_f(r[f'{v}_snitt'])} / {_f(r[f'{v}_maks'])}" for v in VARIANTS) + " |")

    print("\n## OBT-andeler per tiår for de flertydige formene (bøker; * = samlet andel brukt)\n")
    by_form = defaultdict(list)
    for s in shares:
        by_form[(s["lemma"], s["form"])].append(s)
    print("| lemma | form | " + " | ".join(d[:4] for d in DECADES) + " | decomposer 1950/2010 |")
    print("|---|---|" + "---|" * (len(DECADES) + 1))
    for (lem, form), rs in by_form.items():
        cells = [f"{100 * r['andel']:.0f}{'*' if r['kilde'] == 'samlet' else ''} ({r['n_tiaar']:.0f})" for r in rs]
        dc = f"{100 * rs[0]['decomposer_andel']:.0f} / {100 * rs[6]['decomposer_andel']:.0f}"
        print(f"| {lem} | {form} | " + " | ".join(cells) + f" | {dc} |")

    print("\n## Profiler per tiår (andel %, obt_tiaar / decomposer / naiv)\n")
    for r in summary:
        prof = r["profiler"]
        cats = list(next(iter(prof["obt_tiaar"].values())).keys())
        print(f"**{r['lemma']}**\n")
        print("| tiår | " + " | ".join(cats) + " |")
        print("|---|" + "---|" * len(cats))
        for dec in DECADES:
            if dec not in prof["obt_tiaar"]:
                continue
            print(f"| {dec[:4]} | " + " | ".join(
                f"{100 * prof['obt_tiaar'][dec][c]:.0f} / {100 * prof['decomposer'].get(dec, {}).get(c, 0):.0f}"
                f" / {100 * prof['naiv'][dec][c]:.0f}" for c in cats) + " |")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
