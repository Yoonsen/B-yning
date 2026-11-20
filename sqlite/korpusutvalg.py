#!/usr/bin/env python3
"""
Trekker et balansert bokmålskorpus fra NBs samling via dhlab og lagrer en KORPUSOVERSIKT
(metadata + URN + antall ord), ikke fulltekster. Oversikten kan legges i repoet; fulltekstene
hentes separat fra URN-ene og skal ikke i repoet.

Design (avtalt 2026-11-18):
  - 3 teksttyper: skjønnlitteratur (digibok), faglitteratur (digibok), aviser (digavis)
  - 8 tiår: 1950–1959, …, 2010–2019, 2020–2026
  - omtrent like mange ord i hver av de 24 cellene (standard 10 mill. ord totalt)
  - bøker: kun `langs == "nob"` (utelater oversettelser og bøker med blandet språk) og minst
    MIN_ORD_BOK ord (utelater hefter/barnebøker); maks én bok per forfatter per celle
  - bokmål sjekkes med markørord (ikke/ikkje, jeg/eg, …) for ALLE dokumenter: aviser har ikke
    språk i metadata, og `langs == "nob"` slipper gjennom nynorske bøker og dialektbøker
  - aviser: maks MAKS_PER_AVIS numre per avistittel per celle
  - ingen enkeltdokumenter større enn MAKS_ANDEL_AV_CELLE av cellemålet

Antall ord per dokument regnes ut fra dhlab-frekvens-API-et: freq / relfreq for et vanlig ord.

Bruk (fra repo-roten):
    python -m sqlite.korpusutvalg --ut korpus/korpusoversikt.tsv
    python -m sqlite.korpusutvalg --totalt 240000 --ut /tmp/test.tsv     # liten prøve

Utvalget trekkes tilfeldig av dhlab-API-et og kan ikke gjenskapes ved ny kjøring; den lagrede
oversikten ER den reproduserbare definisjonen av korpuset.
"""

import argparse
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd
from dhlab import Corpus
from dhlab.api.dhlab_api import get_document_frequencies

TIAAR = [(1950, 1959), (1960, 1969), (1970, 1979), (1980, 1989),
         (1990, 1999), (2000, 2009), (2010, 2019), (2020, 2026)]

TYPER = {
    "skjonnlitteratur": dict(doctype="digibok", literaryform="Skjønnlitteratur", lang="nob"),
    "faglitteratur": dict(doctype="digibok", literaryform="Faglitteratur", lang="nob"),
    "avis": dict(doctype="digavis"),
}

MIN_ORD_BOK = 20_000
MIN_ORD_AVIS = 3_000
MAKS_ANDEL_AV_CELLE = 0.35
MAKS_PER_AVIS = 3
MIN_BOKMAAL_ANDEL = 0.95
MIN_MARKORER = 5

# Markørpar (bokmål, nynorsk) for språksjekk av aviser
MARKORPAR = [("ikke", "ikkje"), ("jeg", "eg"), ("hva", "kva"), ("hvordan", "korleis"),
             ("noen", "nokon"), ("mye", "mykje"), ("hvem", "kven")]
ORD_FOR_TELLING = ["og", "i", "det", "er", "på"]
SPORREORD = sorted({w for par in MARKORPAR for w in par} | set(ORD_FOR_TELLING))

KOLONNER = ["teksttype", "tiaar", "dhlabid", "urn", "title", "authors", "year", "timestamp",
            "publisher", "city", "langs", "literaryform", "genres", "ddc", "doctype",
            "n_ord", "bokmaal_andel", "trukket_dato"]


def _tiaar_navn(fra: int, til: int) -> str:
    return f"{fra}-{til}"


def ordtelling_og_sprak(df: pd.DataFrame, chunk: int = 100) -> pd.DataFrame:
    """Legger til n_ord og bokmaal_andel for dokumentene i df (via dhlab-frekvens-API-et)."""
    n_ord, andel = {}, {}
    ids = list(df["dhlabid"])
    urns = list(df["urn"])
    for i in range(0, len(urns), chunk):
        f = get_document_frequencies(urns=urns[i:i + chunk], words=SPORREORD, cutoff=0)
        if f is None or len(f) == 0:
            continue
        freq, rel = f["freq"], f["relfreq"]
        for did in ids[i:i + chunk]:
            if did not in freq.columns:
                continue
            fr = freq[did].fillna(0)
            rf = rel[did].fillna(0)
            # totalt antall ord = freq / relfreq for ordet med høyest frekvens
            w = fr.idxmax()
            if fr[w] > 0 and rf[w] > 0:
                n_ord[did] = int(round(fr[w] / rf[w]))
            bm = sum(fr.get(b, 0) for b, _ in MARKORPAR)
            nn = sum(fr.get(n, 0) for _, n in MARKORPAR)
            andel[did] = (bm / (bm + nn)) if (bm + nn) >= MIN_MARKORER else None
    out = df.copy()
    out["n_ord"] = out["dhlabid"].map(n_ord)
    out["bokmaal_andel"] = out["dhlabid"].map(andel)
    return out


