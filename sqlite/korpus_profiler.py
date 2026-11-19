#!/usr/bin/env python3
"""
Paradigmeprofiler fra et OBT-tagget korpus.

Arbeidsflyt:
  1. Tell former per dokument fra OBT-utdata (eller tagg tekstfiler direkte) og lagre KUN telletall
     i en egen SQLite-database (standard `sqlite/korpus.db`, som ignoreres av Git via *.db).
     Selve teksten lagres aldri, så rettighetsbelagte bøker kan brukes uten at tekst havner i repoet.
  2. Koble hver OBT-analyse (ordform + lemma + ordklasse + trekk) til en celle i et Ordbank-paradigme
     (`lemma_id`, `boy_nummer`) ved å sammenligne med `fullformsliste.tag`, som bruker samme
     notasjon som OBT (f.eks. «subst mask appell ent ub»).
  3. Hent paradigmeprofiler (frekvens og andel per bøyningskategori), hele korpuset eller per dokument.
  4. Se den faktiske fordelingen av en flertydig form på lemmaer, og sammenlign med
     `decomposer.estimate_wordform_shares` kjørt på de *samme* korpustallene.

Bruk fra Python / notebook:
    from sqlite.korpus_profiler import open_korpus, add_obt_files, map_types, paradigm_profile
    k = open_korpus()                                  # sqlite/korpus.db
    add_obt_files(k, ["/sti/bok1.obt", "/sti/bok2.obt"])
    map_types(k)
    paradigm_profile(k, grunnform="fisk", pos="subst")

Kommandolinje (fra repo-roten), se `python -m sqlite.korpus_profiler -h`.

Status: skrevet og testet på et lite, konstruert OBT-utdrag; ikke testet på et ekte tagget korpus.
"""

import argparse
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from sqlite.obt_tagger import DEFAULT_OBT_DIR, parse_obt_output, run_obt
from sqlite.queries import DEFAULT_DB_PATH as ORDBANK_DB_PATH

DEFAULT_KORPUS_DB = Path(__file__).resolve().parent / "korpus.db"

# Tokens med disse ordklassene telles ikke (tegnsetting, setningsgrenser, symboler)
SKIP_POS = {"tegn", "clb", "symb", ""}

# OBT-markører som er del av bøyningskategorien (partisipp brukt som adjektiv)
PART_MARKERS = {"<perf-part>", "<pres-part>"}

TYPE_KEY = ("form", "lemma", "pos", "trekk", "partisipp")

SCHEMA = """
CREATE TABLE IF NOT EXISTS dokumenter (
    doc_id        TEXT PRIMARY KEY,
    kilde         TEXT,
    antall_tokens INTEGER,
    flertydige    INTEGER,
    lagt_til      TEXT
);
-- Én rad per (dokument, analysetype). n er vektet antall: et token med k gjenværende
-- analyser gir 1/k til hver (normalt k = 1 etter OBT-Stat).
CREATE TABLE IF NOT EXISTS obt_typer (
    doc_id    TEXT NOT NULL,
    form      TEXT NOT NULL,
    lemma     TEXT NOT NULL,
    pos       TEXT NOT NULL,
    trekk     TEXT NOT NULL,
    partisipp TEXT NOT NULL,
    n         REAL NOT NULL,
    PRIMARY KEY (doc_id, form, lemma, pos, trekk, partisipp)
);
CREATE INDEX IF NOT EXISTS idx_obt_typer_form ON obt_typer(form);
-- Kobling fra analysetype til paradigmecelle i Ordbanken. En type kan få flere rader
-- (vekt < 1) hvis den passer like godt på flere celler/lemmaer.
CREATE TABLE IF NOT EXISTS type_kobling (
    form       TEXT NOT NULL,
    lemma      TEXT NOT NULL,
    pos        TEXT NOT NULL,
    trekk      TEXT NOT NULL,
    partisipp  TEXT NOT NULL,
    lemma_id   INTEGER,          -- NULL hvis ingen kobling
    boy_nummer INTEGER,
    vekt       REAL NOT NULL,
    status     TEXT NOT NULL     -- 'eksakt', 'delvis', 'flertydig', 'ingen'
);
CREATE INDEX IF NOT EXISTS idx_type_kobling ON type_kobling(form, lemma, pos, trekk, partisipp);
CREATE INDEX IF NOT EXISTS idx_type_kobling_lemma ON type_kobling(lemma_id, boy_nummer);
-- Dokumenter som feilet eller fikk tidsavbrudd under tagging (se tag_and_add)
CREATE TABLE IF NOT EXISTS tagging_feil (
    doc_id    TEXT PRIMARY KEY,
    feiltype  TEXT,
    melding   TEXT,
    tidspunkt TEXT
);
CREATE VIEW IF NOT EXISTS v_celle_frekvens AS
    SELECT t.doc_id, k.lemma_id, k.boy_nummer, SUM(t.n * k.vekt) AS n
    FROM obt_typer t
    JOIN type_kobling k USING (form, lemma, pos, trekk, partisipp)
    WHERE k.lemma_id IS NOT NULL
    GROUP BY t.doc_id, k.lemma_id, k.boy_nummer;
"""


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def open_korpus(
    path: str | Path = DEFAULT_KORPUS_DB,
    ordbank_path: str | Path = ORDBANK_DB_PATH,
) -> sqlite3.Connection:
    """Åpner (og oppretter ved behov) korpusdatabasen, med Ordbanken koblet til som `ob`."""
    # URI-modus slik at Ordbanken kan kobles til skrivebeskyttet (mode=ro)
    conn = sqlite3.connect(Path(path).resolve().as_uri(), uri=True)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.execute("ATTACH DATABASE ? AS ob", (_ro_uri(ordbank_path),))
    return conn


