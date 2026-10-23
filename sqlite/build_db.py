#!/usr/bin/env python3
"""
Bygger SQLite-database (sqlite/ordbank.db) fra Norsk Ordbank (nob 2005, ISO-8859-1 TSV-filer).
Oppretter tabeller, indekser og sentrale views for analyse av bøyningsprofiler og flertydighet.
"""

import csv
import os
import sqlite3
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "20220201_norsk_ordbank_nob_2005"
DB_PATH = Path(__file__).resolve().parent / "ordbank.db"


def load_tsv(
    conn: sqlite3.Connection,
    table_name: str,
    filename: str,
    columns: list[tuple[str, str]],
) -> int:
    filepath = SRC_DIR / filename
    col_defs = ", ".join(f"{name} {dtype}" for name, dtype in columns)
    col_names = ", ".join(name for name, _ in columns)
    placeholders = ", ".join("?" for _ in columns)

    conn.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.execute(f"CREATE TABLE {table_name} ({col_defs})")

    int_cols = {i for i, (_, dtype) in enumerate(columns) if "INTEGER" in dtype}

    rows = []
    count = 0
    with open(filepath, mode="r", encoding="latin1", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, None)  # skip header
        for row in reader:
            if not row:
                continue
            parsed = []
            for i in range(len(columns)):
                val = row[i].strip() if i < len(row) else ""
                if val == "":
                    parsed.append(None)
                elif i in int_cols:
                    try:
                        parsed.append(int(val))
                    except ValueError:
                        parsed.append(val)
                else:
                    parsed.append(val)
            rows.append(parsed)
            if len(rows) >= 50000:
                conn.executemany(
                    f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})",
                    rows,
                )
                count += len(rows)
                rows.clear()

    if rows:
        conn.executemany(
            f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})",
            rows,
        )
        count += len(rows)

    conn.commit()
    return count


