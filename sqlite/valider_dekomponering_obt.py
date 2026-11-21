#!/usr/bin/env python3
"""
Validering av decomposer mot det OBT-taggede korpuset (ekte flertydige former).

Utfyller `sqlite/valider_dekomponering.py` (kunstige homografer i gullstandarden, nb_totals): her er
fasiten OBTs kontekstbaserte analyser i `korpus/obt_frekvenser.db`, og decomposer kjøres på de
samme korpustallene (`korpus_profiler.DecomposerSession`), med både `regler` og `logreg`.

Sammenligningsenheten er leksemet = (grunnform, ordklasse): homografe lemma_id i Ordbanken slås
sammen på begge sider (logg del 35). OBT-analyser som ikke er koblet til Ordbanken (OCR-feil,
ukjente ord), holdes utenfor fordelingen og rapporteres som `andel_ukoblet`.

1. Bred del (`compare_forms`): alle ordformer med minst MIN_N forekomster i korpuset der Ordbanken
   har minst to ulike leksemer blant substantiv, verb og adjektiv. Per form:
     - avvik_pp:     total variasjonsavstand mellom fordelingene i prosentpoeng
                     (= hvor mange prosentpoeng som er fordelt på feil leksem; for to kandidater lik
                     feilen i andelen til den ene)
     - umodellert:   andel (OBT) som går til leksemer decomposer gir 0 % (f.eks. adjektiv, andre
                     ordklasser, «i går»); slike feil kan ikke rettes med bedre forholdstall
     - riktig_flest: om decomposer gir størst andel til samme leksem som OBT
2. Dyp del (`profile_comparison`): bøyningsprofiler (kjernekategorier) for utvalgte lemmaer, tre
   varianter: OBT (fasit), decomposer (formfrekvens × decomposerandel) og naiv (formfrekvens uten
   fordeling, slik rå n-gram gir). Kategorier som deler form innen samme leksem (f.eks. inf/imp,
   pret/perf-part i svake verb), slås sammen, fordi decomposer bare fordeler mellom leksemer.

Kjøres fra repo-roten (tar noen minutter):
    python -m sqlite.valider_dekomponering_obt
    python -m sqlite.valider_dekomponering_obt --db sqlite/korpus.db --min-n 100
Skriver resultater/dekomponering_obt_former.tsv og resultater/dekomponering_obt_profiler.tsv.
"""

import argparse
import csv
import sqlite3
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlite.korpus_profiler import (DEFAULT_SHARED_DB, ORDBANK_DB_PATH, DecomposerSession,
                                    _ro_uri, form_split)

METHODS = ("regler", "logreg")
# Varianter som sammenlignes: (navn, decomposermetode, homografhåndtering). "sum": decomposerens
# andeler summeres per leksem (som decomposer gjør i dag: hver homograf-lemma_id får sitt eget fulle
# anslag). "maks": homografe lemma_id av samme leksem teller bare én gang (største anslag), før
# andelene normaliseres; viser hvor mye dobbelttellingen betyr (logg del 42).
VARIANTS = (("regler", "regler", "sum"), ("logreg", "logreg", "sum"), ("logreg_hom", "logreg", "maks"))
MIN_INNHOLD = 0.9  # bred del, hovedutvalg: minst 90 % av OBT-analysene er subst/verb/adj
CONTENT_POS = {"subst", "verb", "adj"}
MIN_N = 100
ZERO = 0.001  # decomposerandel under dette regnes som 0 (leksemet er ikke modellert)
UKOBLET = ("(ukoblet)", "")

# Dyp del: former fra repoet (logg del 40) og lemmaer for profilsammenligning
DEEP_FORMS = ["fisker", "dør", "døde", "går", "hatt", "kroner", "dager", "ønsker", "møter",
              "viser", "landet", "tro"]