def _ro_uri(path: str | Path) -> str:
    return Path(path).resolve().as_uri() + "?mode=ro"


# ---------------------------------------------------------------------------
# 1. Telling
# ---------------------------------------------------------------------------

def _type_key(form: str, a: dict[str, Any]) -> tuple[str, str, str, str, str]:
    part = " ".join(sorted(m for m in a["ekstra"] if m in PART_MARKERS))
    return (form, a["lemma"], a["pos"], " ".join(a["trekk"]), part)


def count_tokens(tokens: list[dict[str, Any]], skip_pos: set[str] = SKIP_POS) -> Counter:
    """Teller analysetyper i en liste OBT-tokens (fra `parse_obt_output`). Flertydige tokens deles likt."""
    c: Counter = Counter()
    for tok in tokens:
        analyser = [a for a in tok["analyser"] if a["pos"] not in skip_pos]
        if not analyser:
            continue
        w = 1.0 / len(analyser)
        for a in analyser:
            c[_type_key(tok["form"], a)] += w
    return c


def add_document(
    conn: sqlite3.Connection,
    doc_id: str,
    tokens: list[dict[str, Any]],
    kilde: str | None = None,
) -> int:
    """Lagrer telletallene for ett dokument (erstatter tidligere tall for samme doc_id)."""
    counts = count_tokens(tokens)
    n_tok = sum(1 for t in tokens if any(a["pos"] not in SKIP_POS for a in t["analyser"]))
    n_amb = sum(1 for t in tokens if len(t["analyser"]) > 1)
    with conn:
        conn.execute("DELETE FROM obt_typer WHERE doc_id = ?", (doc_id,))
        conn.executemany(
            "INSERT INTO obt_typer (doc_id, form, lemma, pos, trekk, partisipp, n) VALUES (?,?,?,?,?,?,?)",
            [(doc_id, *k, n) for k, n in counts.items()],
        )
        conn.execute(
            "INSERT OR REPLACE INTO dokumenter VALUES (?,?,?,?,?)",
            (doc_id, kilde, n_tok, n_amb, datetime.now().isoformat(timespec="seconds")),
        )
    return n_tok


def add_obt_files(
    conn: sqlite3.Connection,
    paths: Iterable[str | Path],
    doc_id_from_path=lambda p: Path(p).stem,
) -> None:
    """Leser filer med rå OBT-utdata (fra tag-bm.sh) og lagrer telletall. doc_id = filnavn uten endelse."""
    for p in paths:
        tokens = parse_obt_output(Path(p).read_text(encoding="utf-8"))
        n = add_document(conn, doc_id_from_path(p), tokens, kilde=str(p))
        print(f"{doc_id_from_path(p)}: {n} tokens")


