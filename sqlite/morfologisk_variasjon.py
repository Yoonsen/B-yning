#!/usr/bin/env python3
"""
Hvor mye morfologisk variasjon er det i korpuset? Sammenligner antall ord (tokens), antall ulike
ordformer og antall ulike lemmaer når bøyningsformene slås sammen til lemma (OBT-lemma + ordklasse).

Mål:
  - tokens:             antall løpende ord
  - formtyper:          antall ulike ordformer (små bokstaver, slik OBT slo dem opp)
  - lemmatyper:         antall ulike (lemma, ordklasse)
  - former_per_lemma:   formtyper / lemmatyper. 1,0 = ingen bøyningsvariasjon i ordforrådet
  - andel_boyd:         andel tokens der formen er en annen enn lemmaet (bøyd form eller variant),
                        dvs. hvor ofte en leser møter noe annet enn oppslagsformen i løpende tekst

Antall typer vokser med tekstmengden, så grupper (tiår, teksttype) sammenlignes ved samme antall
tokens med forventet antall typer i et tilfeldig utvalg (rarefaction, hypergeometrisk; eksakt,
ingen tilfeldighet).

"Ord" = tokens med minst én bokstav (tall og symboler tas ikke med; tegnsetting er allerede utelatt
i korpusdatabasen). Egennavn (subst prop) og ord OBT ikke kjenner (ukjent: OCR-feil, eldre
rettskrivning, fremmedord) er med i "alle ord" og vises også separat.

Bruk (fra repo-roten):
    python -m sqlite.morfologisk_variasjon                       # korpus/obt_frekvenser.db
    python -m sqlite.morfologisk_variasjon --db sqlite/korpus.db --utvalg 200000
"""

import argparse
import math
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from sqlite.korpus_profiler import DEFAULT_SHARED_DB, load_metadata

# Ordklassegrupper for tabellen per ordklasse. "subst appell" og "subst prop" skilles via trekk.
POS_GROUPS = ["subst appell", "verb", "adj", "subst prop", "det", "pron", "adv", "prep",
              "konj/sbu", "ukjent", "annet"]
INFLECTING = ("subst appell", "verb", "adj")


def _pos_group(pos: str, trekk: str) -> str:
    if pos == "subst":
        return "subst prop" if "prop" in trekk.split() else "subst appell"
    if pos in ("konj", "sbu"):
        return "konj/sbu"
    if pos in ("verb", "adj", "det", "pron", "adv", "prep", "ukjent"):
        return pos
    return "annet"


_EDGE_RE = re.compile(r"^[\W_]+|[\W_]+$")


def clean_form(s: str) -> str:
    """Fjerner tegn som ikke er bokstaver/tall i starten og slutten (f.eks. «er.», «er|», «_vært»,
    «var-», «kl.»). Ca. 2 % av tokens har slike rester fra tokenisering/OCR (logg del 39)."""
    return _EDGE_RE.sub("", s)


def load_counts(conn: sqlite3.Connection) -> list[tuple[str, str, str, str, float]]:
    """(doc_id, renset form, lemma_nøkkel, ordklassegruppe, n) for tokens med minst én bokstav."""
    rows = []
    for doc, form, lemma, pos, trekk, n in conn.execute(
        "SELECT doc_id, form, lemma, pos, trekk, SUM(n) FROM obt_typer GROUP BY 1, 2, 3, 4, 5"
    ):
        if not any(ch.isalpha() for ch in form):
            continue
        rows.append((doc, clean_form(form.lower()), f"{clean_form(lemma.lower())}|{pos}",
                     _pos_group(pos, trekk), n))
    return rows


def _expected_types(counts: Iterable[float], m: int) -> float:
    """Forventet antall typer i et tilfeldig utvalg på m tokens uten tilbakelegging."""
    counts = [int(round(c)) for c in counts if c > 0]
    total = sum(counts)
    if m >= total:
        return float(len(counts))
    lg = math.lgamma
    base = lg(total + 1) - lg(m + 1) - lg(total - m + 1)  # log C(N, m)
    e = 0.0
    for c in counts:
        if total - c < m:
            e += 1.0
        else:
            log_p0 = lg(total - c + 1) - lg(m + 1) - lg(total - c - m + 1) - base
            e += 1.0 - math.exp(log_p0)
    return e


def measures(rows: list[tuple], sample: int | None = None) -> dict[str, float]:
    """Mål for et sett rader (se modulens docstring). `sample`: også typer ved `sample` tokens."""
    forms: Counter = Counter()
    lemmas: Counter = Counter()
    tokens = inflected = 0.0
    for _, form, lemma_key, _, n in rows:
        forms[form] += n
        lemmas[lemma_key] += n
        tokens += n
        if form != lemma_key.split("|", 1)[0]:
            inflected += n
    out = {
        "tokens": tokens,
        "formtyper": len(forms),
        "lemmatyper": len(lemmas),
        "former_per_lemma": len(forms) / len(lemmas) if lemmas else 0.0,
        "andel_boyd": inflected / tokens if tokens else 0.0,
    }
    if sample:
        f_m = _expected_types(forms.values(), sample)
        l_m = _expected_types(lemmas.values(), sample)
        out.update({
            "utvalg": sample,
            "formtyper_utvalg": f_m,
            "lemmatyper_utvalg": l_m,
            "former_per_lemma_utvalg": f_m / l_m if l_m else 0.0,
        })
    return out