# Verbene som rapport_verbtyper.md tok ut av gullstandarden fordi en kollisjon forrykker profilen,
# pluss gå og tro, og substantiv fra decomposerens eksempler.
PROFILE_LEMMAS = [(v, "verb") for v in ("dø", "gå", "tro", "fiske", "stille", "svare", "selge",
                                         "leve", "vinne", "legge", "bygge", "sette", "tape")] + \
                 [(n, "subst") for n in ("fisk", "fisker", "dør", "krone", "land")]
CORE_SLOTS = {"verb": (1, 2, 4, 5, 11), "subst": (1, 2, 3, 4)}

RESULT_DIR = Path(__file__).resolve().parent.parent / "resultater"


# ---------------------------------------------------------------------------
# Hjelpere
# ---------------------------------------------------------------------------

def _connect_ro(path: str | Path) -> sqlite3.Connection:
    c = sqlite3.connect(_ro_uri(path), uri=True)
    c.row_factory = sqlite3.Row
    return c


def lexeme_map(oconn: sqlite3.Connection) -> dict[int, tuple[str, str]]:
    """lemma_id -> (grunnform, pos)."""
    return {r[0]: (r[1], r[2]) for r in oconn.execute(
        "SELECT lemma_id, MIN(grunnform), MIN(pos) FROM lemma_former GROUP BY lemma_id")}


def candidate_lexemes(oconn: sqlite3.Connection, form: str) -> set[tuple[str, str]]:
    return {(r[0], r[1]) for r in oconn.execute(
        "SELECT DISTINCT grunnform, pos FROM lemma_former WHERE oppslag = ?", (form,))}


def obt_distribution(kconn: sqlite3.Connection, form: str,
                     lex: dict[int, tuple[str, str]]) -> tuple[dict[tuple, float], float, float]:
    """OBT-fordeling på leksemer (normalisert over koblede analyser), antall og andel ukoblet."""
    counts: dict[tuple, float] = defaultdict(float)
    for r in form_split(kconn, form):
        key = lex.get(r["lemma_id"], UKOBLET) if r["lemma_id"] is not None else UKOBLET
        counts[key] += r["n"]
    total = sum(counts.values())
    ukoblet = counts.pop(UKOBLET, 0.0)
    linked = sum(counts.values())
    dist = {k: v / linked for k, v in counts.items()} if linked else {}
    return dist, total, (ukoblet / total if total else 0.0)


def decomposer_distribution(est: dict[str, Any], homographs: str = "sum") -> dict[tuple, float]:
    """Decomposerens fordeling per leksem. homographs="maks": homografe lemma_id telles én gang."""
    if homographs == "sum":
        dist: dict[tuple, float] = defaultdict(float)
        for c in est["candidates"]:
            dist[(c["grunnform"], c["pos"])] += c["share"]
        return dict(dist)
    raw: dict[tuple, float] = {}
    for c in est["candidates"]:
        k = (c["grunnform"], c["pos"])
        raw[k] = max(raw.get(k, 0.0), c["raw_est"])
    tot = sum(raw.values())
    return {k: v / tot for k, v in raw.items()} if tot > 0 else {}


def evidence_ratio(est: dict[str, Any]) -> float:
    """Sum av decomposerens ukappede anslag / observert frekvens. Nær 0: lite å regne ut fra, og
    fordelingen styres av normaliseringen; nær 1: anslagene stemmer med observert nivå."""
    obs = est.get("obs_freq") or 0
    return sum(c.get("uncapped_est", c["raw_est"]) for c in est["candidates"]) / obs if obs else 0.0


def _fmt_dist(d: dict[tuple, float], limit: int = 4) -> str:
    items = sorted(d.items(), key=lambda x: -x[1])[:limit]
    return ", ".join(f"{g} ({p}) {v * 100:.0f}" for (g, p), v in items if v >= 0.005)


def compare(p_obt: dict[tuple, float], p_dec: dict[tuple, float]) -> dict[str, Any]:
    keys = set(p_obt) | set(p_dec)
    tvd = 0.5 * sum(abs(p_dec.get(k, 0.0) - p_obt.get(k, 0.0)) for k in keys)
    umod = sum(v for k, v in p_obt.items() if p_dec.get(k, 0.0) < ZERO)
    top_obt = max(p_obt, key=p_obt.get) if p_obt else None
    top_dec = max(p_dec, key=p_dec.get) if p_dec else None
    return {"avvik_pp": 100 * tvd, "umodellert": umod, "riktig_flest": top_obt == top_dec,
            "fordeling": _fmt_dist(p_dec)}