def tag_and_add(
    conn: sqlite3.Connection,
    text_paths: Iterable[str | Path],
    obt_dir: str | Path = DEFAULT_OBT_DIR,
    stat: bool = True,
    doc_id_from_path=lambda p: Path(p).stem,
    skip_existing: bool = True,
    timeout: float | None = 900,
    retry_failed: bool = False,
) -> None:
    """Tagger tekstfiler med OBT og lagrer KUN telletall (OBT-utdataene skrives ikke til disk).
    Dokumenter som allerede finnes i databasen hoppes over (med mindre skip_existing=False), så en
    avbrutt kjøring kan startes på nytt med samme kommando.
    Et dokument som feiler eller bruker mer enn `timeout` sekunder, noteres i tabellen
    `tagging_feil` og hoppes over, så resten av korpuset blir tagget. Feilede dokumenter prøves
    ikke igjen ved neste kjøring med mindre retry_failed=True."""
    import time

    text_paths = list(text_paths)
    done = {r[0] for r in conn.execute("SELECT doc_id FROM dokumenter")} if skip_existing else set()
    failed = set() if retry_failed else {r[0] for r in conn.execute("SELECT doc_id FROM tagging_feil")}
    todo = [p for p in text_paths if doc_id_from_path(p) not in done | failed]
    n_done = sum(1 for p in text_paths if doc_id_from_path(p) in done)
    n_failed = sum(1 for p in text_paths if doc_id_from_path(p) in failed - done)
    if n_done:
        print(f"Hopper over {n_done} dokumenter som allerede er tagget.", flush=True)
    if n_failed:
        print(f"Hopper over {n_failed} dokumenter som feilet tidligere (bruk --prøv-feilede for å prøve igjen).", flush=True)
    t0 = time.time()
    n_ok = n_err = 0
    for i, p in enumerate(todo, start=1):
        t = time.time()
        doc_id = doc_id_from_path(p)
        try:
            tokens = parse_obt_output(run_obt(p, obt_dir=obt_dir, stat=stat, timeout=timeout))
        except Exception as e:  # tidsavbrudd (ObtTimeout) eller annen OBT-feil
            n_err += 1
            msg = str(e).splitlines()[0][:500] if str(e) else type(e).__name__
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO tagging_feil VALUES (?,?,?,?)",
                    (doc_id, type(e).__name__, msg, datetime.now().isoformat(timespec="seconds")),
                )
            print(f"[{i}/{len(todo)}] {doc_id}: FEIL ({type(e).__name__}) etter {time.time() - t:.0f} s: {msg}", flush=True)
            continue
        n = add_document(conn, doc_id, tokens, kilde=str(p))
        with conn:
            conn.execute("DELETE FROM tagging_feil WHERE doc_id = ?", (doc_id,))
        n_ok += 1
        print(f"[{i}/{len(todo)}] {doc_id}: {n} tokens, {time.time() - t:.0f} s "
              f"(totalt {(time.time() - t0) / 60:.1f} min)", flush=True)
    print(f"Ferdig: {n_ok} tagget, {n_err} feilet i denne kjøringen.", flush=True)


# ---------------------------------------------------------------------------
# 2. Kobling til Ordbanken
# ---------------------------------------------------------------------------

def _core_tags(tag_string: str) -> frozenset[str]:
    """Kjernetrekk fra en Ordbank-tag eller OBT-analyse: alt unntatt <…>-markører, normering og
    OBTs setningsgrensemarkør `clb` (som OBT f.eks. setter på *og*, *men*), men med
    <perf-part>/<pres-part> beholdt (de skiller partisipp-cellene)."""
    out = set()
    for t in tag_string.split():
        if t in ("normert", "unormert", "clb"):
            continue
        if t.startswith("<") and t not in PART_MARKERS:
            continue
        out.add(t)
    return frozenset(out)


