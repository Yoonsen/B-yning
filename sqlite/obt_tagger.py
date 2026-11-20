#!/usr/bin/env python3
"""
Kjører Oslo-Bergen-taggeren (OBT) på en tekstfil og leser resultatet inn som tabellrader.

OBT er en kjede av tre trinn:
  1. mtag (multitagger): tokenisering + oppslag i Norsk Ordbank -> alle mulige analyser per ord
  2. VISL CG-3: regelbasert disambiguering ut fra kontekst
  3. OBT-Stat: statistisk disambiguering (kun bokmål) -> normalt én analyse per ord

OBT må være installert separat (Linux). Modulen finner installasjonen via miljøvariabelen
OBT_DIR, ellers ~/opt/obt. Mappen skal inneholde tag-bm.sh, tag-nostat-bm.sh, cg/, mtag/ og
OBT-Stat/, og `vislcg3`, `python3`, `ruby` og `perl` må ligge på PATH. Se logg.md (del 21–22).

Selve parsingen (`parse_obt_output`) bruker bare standardbiblioteket og kan kjøres hvor som helst,
f.eks. på en OBT-fil som er kopiert fra Linux-maskinen.

Bruk fra kommandolinjen (fra repo-roten):
    python -m sqlite.obt_tagger tekster/test-tekst-bokselskap.txt --out /tmp/test.tsv
    python -m sqlite.obt_tagger --parse-only /tmp/obt_full.txt --out /tmp/test.tsv

Bruk fra Python / notebook:
    from sqlite.obt_tagger import tag_file, to_rows
    tokens = tag_file("tekster/test-tekst-bokselskap.txt")
    rows = to_rows(tokens)          # én rad per analyse
"""

import argparse
import csv
import os
import re
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_OBT_DIR = Path(os.environ.get("OBT_DIR", Path.home() / "opt" / "obt"))

_WORD_RE = re.compile(r"^<word>(.*)</word>$")
_FORM_RE = re.compile(r'^"<(.*)>"$')
_READING_RE = re.compile(r'^\s+"(.*)"(?:\s+(.*))?$')


def _is_marker(tag: str) -> bool:
    """OBT-markører som ikke er ordklasse eller bøyningstrekk. `clb` (setningsgrense) settes av OBT
    både på setningsavsluttende tegn ("$." clb <punkt>) og på konjunksjoner (*og*, *men*)."""
    return tag == "clb" or tag.startswith("<") or tag.startswith("samset") or tag.startswith("flerord")


class ObtTimeout(RuntimeError):
    """OBT brukte lengre tid enn tidsgrensen (f.eks. fordi mtag.py henger på en tekst)."""