# ---------------------------------------------------------------------------
# 1. Bred del
# ---------------------------------------------------------------------------

def select_forms(kconn: sqlite3.Connection, oconn: sqlite3.Connection, min_n: int = MIN_N) -> list[tuple[str, float]]:
    """Former med >= min_n forekomster og minst to ulike leksemer blant subst/verb/adj i Ordbanken."""
    out = []
    for form, n in kconn.execute("SELECT form, SUM(n) FROM obt_typer GROUP BY form HAVING SUM(n) >= ?", (min_n,)):
        content = {k for k in candidate_lexemes(oconn, form) if k[1] in CONTENT_POS}
        if len(content) >= 2:
            out.append((form, n))
    return sorted(out, key=lambda x: -x[1])


def compare_forms(kconn, oconn, sessions: dict[str, DecomposerSession], forms: list[str],
                  lex: dict[int, tuple[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for form in forms:
        p_obt, n, ukoblet = obt_distribution(kconn, form, lex)
        if not p_obt:
            continue
        row = {"form": form, "n": n, "andel_ukoblet": ukoblet,
               "obt_innhold": sum(v for (g, pos), v in p_obt.items() if pos in CONTENT_POS),
               "kandidater": len(candidate_lexemes(oconn, form)), "obt": _fmt_dist(p_obt)}
        ests = {m: sess.estimate(form) for m, sess in sessions.items()}
        row["grunnlag"] = evidence_ratio(ests["logreg"])
        for name, m, hom in VARIANTS:
            c = compare(p_obt, decomposer_distribution(ests[m], hom))
            row.update({f"{name}_{k}": v for k, v in c.items()})
        rows.append(row)
    return rows


def summarize(rows: list[dict[str, Any]], method: str) -> dict[str, Any]:
    if not rows:
        return {"former": 0}
    av = [r[f"{method}_avvik_pp"] for r in rows]
    q = st.quantiles(av, n=10) if len(av) >= 10 else [max(av)] * 9
    return {
        "former": len(rows),
        "tokens": sum(r["n"] for r in rows),
        "median_avvik_pp": st.median(av),
        "vektet_avvik_pp": sum(r[f"{method}_avvik_pp"] * r["n"] for r in rows) / sum(r["n"] for r in rows),
        "p90_avvik_pp": q[8],
        "riktig_flest": sum(r[f"{method}_riktig_flest"] for r in rows) / len(rows),
        "median_umodellert": st.median(r[f"{method}_umodellert"] for r in rows),
    }


# ---------------------------------------------------------------------------
# 2. Dyp del: profiler
# ---------------------------------------------------------------------------

def _cell_groups(oconn, grunnform: str, pos: str) -> tuple[list[int], list[dict[str, Any]]]:
    """Kjernekategorier for leksemet, slått sammen når de deler form (union-find)."""
    ids = [r[0] for r in oconn.execute(
        "SELECT DISTINCT lemma_id FROM lemma_former WHERE grunnform = ? AND pos = ?", (grunnform, pos))]
    slots = CORE_SLOTS[pos]
    cells: dict[int, dict[str, Any]] = {}
    for bn, txt, form in oconn.execute(
        f"SELECT boy_nummer, boy_tekst, oppslag FROM lemma_former WHERE lemma_id IN ({','.join('?' * len(ids))})",
        ids,
    ):
        if bn in slots:
            c = cells.setdefault(bn, {"tekst": txt, "former": set()})
            c["former"].add(form)
    parent = {bn: bn for bn in cells}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    owner: dict[str, int] = {}
    for bn in sorted(cells):
        for f in cells[bn]["former"]:
            if f in owner:
                parent[find(bn)] = find(owner[f])
            else:
                owner[f] = bn
    groups: dict[int, dict[str, Any]] = {}
    for bn in sorted(cells):
        g = groups.setdefault(find(bn), {"slots": [], "tekst": [], "former": set()})
        g["slots"].append(bn)
        g["tekst"].append(cells[bn]["tekst"])
        g["former"] |= cells[bn]["former"]
    return ids, [{"slots": g["slots"], "kategori": "/".join(g["tekst"]), "former": sorted(g["former"])}
                 for _, g in sorted(groups.items())]


def profile_comparison(kconn, oconn, sessions: dict[str, DecomposerSession], grunnform: str, pos: str,
                       form_n: dict[str, float]) -> list[dict[str, Any]]:
    ids, groups = _cell_groups(oconn, grunnform, pos)
    lexeme = (grunnform, pos)
    share_cache: dict[tuple[str, str], float] = {}

    def share(form: str, variant: tuple[str, str, str]) -> float:
        name, method, hom = variant
        if (form, name) not in share_cache:
            cands = candidate_lexemes(oconn, form)
            share_cache[(form, name)] = 1.0 if cands == {lexeme} else \
                decomposer_distribution(sessions[method].estimate(form), hom).get(lexeme, 0.0)
        return share_cache[(form, name)]

    obt_cells = dict(kconn.execute(
        f"SELECT boy_nummer, SUM(n) FROM v_celle_frekvens WHERE lemma_id IN ({','.join('?' * len(ids))}) "
        "GROUP BY boy_nummer", ids).fetchall())
    rows = []
    for g in groups:
        row = {"lemma": grunnform, "pos": pos, "kategori": g["kategori"], "former": ",".join(g["former"]),
               "flertydige": ",".join(f for f in g["former"] if candidate_lexemes(oconn, f) != {lexeme}),
               "obt_n": sum(obt_cells.get(s, 0.0) for s in g["slots"]),
               "naiv_n": sum(form_n.get(f, 0.0) for f in g["former"])}
        for v in VARIANTS:
            row[f"{v[0]}_n"] = sum(form_n.get(f, 0.0) * share(f, v) for f in g["former"])
        rows.append(row)
    for col in ["obt"] + [v[0] for v in VARIANTS] + ["naiv"]:
        tot = sum(r[f"{col}_n"] for r in rows) or 1.0
        for r in rows:
            r[f"{col}_andel"] = r[f"{col}_n"] / tot
    return rows


def profile_distance(rows: list[dict[str, Any]], col: str) -> dict[str, Any]:
    tvd = 50 * sum(abs(r[f"{col}_andel"] - r["obt_andel"]) for r in rows)
    order = lambda c: [r["kategori"] for r in sorted(rows, key=lambda r: -r[f"{c}_andel"])]
    return {"avvik_pp": tvd, "samme_rekkefolge": order(col) == order("obt"),
            "samme_topp": order(col)[:1] == order("obt")[:1]}


# ---------------------------------------------------------------------------
# Utskrift
# ---------------------------------------------------------------------------

def _write_tsv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})


def _md(rows: list[list[Any]], header: list[str]) -> str:
    def f(v):
        if isinstance(v, bool):
            return "ja" if v else "nei"
        if isinstance(v, float):
            return f"{v:.1f}".replace(".", ",")
        return str(v)
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(f(v) for v in r) + " |" for r in rows]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Valider decomposer mot det OBT-taggede korpuset.")
    p.add_argument("--db", default=str(DEFAULT_SHARED_DB))
    p.add_argument("--min-n", type=int, default=MIN_N)
    p.add_argument("--ut", default=str(RESULT_DIR))
    args = p.parse_args(argv)

    kconn = _connect_ro(args.db)
    oconn = _connect_ro(ORDBANK_DB_PATH)
    lex = lexeme_map(oconn)
    sessions = {m: DecomposerSession(kconn, method=m) for m in METHODS}
    form_n = dict(kconn.execute("SELECT form, SUM(n) FROM obt_typer GROUP BY form").fetchall())
    ut = Path(args.ut)

    # 1. Bred del
    selected = select_forms(kconn, oconn, args.min_n)
    broad = compare_forms(kconn, oconn, sessions, [f for f, _ in selected], lex)
    _write_tsv(broad, ut / "dekomponering_obt_former.tsv")
    content = [r for r in broad if r["obt_innhold"] >= MIN_INNHOLD]
    print(f"## Bred del: {len(broad)} former med >= {args.min_n} forekomster; "
          f"{len(content)} der OBT gir >= {MIN_INNHOLD:.0%} subst/verb/adj\n")
    modelled = [r for r in content if r["logreg_umodellert"] < 0.05]
    subsets = {
        "alle utvalgte former": broad,
        "innholdsord": content,
        "innholdsord, alle kandidater modellert (umodellert < 5 %)": modelled,
        "innholdsord, umodellert >= 5 %": [r for r in content if r["logreg_umodellert"] >= 0.05],
        "modellert, grunnlag >= 0,5": [r for r in modelled if r["grunnlag"] >= 0.5],
        "modellert, grunnlag < 0,5": [r for r in modelled if r["grunnlag"] < 0.5],
    }
    table = []
    for name, rs in subsets.items():
        for v, _, _ in VARIANTS:
            s_ = summarize(rs, v)
            if s_["former"]:
                table.append([name, v, s_["former"], f"{s_['tokens']:,.0f}".replace(",", " "),
                              s_["median_avvik_pp"], s_["vektet_avvik_pp"], s_["p90_avvik_pp"],
                              100 * s_["riktig_flest"], 100 * s_["median_umodellert"]])
    print(_md(table, ["utvalg", "variant", "former", "tokens", "median avvik pp", "vektet avvik pp",
                      "p90 avvik pp", "riktig flest %", "median umodellert %"]))

    # Dyp del: former
    print("\n## Dyp del: utvalgte former\n")
    deep = compare_forms(kconn, oconn, sessions, DEEP_FORMS, lex)
    print(_md([[r["form"], f"{r['n']:.0f}", r["obt"], r["logreg_fordeling"], r["regler_avvik_pp"],
                r["logreg_avvik_pp"], r["logreg_hom_avvik_pp"], 100 * r["logreg_umodellert"], r["grunnlag"]]
               for r in deep],
              ["form", "n", "OBT %", "logreg %", "avvik regler pp", "avvik logreg pp", "avvik logreg_hom pp",
               "umodellert %", "grunnlag"]))

    # Dyp del: profiler
    print("\n## Dyp del: profiler (andel %, OBT / logreg / logreg_hom / naiv)\n")
    prof_rows, summary = [], []
    for g, pos in PROFILE_LEMMAS:
        rows = profile_comparison(kconn, oconn, sessions, g, pos, form_n)
        prof_rows += rows
        d = {c: profile_distance(rows, c) for c in ("logreg", "regler", "logreg_hom", "naiv")}
        cats = " · ".join(
            f"{r['kategori']} {100 * r['obt_andel']:.0f}/{100 * r['logreg_andel']:.0f}/"
            f"{100 * r['logreg_hom_andel']:.0f}/{100 * r['naiv_andel']:.0f}"
            + (f" [{r['flertydige']}]" if r["flertydige"] else "") for r in rows)
        summary.append([f"{g} ({pos})", f"{sum(r['obt_n'] for r in rows):.0f}", d["logreg"]["avvik_pp"],
                        d["regler"]["avvik_pp"], d["logreg_hom"]["avvik_pp"], d["naiv"]["avvik_pp"],
                        d["logreg"]["samme_topp"], d["naiv"]["samme_topp"], cats])
    _write_tsv(prof_rows, ut / "dekomponering_obt_profiler.tsv")
    print(_md(summary, ["lemma", "n (OBT)", "avvik logreg pp", "avvik regler pp", "avvik logreg_hom pp",
                        "avvik naiv pp", "samme topp logreg", "samme topp naiv",
                        "kategorier (flertydige former)"]))
    for s in sessions.values():
        s.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