def _match_type(conn: sqlite3.Connection, form: str, lemma: str, pos: str, trekk: str, part: str):
    """Finner paradigmeceller som passer én OBT-analysetype. Returnerer [(lemma_id, boy_nummer, vekt, status)]."""
    obt = _core_tags(f"{pos} {trekk} {part}")
    rows = conn.execute(
        """
        SELECT f.lemma_id, f.boy_nummer, f.tag
        FROM ob.fullformsliste f
        JOIN ob.lemma l ON l.lemma_id = f.lemma_id
        WHERE f.oppslag = ? AND f.normering = 'normert' AND l.grunnform = ?
        """,
        (form, lemma),
    ).fetchall()
    if not rows:
        return [(None, None, 1.0, "ingen")]

    exact = {(r["lemma_id"], r["boy_nummer"]) for r in rows if _core_tags(r["tag"]) == obt}
    if exact:
        cells, status = exact, "eksakt"
    else:
        # Ingen eksakt match: velg cellene med størst overlapp i trekk (samme ordklasse kreves)
        scored = []
        for r in rows:
            tags = _core_tags(r["tag"])
            if pos not in tags:
                continue
            overlap = len(tags & obt) / len(tags | obt)
            scored.append((overlap, (r["lemma_id"], r["boy_nummer"])))
        if not scored:
            return [(None, None, 1.0, "ingen")]
        best = max(s for s, _ in scored)
        cells, status = {c for s, c in scored if s == best}, "delvis"

    if len(cells) > 1:
        status = "flertydig" if status == "eksakt" else status
    w = 1.0 / len(cells)
    return [(lid, bnr, w, status) for lid, bnr in sorted(cells)]


def map_types(conn: sqlite3.Connection, remap: bool = False) -> dict[str, float]:
    """Kobler alle analysetyper som ikke er koblet ennå (alle med remap=True). Returnerer `mapping_report`."""
    with conn:
        if remap:
            conn.execute("DELETE FROM type_kobling")
        todo = conn.execute(
            """
            SELECT DISTINCT t.form, t.lemma, t.pos, t.trekk, t.partisipp
            FROM obt_typer t
            LEFT JOIN type_kobling k USING (form, lemma, pos, trekk, partisipp)
            WHERE k.form IS NULL
            """
        ).fetchall()
        for r in todo:
            key = tuple(r[c] for c in TYPE_KEY)
            for lid, bnr, w, status in _match_type(conn, *key):
                conn.execute(
                    "INSERT INTO type_kobling VALUES (?,?,?,?,?,?,?,?,?)",
                    (*key, lid, bnr, w, status),
                )
    return mapping_report(conn)


def mapping_report(conn: sqlite3.Connection) -> dict[str, float]:
    """Andel av (vektede) tokens per koblingsstatus. 'ingen' er typisk egennavn, sammensetninger som
    ikke står i Ordbanken, ukjente ord og funksjonsord med avvikende lemma."""
    rows = conn.execute(
        """
        SELECT k.status, SUM(t.n * k.vekt) AS n
        FROM obt_typer t JOIN type_kobling k USING (form, lemma, pos, trekk, partisipp)
        GROUP BY k.status
        """
    ).fetchall()
    total = sum(r["n"] for r in rows) or 1.0
    return {r["status"]: round(r["n"] / total, 4) for r in rows}


def mapping_report_by_pos(
    conn: sqlite3.Connection, pos_list: Iterable[str] = ("subst", "verb", "adj")
) -> dict[str, dict[str, float]]:
    """Som `mapping_report`, men per ordklasse (OBT-ordklasse). Egennavn (subst prop) holdes
    utenfor substantivene, siden de normalt ikke står i Ordbanken."""
    out = {}
    for pos in pos_list:
        extra = " AND t.trekk NOT LIKE '%prop%'" if pos == "subst" else ""
        rows = conn.execute(
            f"""
            SELECT k.status, SUM(t.n * k.vekt) AS n
            FROM obt_typer t JOIN type_kobling k USING (form, lemma, pos, trekk, partisipp)
            WHERE t.pos = ?{extra}
            GROUP BY k.status
            """,
            (pos,),
        ).fetchall()
        total = sum(r["n"] for r in rows)
        out[pos] = {r["status"]: round(r["n"] / total, 4) for r in rows} if total else {}
        out[pos]["tokens"] = round(total)
    return out