def run_obt(
    text_path: str | Path,
    obt_dir: str | Path = DEFAULT_OBT_DIR,
    stat: bool = True,
    timeout: float | None = None,
) -> str:
    """
    Kjører OBT på `text_path` (UTF-8 ren tekst) og returnerer rå OBT-utdata som streng.
    `stat=True` bruker tag-bm.sh (CG + OBT-Stat), `stat=False` tag-nostat-bm.sh (kun CG).
    Advarsler fra mtag/OBT-Stat på stderr ignoreres med mindre kjøringen feiler.
    `timeout` (sekunder): hele OBT-kjeden (skallskript + mtag/vislcg3/ruby/perl) avbrytes og
    `ObtTimeout` kastes hvis den bruker lengre tid. mtag.py kan gå i evig løkke på enkelte tekster
    under nyere Python (sett 2026-11-19, logg del 33).
    """
    obt_dir = Path(obt_dir).expanduser().resolve()
    script = obt_dir / ("tag-bm.sh" if stat else "tag-nostat-bm.sh")
    if not script.exists():
        raise FileNotFoundError(
            f"Fant ikke {script}. Sett OBT_DIR eller send inn obt_dir= til OBT-installasjonen."
        )
    text_path = Path(text_path).expanduser().resolve()
    if not text_path.exists():
        raise FileNotFoundError(text_path)

    # Skriptet finner mtag/, cg/ og OBT-Stat/ via $(dirname $0), så vi kaller det med full sti.
    # Egen prosessgruppe (start_new_session), slik at hele kjeden kan stoppes ved tidsavbrudd;
    # subprocess.run(timeout=…) ville bare stoppet skallskriptet og latt mtag.py fortsette.
    proc = subprocess.Popen(
        [str(script), str(text_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.communicate()
        raise ObtTimeout(f"OBT brukte mer enn {timeout:.0f} s på {text_path.name}")
    if proc.returncode != 0:
        raise RuntimeError(f"OBT feilet (kode {proc.returncode}):\n{stderr[-2000:]}")
    return stdout


def parse_obt_output(obt_text: str) -> list[dict[str, Any]]:
    """
    Leser OBT-utdata (CG-format med <word>-tagger) til en liste med tokens:
      {
        "token_nr": 1,
        "ord": "Forfatteren",        # slik ordet står i teksten
        "form": "forfatteren",       # ordformen OBT slo opp (små bokstaver)
        "analyser": [ {"lemma": "forfatter", "pos": "subst", "trekk": ["appell", "mask", "be", "ent"],
                       "ekstra": []} , ... ]
      }
    `trekk` er morfologiske trekk; `ekstra` er OBT-markører i vinkelparentes (f.eks. <*> for stor
    forbokstav, <+debattanten> for sammensetningsledd, <komma>) og merknader som samset-analyse og
    flerord-ledd1. Tegnsetting (lemma som starter med $, f.eks. "$,") får pos = "tegn".
    Ord som ikke finnes i Norsk Ordbank (f.eks. gammel rettskrivning som «aar») får pos = "ukjent".
    Linjer som ikke passer formatet hoppes over.
    """
    tokens: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    pending_word: str | None = None

    for line in obt_text.splitlines():
        if not line.strip():
            continue
        m = _WORD_RE.match(line)
        if m:
            pending_word = m.group(1)
            continue
        m = _FORM_RE.match(line)
        if m:
            current = {
                "token_nr": len(tokens) + 1,
                "ord": pending_word if pending_word is not None else m.group(1),
                "form": m.group(1),
                "analyser": [],
            }
            tokens.append(current)
            pending_word = None
            continue
        m = _READING_RE.match(line)
        if m and current is not None:
            lemma = m.group(1)
            tags = (m.group(2) or "").split()
            # Markører (<*>, <komma>, <+ledd>, samset-..., flerord-...) skilles fra ordklasse og trekk.
            plain = [t for t in tags if not _is_marker(t)]
            ekstra = [t for t in tags if _is_marker(t)]
            if plain:
                pos, trekk = plain[0], plain[1:]
            elif lemma.startswith("$"):
                # Tegnsetting har ingen ordklasse i OBT, kun en markør: "$," <komma>
                pos, trekk = "tegn", []
            else:
                pos, trekk = "", []
            current["analyser"].append(
                {"lemma": lemma, "pos": pos, "trekk": trekk, "ekstra": ekstra}
            )
    return tokens


def to_rows(tokens: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flater ut tokens til én rad per analyse (praktisk for CSV/pandas)."""
    rows = []
    for tok in tokens:
        n = len(tok["analyser"])
        for i, a in enumerate(tok["analyser"], start=1):
            rows.append(
                {
                    "token_nr": tok["token_nr"],
                    "ord": tok["ord"],
                    "form": tok["form"],
                    "analyse_nr": i,
                    "antall_analyser": n,
                    "lemma": a["lemma"],
                    "pos": a["pos"],
                    "trekk": " ".join(a["trekk"]),
                    "ekstra": " ".join(a["ekstra"]),
                }
            )
    return rows


def tag_file(
    text_path: str | Path,
    obt_dir: str | Path = DEFAULT_OBT_DIR,
    stat: bool = True,
) -> list[dict[str, Any]]:
    """Kjører OBT på en tekstfil og returnerer parsede tokens (se `parse_obt_output`)."""
    return parse_obt_output(run_obt(text_path, obt_dir=obt_dir, stat=stat))


def summarize(tokens: list[dict[str, Any]]) -> dict[str, Any]:
    """Enkel oversikt: antall tokens, hvor mange som fortsatt har >1 analyse, og ordklassefordeling."""
    from collections import Counter

    n_amb = sum(1 for t in tokens if len(t["analyser"]) > 1)
    pos_counts = Counter(t["analyser"][0]["pos"] for t in tokens if t["analyser"])
    return {
        "antall_tokens": len(tokens),
        "flertydige_tokens": n_amb,
        "uten_analyse": sum(1 for t in tokens if not t["analyser"]),
        "ordklasser": dict(pos_counts.most_common()),
    }


def write_tsv(rows: list[dict[str, Any]], out_path: str | Path) -> None:
    fields = ["token_nr", "ord", "form", "analyse_nr", "antall_analyser",
              "lemma", "pos", "trekk", "ekstra"]
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        w.writeheader()
        w.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Tagg en tekstfil med OBT og skriv resultatet som TSV.")
    p.add_argument("fil", help="Tekstfil (UTF-8), eller rå OBT-utdata med --parse-only")
    p.add_argument("--out", help="TSV-fil å skrive (én rad per analyse). Utelates: kun oppsummering.")
    p.add_argument("--obt-dir", default=str(DEFAULT_OBT_DIR), help="OBT-installasjon (standard: $OBT_DIR eller ~/opt/obt)")
    p.add_argument("--nostat", action="store_true", help="Bruk kun CG (tag-nostat-bm.sh), uten OBT-Stat")
    p.add_argument("--parse-only", action="store_true", help="Les en eksisterende OBT-utdatafil i stedet for å kjøre OBT")
    args = p.parse_args(argv)

    if args.parse_only:
        tokens = parse_obt_output(Path(args.fil).read_text(encoding="utf-8"))
    else:
        tokens = tag_file(args.fil, obt_dir=args.obt_dir, stat=not args.nostat)

    s = summarize(tokens)
    print(f"Tokens: {s['antall_tokens']}  |  fortsatt flertydige: {s['flertydige_tokens']}  |  uten analyse: {s['uten_analyse']}")
    print("Ordklasser:", ", ".join(f"{k}={v}" for k, v in s["ordklasser"].items()))
    if args.out:
        write_tsv(to_rows(tokens), args.out)
        print(f"Skrev {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