def by_pos(rows: list[tuple]) -> dict[str, dict[str, float]]:
    groups: dict[str, list] = defaultdict(list)
    for r in rows:
        groups[r[3]].append(r)
    return {g: measures(groups[g]) for g in POS_GROUPS if g in groups}


def by_group(rows: list[tuple], meta: dict[str, dict[str, str]], keys: tuple[str, ...],
             sample: int, pos_filter: Iterable[str] | None = None) -> dict[tuple, dict[str, float]]:
    """Mål per gruppe av dokumenter (kolonner i korpusoversikten), med typer ved `sample` tokens."""
    pos_filter = set(pos_filter) if pos_filter else None
    groups: dict[tuple, list] = defaultdict(list)
    for r in rows:
        if pos_filter and r[3] not in pos_filter:
            continue
        m = meta.get(r[0])
        groups[tuple(m.get(k, "ukjent") if m else "ukjent" for k in keys)].append(r)
    return {g: measures(groups[g], sample) for g in sorted(groups)}


FREQ_BANDS = [(1, 1), (2, 9), (10, 99), (100, 999), (1000, None)]


def by_frequency_band(rows: list[tuple], pos_group: str) -> dict[str, dict[str, float]]:
    """
    Former per lemma etter hvor hyppig lemmaet er i korpuset (for én ordklassegruppe).
    Skiller bøyningsvariasjon fra ordforrådsrikdom: et lemma som bare forekommer én gang, kan bare
    ha én form, så mange sjeldne lemmaer trekker forholdet former/lemma ned.
    """
    lemma_n: Counter = Counter()
    lemma_forms: dict[str, set] = defaultdict(set)
    for _, form, lemma_key, g, n in rows:
        if g != pos_group:
            continue
        lemma_n[lemma_key] += n
        lemma_forms[lemma_key].add(form)
    out = {}
    for lo, hi in FREQ_BANDS:
        sel = [l for l, n in lemma_n.items() if round(n) >= lo and (hi is None or round(n) <= hi)]
        if not sel:
            continue
        label = f"{lo}" if lo == hi else (f"{lo}–{hi}" if hi else f"{lo}+")
        out[label] = {
            "lemmaer": len(sel),
            "tokens": sum(lemma_n[l] for l in sel),
            "former_per_lemma": sum(len(lemma_forms[l]) for l in sel) / len(sel),
        }
    return out


def _fmt(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:.3f}" if v < 10 else f"{v:,.0f}".replace(",", " ")
    if isinstance(v, int):
        return f"{v:,}".replace(",", " ")
    return str(v)


def _print_table(title: str, table: dict, cols: list[str], keyname: str) -> None:
    print(f"\n## {title}\n")
    print("| " + " | ".join([keyname] + cols) + " |")
    print("|" + "---|" * (len(cols) + 1))
    for k, v in table.items():
        key = " / ".join(k) if isinstance(k, tuple) else k
        print("| " + " | ".join([key] + [_fmt(v[c]) for c in cols]) + " |")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ordformer vs. lemmaer: morfologisk variasjon i korpuset.")
    p.add_argument("--db", default=str(DEFAULT_SHARED_DB), help="Korpusdatabase (standard: korpus/obt_frekvenser.db)")
    p.add_argument("--utvalg", type=int, default=200_000,
                   help="Antall tokens gruppene sammenlignes ved (standard 200 000)")
    args = p.parse_args(argv)

    conn = sqlite3.connect(Path(args.db).resolve().as_uri() + "?mode=ro", uri=True)
    rows = load_counts(conn)
    meta = load_metadata()
    base_cols = ["tokens", "formtyper", "lemmatyper", "former_per_lemma", "andel_boyd"]
    s_cols = ["tokens", "formtyper_utvalg", "lemmatyper_utvalg", "former_per_lemma_utvalg", "andel_boyd"]

    _print_table("Hele korpuset", {"alle ord": measures(rows),
                                   "bøyningsklasser (subst appell, verb, adj)":
                                       measures([r for r in rows if r[3] in INFLECTING])},
                 base_cols, "utvalg")
    _print_table("Per ordklasse", by_pos(rows), base_cols, "ordklasse")
    for g in INFLECTING:
        _print_table(f"Former per lemma etter lemmafrekvens: {g}", by_frequency_band(rows, g),
                     ["lemmaer", "tokens", "former_per_lemma"], "forekomster av lemmaet")
    for keys in (("teksttype",), ("tiaar",), ("tiaar", "teksttype")):
        sample = args.utvalg if keys != ("tiaar", "teksttype") else args.utvalg // 3
        _print_table(f"Alle ord per {' × '.join(keys)} (typer ved {sample:,} tokens)",
                     by_group(rows, meta, keys, sample), s_cols, " / ".join(keys))
    _print_table(f"Bøyningsklasser per teksttype (typer ved {args.utvalg // 2:,} tokens)",
                 by_group(rows, meta, ("teksttype",), args.utvalg // 2, INFLECTING), s_cols, "teksttype")
    _print_table(f"Bøyningsklasser per tiår (typer ved {args.utvalg // 2:,} tokens)",
                 by_group(rows, meta, ("tiaar",), args.utvalg // 2, INFLECTING), s_cols, "tiaar")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