def unmatched(
    conn: sqlite3.Connection,
    limit: int = 30,
    statuses: Iterable[str] = ("ingen", "delvis"),
    pos: str | None = None,
) -> list[dict[str, Any]]:
    """De hyppigste analysetypene med gitt koblingsstatus (standard: ikke eller bare delvis koblet),
    ev. avgrenset til én ordklasse. `celler` viser hvilke (lemma_id:boy_nummer) typen er koblet til –
    nyttig for å se hva 'flertydig' deler forekomstene mellom."""
    statuses = list(statuses)
    q = f"""
        SELECT t.form, t.lemma, t.pos, t.trekk, t.partisipp, k.status,
               SUM(t.n * k.vekt) AS n,
               GROUP_CONCAT(DISTINCT k.lemma_id || ':' || k.boy_nummer) AS celler
        FROM obt_typer t JOIN type_kobling k USING (form, lemma, pos, trekk, partisipp)
        WHERE k.status IN ({",".join("?" for _ in statuses)})
    """
    params: list[Any] = statuses
    if pos:
        q += " AND t.pos = ?"
        params = params + [pos]
    q += " GROUP BY t.form, t.lemma, t.pos, t.trekk, t.partisipp, k.status ORDER BY n DESC LIMIT ?"
    rows = conn.execute(q, params + [limit]).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# 3. Paradigmeprofiler
# ---------------------------------------------------------------------------

def find_lemma_ids(conn: sqlite3.Connection, grunnform: str, pos: str | None = None) -> list[int]:
    q = "SELECT DISTINCT lemma_id FROM ob.lemma_former WHERE grunnform = ?"
    params: list[Any] = [grunnform]
    if pos:
        q += " AND pos = ?"
        params.append(pos)
    return [r[0] for r in conn.execute(q, params)]


def paradigm_profile(
    conn: sqlite3.Connection,
    lemma_id: int | None = None,
    grunnform: str | None = None,
    pos: str | None = None,
    per_doc: bool = False,
    slots: Iterable[int] | None = None,
) -> list[dict[str, Any]]:
    """
    Frekvens og andel per bøyningskategori for ett lemma, med alle paradigmets celler (også de med 0).
    Gis `grunnform` uten `lemma_id` og det finnes flere homografe lemmaer, velges det med flest
    forekomster i korpuset (alle kandidater listes i feltet `kandidater`).
    `slots` begrenser til bestemte boy_nummer (f.eks. (1, 2, 4) for inf/pres/pret); andelene regnes
    da innenfor disse. `per_doc=True` gir én rad per (dokument, celle).
    """
    if lemma_id is None:
        if not grunnform:
            raise ValueError("Oppgi lemma_id eller grunnform")
        cands = find_lemma_ids(conn, grunnform, pos)
        if not cands:
            raise ValueError(f"Fant ikke {grunnform!r} ({pos}) i Ordbanken")
        totals = {
            lid: conn.execute(
                "SELECT COALESCE(SUM(n), 0) FROM v_celle_frekvens WHERE lemma_id = ?", (lid,)
            ).fetchone()[0]
            for lid in cands
        }
        lemma_id = max(cands, key=lambda lid: totals[lid])
    else:
        cands, totals = [lemma_id], {}

    cells = conn.execute(
        """
        SELECT boy_nummer, MIN(boy_tekst) AS boy_tekst, GROUP_CONCAT(DISTINCT oppslag) AS former,
               MIN(grunnform) AS grunnform, MIN(pos) AS pos
        FROM ob.lemma_former WHERE lemma_id = ?
        GROUP BY boy_nummer ORDER BY boy_nummer
        """,
        (lemma_id,),
    ).fetchall()
    if slots is not None:
        slots = set(slots)
        cells = [c for c in cells if c["boy_nummer"] in slots]

    if per_doc:
        docs = [r[0] for r in conn.execute("SELECT doc_id FROM dokumenter ORDER BY doc_id")]
    else:
        docs = [None]

    out = []
    for doc in docs:
        q = "SELECT boy_nummer, SUM(n) FROM v_celle_frekvens WHERE lemma_id = ?"
        params: list[Any] = [lemma_id]
        if doc is not None:
            q += " AND doc_id = ?"
            params.append(doc)
        freq = dict(conn.execute(q + " GROUP BY boy_nummer", params).fetchall())
        total = sum(freq.get(c["boy_nummer"], 0.0) for c in cells)
        for c in cells:
            n = freq.get(c["boy_nummer"], 0.0)
            row = {
                "lemma_id": lemma_id,
                "grunnform": c["grunnform"],
                "pos": c["pos"],
                "boy_nummer": c["boy_nummer"],
                "boy_tekst": c["boy_tekst"],
                "former": c["former"],
                "n": n,
                "andel": n / total if total else 0.0,
            }
            if doc is not None:
                row["doc_id"] = doc
            if len(cands) > 1:
                row["kandidater"] = {lid: totals.get(lid) for lid in cands}
            out.append(row)
    return out