def _godkjent(row, teksttype: str, cellemaal: int) -> bool:
    n = row["n_ord"]
    if pd.isna(n) or n > MAKS_ANDEL_AV_CELLE * cellemaal:
        return False
    a = row["bokmaal_andel"]
    har_andel = a is not None and not pd.isna(a)
    if teksttype == "avis":
        return n >= MIN_ORD_AVIS and har_andel and a >= MIN_BOKMAAL_ANDEL
    # Bøker: metadata `langs == "nob"` er ikke nok (nynorske og dialektbøker forekommer),
    # så språksjekken brukes også her når det finnes nok markørord.
    langs = str(row.get("langs") or "").replace(" ", "")
    return n >= MIN_ORD_BOK and langs == "nob" and (not har_andel or a >= MIN_BOKMAAL_ANDEL)


def trekk_celle(teksttype: str, fra: int, til: int, cellemaal: int, brukt: set,
                batch: int, maks_runder: int) -> list[dict]:
    """Trekker dokumenter til én celle (teksttype × tiår) til cellemålet er nådd."""
    valgt, sum_ord = [], 0
    per_nokkel: Counter = Counter()  # forfatter (bøker) eller avistittel (aviser)
    for runde in range(maks_runder):
        if sum_ord >= cellemaal:
            break
        kand = Corpus(from_year=fra, to_year=til, limit=batch, **TYPER[teksttype]).frame
        if kand.empty:
            break
        kand = kand[~kand["dhlabid"].isin(brukt)]
        if teksttype != "avis":
            kand = kand[kand["langs"].fillna("").str.replace(" ", "") == "nob"]
        if kand.empty:
            continue
        kand = ordtelling_og_sprak(kand)
        for _, row in kand.sample(frac=1, random_state=runde).iterrows():
            if sum_ord >= cellemaal:
                break
            if row["dhlabid"] in brukt or not _godkjent(row, teksttype, cellemaal):
                continue
            forfatter = row.get("authors")
            if teksttype == "avis" or pd.isna(forfatter) or not str(forfatter).strip():
                nokkel = row["title"]
            else:
                nokkel = forfatter
            grense = MAKS_PER_AVIS if teksttype == "avis" else 1
            if per_nokkel[nokkel] >= grense:
                continue
            per_nokkel[nokkel] += 1
            brukt.add(row["dhlabid"])
            sum_ord += int(row["n_ord"])
            d = {k: row.get(k) for k in KOLONNER if k in row}
            d.update(teksttype=teksttype, tiaar=_tiaar_navn(fra, til))
            valgt.append(d)
    return valgt


def bygg_korpus(totalt: int = 10_000_000, batch: int = 60, maks_runder: int = 8) -> pd.DataFrame:
    cellemaal = totalt // (len(TYPER) * len(TIAAR))
    brukt: set = set()
    rader = []
    for teksttype in TYPER:
        for fra, til in TIAAR:
            valgt = trekk_celle(teksttype, fra, til, cellemaal, brukt, batch, maks_runder)
            s = sum(int(v["n_ord"]) for v in valgt)
            flagg = "" if s >= cellemaal else f"  (under målet på {cellemaal:,})"
            print(f"{teksttype:17s} {fra}-{til}: {len(valgt):3d} dok, {s:>9,} ord{flagg}", flush=True)
            rader.extend(valgt)
    df = pd.DataFrame(rader)
    df["trukket_dato"] = date.today().isoformat()
    df["n_ord"] = df["n_ord"].astype(int)
    df["bokmaal_andel"] = df["bokmaal_andel"].astype(float).round(3)
    return df[[k for k in KOLONNER if k in df.columns]]


def oppsummer(df: pd.DataFrame) -> pd.DataFrame:
    return df.pivot_table(index="tiaar", columns="teksttype", values="n_ord",
                          aggfunc=["count", "sum"], fill_value=0)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Trekk et balansert bokmålskorpus (kun oversikt, ikke fulltekst).")
    p.add_argument("--totalt", type=int, default=10_000_000, help="Mål for totalt antall ord (standard 10 mill.)")
    p.add_argument("--ut", required=True, help="TSV-fil for korpusoversikten")
    p.add_argument("--batch", type=int, default=60, help="Antall kandidater per trekning")
    p.add_argument("--maks-runder", type=int, default=8, help="Maks antall trekninger per celle")
    args = p.parse_args(argv)

    df = bygg_korpus(args.totalt, args.batch, args.maks_runder)
    Path(args.ut).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.ut, sep="\t", index=False)
    print(f"\nSkrev {len(df)} dokumenter, {df['n_ord'].sum():,} ord til {args.ut}")
    print(oppsummer(df).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