def build_database():
    t0 = time.time()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")

    tables = [
        (
            "boying_grupper",
            "boying_grupper.txt",
            [
                ("loepenr", "INTEGER PRIMARY KEY"),
                ("boy_gruppe", "TEXT"),
            ],
        ),
        (
            "boying",
            "boying.txt",
            [
                ("loepenr", "INTEGER PRIMARY KEY"),
                ("boy_nummer", "INTEGER"),
                ("boy_gruppe", "TEXT"),
                ("boy_tekst", "TEXT"),
                ("ordbok_tekst", "TEXT"),
            ],
        ),
        (
            "paradigme",
            "paradigme.txt",
            [
                ("loepenr", "INTEGER PRIMARY KEY"),
                ("paradigme_id", "TEXT"),
                ("boy_gruppe", "TEXT"),
                ("ordklasse", "TEXT"),
                ("ordklasse_utdyping", "TEXT"),
                ("forklaring", "TEXT"),
                ("doeme", "TEXT"),
                ("id", "INTEGER"),
            ],
        ),
        (
            "paradigme_boying",
            "paradigme_boying.txt",
            [
                ("loepenr", "INTEGER PRIMARY KEY"),
                ("paradigme_id", "TEXT"),
                ("boy_nummer", "INTEGER"),
                ("boy_gruppe", "TEXT"),
                ("boy_uttrykk", "TEXT"),
            ],
        ),
        (
            "lemma",
            "lemma.txt",
            [
                ("loepenr", "INTEGER PRIMARY KEY"),
                ("lemma_id", "INTEGER"),
                ("grunnform", "TEXT"),
                ("bm_ordbok", "TEXT"),
            ],
        ),
        (
            "lemma_paradigme",
            "lemma_paradigme.txt",
            [
                ("loepenr", "INTEGER PRIMARY KEY"),
                ("lemma_id", "INTEGER"),
                ("paradigme_id", "TEXT"),
                ("normering", "TEXT"),
                ("fradato", "TEXT"),
                ("tildato", "TEXT"),
                ("kommentar", "TEXT"),
            ],
        ),
        (
            "leddanalyse",
            "leddanalyse.txt",
            [
                ("loepenr", "INTEGER PRIMARY KEY"),
                ("leddanalyse_id", "INTEGER"),
                ("oppslag", "TEXT"),
                ("leddanalyse", "TEXT"),
                ("forledd", "TEXT"),
                ("forledd_gram", "TEXT"),
                ("fuge", "TEXT"),
                ("etterledd", "TEXT"),
                ("etterledd_gram", "TEXT"),
                ("leddmarkert_bob", "TEXT"),
                ("neg_fuge", "TEXT"),
                ("oppslag_ledd_markert", "TEXT"),
                ("bindestreksform_for_lemma", "TEXT"),
                ("lemma_id", "INTEGER"),
            ],
        ),
        (
            "fullformsliste",
            "fullformsliste.txt",
            [
                ("loepenr", "INTEGER PRIMARY KEY"),
                ("lemma_id", "INTEGER"),
                ("oppslag", "TEXT"),
                ("tag", "TEXT"),
                ("paradigme_id", "TEXT"),
                ("boy_nummer", "INTEGER"),
                ("fradato", "TEXT"),
                ("tildato", "TEXT"),
                ("normering", "TEXT"),
            ],
        ),
    ]

    for table_name, filename, cols in tables:
        t_start = time.time()
        n = load_tsv(conn, table_name, filename, cols)
        print(f"Lastet {table_name:18s}: {n:9d} rader ({time.time() - t_start:.2f}s)")

    print("Bygger indekser...")
    indexes = [
        "CREATE INDEX idx_lemma_id ON lemma(lemma_id)",
        "CREATE INDEX idx_lemma_grunnform ON lemma(grunnform)",
        "CREATE INDEX idx_paradigme_id ON paradigme(paradigme_id)",
        "CREATE INDEX idx_boying_gruppe_nr ON boying(boy_gruppe, boy_nummer)",
        "CREATE INDEX idx_lemma_paradigme_lid ON lemma_paradigme(lemma_id)",
        "CREATE INDEX idx_lemma_paradigme_pid ON lemma_paradigme(paradigme_id)",
        "CREATE INDEX idx_fullform_lemma_id ON fullformsliste(lemma_id)",
        "CREATE INDEX idx_fullform_oppslag ON fullformsliste(oppslag)",
        "CREATE INDEX idx_fullform_paradigme ON fullformsliste(paradigme_id, boy_nummer)",
        "CREATE INDEX idx_ledd_lemma_id ON leddanalyse(lemma_id)",
    ]
    for idx_sql in indexes:
        conn.execute(idx_sql)

    print("Oppretter materialisert tabell lemma_former og views...")
    # Materialisert tabell lemma_former:
    # Dedupliserer over alternative paradigmer (inkl. mask/fem-valgfrihet i bokmål) for samme lemma,
    # slik at hver kombinasjon av (lemma_id, grunnform, pos, boy_gruppe, boy_nummer, boy_tekst, ordbok_tekst, oppslag)
    # kun lagres én gang (kun normerte former), og indekseres for umiddelbare oppslag (<1 ms).
    conn.execute("DROP TABLE IF EXISTS lemma_former")
    conn.execute("""
    CREATE TABLE lemma_former AS
    SELECT
        f.lemma_id,
        l.grunnform,
        SUBSTR(p.ordklasse, 1, INSTR(p.ordklasse || ' ', ' ') - 1) AS pos,
        GROUP_CONCAT(DISTINCT p.ordklasse) AS ordklasser,
        p.boy_gruppe,
        f.boy_nummer,
        b.boy_tekst,
        b.ordbok_tekst,
        f.oppslag
    FROM fullformsliste f
    JOIN lemma l ON f.lemma_id = l.lemma_id
    JOIN paradigme p ON f.paradigme_id = p.paradigme_id
    LEFT JOIN boying b ON p.boy_gruppe = b.boy_gruppe AND f.boy_nummer = b.boy_nummer
    WHERE f.normering = 'normert'
    GROUP BY
        f.lemma_id,
        l.grunnform,
        SUBSTR(p.ordklasse, 1, INSTR(p.ordklasse || ' ', ' ') - 1),
        p.boy_gruppe,
        f.boy_nummer,
        b.boy_tekst,
        b.ordbok_tekst,
        f.oppslag
    """)
    conn.execute("CREATE INDEX idx_lf_oppslag ON lemma_former(oppslag)")
    conn.execute("CREATE INDEX idx_lf_lemma_id ON lemma_former(lemma_id)")
    conn.execute("CREATE INDEX idx_lf_grunnform ON lemma_former(grunnform, pos)")

    conn.execute("CREATE VIEW v_lemma_former AS SELECT * FROM lemma_former")

    # Materialisert tabell ordform_flertydighet (og view v_ordform_flertydighet):
    # Viser for hver ordform (oppslag) hvor mange ulike (lemma_id, boy_gruppe, boy_nummer)
    # og hvor mange ulike grunnformer den kan representere, med PK-indeks på oppslag.
    conn.execute("DROP TABLE IF EXISTS ordform_flertydighet")
    conn.execute("""
    CREATE TABLE ordform_flertydighet AS
    SELECT
        oppslag,
        COUNT(DISTINCT lemma_id) AS antall_lemma_id,
        COUNT(DISTINCT grunnform || ':' || pos) AS antall_leksem_pos,
        COUNT(*) AS antall_analyser,
        GROUP_CONCAT(
            grunnform || ' (' || pos || ' ' || COALESCE(boy_tekst, '') || ', id=' || lemma_id || ')',
            ' | '
        ) AS analyser
    FROM lemma_former
    GROUP BY oppslag
    """)
    conn.execute("CREATE UNIQUE INDEX idx_of_oppslag ON ordform_flertydighet(oppslag)")
    conn.execute("CREATE VIEW v_ordform_flertydighet AS SELECT * FROM ordform_flertydighet")

    print("Henter topp 500 000 ordform-frekvenser fra NB DH-lab (nb_totals)...")
    try:
        import json
        import urllib.request

        with urllib.request.urlopen("https://api.nb.no/dhlab/totals/500000", timeout=30) as resp:
            totals = json.loads(resp.read().decode("utf-8"))
        conn.execute("DROP TABLE IF EXISTS nb_totals")
        conn.execute("CREATE TABLE nb_totals (oppslag TEXT PRIMARY KEY, freq INTEGER)")
        conn.executemany("INSERT OR IGNORE INTO nb_totals (oppslag, freq) VALUES (?, ?)", totals)
        print(f"Lastet nb_totals          : {len(totals):9d} rader")
    except Exception as e:
        print(f"Kunne ikke hente nb_totals fra nett ({e}); hopper over.")

    conn.commit()
    conn.close()
    print(f"Ferdig! Database lagret til {DB_PATH} på {time.time() - t0:.2f}s.")


if __name__ == "__main__":
    build_database()