# ---------------------------------------------------------------------------
# 4. Flertydige former: faktisk fordeling og sammenligning med decomposer
# ---------------------------------------------------------------------------

def form_split(conn: sqlite3.Connection, form: str, doc_id: str | None = None) -> list[dict[str, Any]]:
    """Faktisk (OBT-basert) fordeling av en ordform på lemma og bøyningskategori, inkl. ukoblede analyser."""
    q = """
        SELECT k.lemma_id, k.boy_nummer, t.lemma, t.pos, t.trekk, k.status, SUM(t.n * k.vekt) AS n
        FROM obt_typer t JOIN type_kobling k USING (form, lemma, pos, trekk, partisipp)
        WHERE t.form = ?
    """
    params: list[Any] = [form]
    if doc_id is not None:
        q += " AND t.doc_id = ?"
        params.append(doc_id)
    rows = [dict(r) for r in conn.execute(q + " GROUP BY 1,2,3,4,5,6 ORDER BY n DESC", params)]
    total = sum(r["n"] for r in rows) or 1.0
    for r in rows:
        r["andel"] = r["n"] / total
    return rows


def compare_with_decomposer(
    conn: sqlite3.Connection,
    form: str,
    ordbank_path: str | Path = ORDBANK_DB_PATH,
) -> list[dict[str, Any]]:
    """
    Sammenligner OBT-fordelingen av `form` per lemma_id med `decomposer.estimate_wordform_shares`
    kjørt på de SAMME korpustallene: en midlertidig view `nb_totals` (formfrekvenser i korpuset)
    skygger for Ordbankens `nb_totals` i en egen tilkobling, så decomposer.py brukes uendret.
    Merk: korpustallene teller alle forekomster av formen (alle ordklasser), som nb_totals.
    """
    from sqlite.decomposer import estimate_wordform_shares

    dbs = conn.execute("PRAGMA database_list").fetchall()
    korpus_file = next(r["file"] for r in dbs if r["name"] == "main")

    dconn = sqlite3.connect(_ro_uri(ordbank_path), uri=True)
    dconn.row_factory = sqlite3.Row
    try:
        dconn.execute("ATTACH DATABASE ? AS k", (_ro_uri(korpus_file),))
        dconn.execute(
            "CREATE TEMP VIEW nb_totals AS SELECT form AS oppslag, SUM(n) AS freq FROM k.obt_typer GROUP BY form"
        )
        est = estimate_wordform_shares(form, conn=dconn)
    finally:
        dconn.close()

    actual: dict[int | None, float] = {}
    for r in form_split(conn, form):
        actual[r["lemma_id"]] = actual.get(r["lemma_id"], 0.0) + r["n"]
    total = sum(actual.values()) or 1.0

    out = []
    seen = set()
    for c in est["candidates"]:
        lid = c["lemma_id"]
        seen.add(lid)
        out.append({
            "lemma_id": lid,
            "grunnform": c["grunnform"],
            "pos": c["pos"],
            "boy_tekst": c["boy_tekst"],
            "decomposer_andel": c["share"],
            "obt_andel": actual.get(lid, 0.0) / total,
            "obt_n": actual.get(lid, 0.0),
        })
    for lid, n in actual.items():
        if lid not in seen:
            out.append({
                "lemma_id": lid, "grunnform": None, "pos": None, "boy_tekst": None,
                "decomposer_andel": None, "obt_andel": n / total, "obt_n": n,
            })
    return out


# ---------------------------------------------------------------------------
# Kommandolinje
# ---------------------------------------------------------------------------

def _print_rows(rows: list[dict[str, Any]], cols: list[str]) -> None:
    print("\t".join(cols))
    for r in rows:
        vals = []
        for c in cols:
            v = r.get(c)
            vals.append(f"{v:.3f}" if isinstance(v, float) else ("" if v is None else str(v)))
        print("\t".join(vals))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Paradigmeprofiler fra et OBT-tagget korpus.")
    p.add_argument("--db", default=str(DEFAULT_KORPUS_DB), help="Korpusdatabase (standard: sqlite/korpus.db)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("legg-til", help="Les filer med rå OBT-utdata og lagre telletall")
    s.add_argument("filer", nargs="+")
    s = sub.add_parser("tagg", help="Tagg tekstfiler med OBT og lagre kun telletall")
    s.add_argument("filer", nargs="+")
    s.add_argument("--obt-dir", default=str(DEFAULT_OBT_DIR))
    s.add_argument("--tidsgrense", type=float, default=900,
                   help="Maks sekunder per dokument før det avbrytes og noteres som feilet (standard 900)")
    s.add_argument("--prøv-feilede", dest="prov_feilede", action="store_true",
                   help="Prøv på nytt dokumenter som feilet i en tidligere kjøring")
    sub.add_parser("feilet", help="Vis dokumenter som feilet eller fikk tidsavbrudd under tagging")
    s = sub.add_parser("koble", help="Koble analysetyper til Ordbank-paradigmer og vis koblingsrapport")
    s.add_argument("--på-nytt", dest="paa_nytt", action="store_true",
                   help="Slett eksisterende koblinger og koble alt på nytt (etter endringer i koblingsreglene)")
    s = sub.add_parser("profil", help="Paradigmeprofil for et lemma")
    s.add_argument("grunnform")
    s.add_argument("--pos", help="subst, verb, adj …")
    s.add_argument("--lemma-id", type=int)
    s.add_argument("--per-dok", action="store_true")
    s = sub.add_parser("form", help="Faktisk fordeling av en ordform på lemma/kategori")
    s.add_argument("form")
    s = sub.add_parser("sammenlign", help="OBT-fordeling vs. decomposer.py for en ordform")
    s.add_argument("form")
    s = sub.add_parser("ukoblet", help="Hyppigste analyser som ikke ble koblet (eller med annen status)")
    s.add_argument("--status", nargs="+", default=["ingen", "delvis"],
                   help="Koblingsstatus å vise: ingen, delvis, flertydig, eksakt (standard: ingen delvis)")
    s.add_argument("--pos", help="Avgrens til én ordklasse, f.eks. verb")
    s.add_argument("--antall", type=int, default=30)
    args = p.parse_args(argv)

    conn = open_korpus(args.db)
    if args.cmd == "legg-til":
        add_obt_files(conn, args.filer)
    elif args.cmd == "tagg":
        tag_and_add(conn, args.filer, obt_dir=args.obt_dir, timeout=args.tidsgrense,
                    retry_failed=args.prov_feilede)
    elif args.cmd == "feilet":
        _print_rows([dict(r) for r in conn.execute("SELECT * FROM tagging_feil ORDER BY tidspunkt")],
                    ["doc_id", "feiltype", "melding", "tidspunkt"])
    elif args.cmd == "koble":
        print("Alle ordklasser:", map_types(conn, remap=args.paa_nytt))
        for pos, rep in mapping_report_by_pos(conn).items():
            print(f"  {pos:6s}", rep)
    elif args.cmd == "profil":
        rows = paradigm_profile(conn, lemma_id=args.lemma_id, grunnform=args.grunnform,
                                pos=args.pos, per_doc=args.per_dok)
        cols = (["doc_id"] if args.per_dok else []) + ["lemma_id", "boy_nummer", "boy_tekst", "former", "n", "andel"]
        _print_rows(rows, cols)
    elif args.cmd == "form":
        _print_rows(form_split(conn, args.form), ["lemma_id", "boy_nummer", "lemma", "pos", "trekk", "status", "n", "andel"])
    elif args.cmd == "sammenlign":
        _print_rows(compare_with_decomposer(conn, args.form),
                    ["lemma_id", "grunnform", "pos", "boy_tekst", "decomposer_andel", "obt_andel", "obt_n"])
    elif args.cmd == "ukoblet":
        _print_rows(unmatched(conn, limit=args.antall, statuses=args.status, pos=args.pos),
                    ["form", "lemma", "pos", "trekk", "partisipp", "status", "n", "celler"])
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
