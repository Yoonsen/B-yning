"""
Hjelpefunksjoner og SQL-spørringer mot Norsk Ordbank (sqlite/ordbank.db)
for prosjektet «Leksikalske bøyningsprofiler: ordboksdata og historiske n-gram» (MONS).

Kan brukes direkte fra Jupyter Notebooks:
    from sqlite.queries import (
        get_conn,
        lookup_wordform,
        get_paradigm,
        get_verb_profile_forms,
        get_noun_profile_forms,
        find_anchor_forms,
    )
"""

import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "ordbank.db"

# Sentrale bøyningskategorier (boy_nummer) i Norsk Ordbank:
# Substantiv (boy_gruppe = 'substantiv'):
#   1: ent ub   (entall_ubestemt)
#   2: ent be   (entall_bestemt)
#   3: fl ub    (flertall_ubestemt)
#   4: fl be    (flertall_bestemt)
NOUN_CORE_SLOTS = (1, 2, 3, 4)

# Verb (boy_gruppe = 'verb, normal'):
#   1: inf           (infinitiv)
#   2: pres          (presens)
#   3: inf pres pass (passiv / s-form)
#   4: pret          (preteritum)
#   5: perf-part     (supinum / perfektum partisipp)
#  11: imp           (imperativ)
VERB_CORE_SLOTS = (1, 2, 4, 5)
VERB_TENSE_SLOTS = (1, 2, 4)  # inf, pres, pret (som omtalt i abstractet: gå/går/gikk, vite/vet/visste)


def get_conn(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Returnerer en SQLite-tilkobling med Row-factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def lookup_wordform(
    oppslag: str, conn: sqlite3.Connection | None = None
) -> list[dict[str, Any]]:
    """
    Slår opp en ordform (f.eks. 'fisker') og returnerer alle normerte analyser
    (lemma_id, grunnform, pos, ordklasser, boy_gruppe, boy_nummer, boy_tekst, ordbok_tekst).
    """
    close = conn is None
    if conn is None:
        conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT
                lemma_id,
                grunnform,
                pos,
                ordklasser,
                boy_gruppe,
                boy_nummer,
                boy_tekst,
                ordbok_tekst,
                oppslag
            FROM lemma_former
            WHERE oppslag = ?
            ORDER BY pos, grunnform, lemma_id, boy_nummer
            """,
            (oppslag,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        if close:
            conn.close()


def get_paradigm(
    grunnform: str | None = None,
    lemma_id: int | None = None,
    pos: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> list[dict[str, Any]]:
    """
    Henter hele det normerte bøyningsparadigmet (med flertydighetsstatus for hver ordform)
    for et gitt lemma (enten via lemma_id eller grunnform + ev. pos som 'verb' eller 'subst').
    """
    if lemma_id is None and grunnform is None:
        raise ValueError("Må oppgi enten lemma_id eller grunnform.")

    close = conn is None
    if conn is None:
        conn = get_conn()
    try:
        conditions = []
        params: list[Any] = []
        if lemma_id is not None:
            conditions.append("lf.lemma_id = ?")
            params.append(lemma_id)
        if grunnform is not None:
            conditions.append("lf.grunnform = ?")
            params.append(grunnform)
        if pos is not None:
            conditions.append("lf.pos = ?")
            params.append(pos)

        where_clause = " AND ".join(conditions)
        sql = f"""
        SELECT
            lf.lemma_id,
            lf.grunnform,
            lf.pos,
            lf.ordklasser,
            lf.boy_gruppe,
            lf.boy_nummer,
            lf.boy_tekst,
            lf.ordbok_tekst,
            lf.oppslag,
            vf.antall_lemma_id,
            vf.antall_leksem_pos,
            vf.antall_analyser,
            vf.analyser AS alle_analyser_for_ordform
        FROM lemma_former lf
        JOIN ordform_flertydighet vf ON lf.oppslag = vf.oppslag
        WHERE {where_clause}
        ORDER BY lf.lemma_id, lf.boy_nummer, lf.oppslag
        """
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        if close:
            conn.close()


def get_verb_profile_forms(
    grunnform: str | None = None,
    lemma_id: int | None = None,
    slots: tuple[int, ...] = VERB_TENSE_SLOTS,
    conn: sqlite3.Connection | None = None,
) -> list[dict[str, Any]]:
    """
    Henter kjerneformene for verb (standard: 1=inf, 2=pres, 4=pret; ev. 5=perf-part)
    samt informasjon om hver ordform er entydig eller flertydig i ordbanken.
    """
    rows = get_paradigm(grunnform=grunnform, lemma_id=lemma_id, pos="verb", conn=conn)
    return [r for r in rows if r["boy_gruppe"] == "verb, normal" and r["boy_nummer"] in slots]


def get_noun_profile_forms(
    grunnform: str | None = None,
    lemma_id: int | None = None,
    slots: tuple[int, ...] = NOUN_CORE_SLOTS,
    conn: sqlite3.Connection | None = None,
) -> list[dict[str, Any]]:
    """
    Henter kjerneformene for substantiv (1=ent ub, 2=ent be, 3=fl ub, 4=fl be)
    samt informasjon om hver ordform er entydig eller flertydig i ordbanken.
    """
    rows = get_paradigm(grunnform=grunnform, lemma_id=lemma_id, pos="subst", conn=conn)
    return [r for r in rows if r["boy_gruppe"] == "substantiv" and r["boy_nummer"] in slots]


def find_anchor_forms(
    lemma_id: int, conn: sqlite3.Connection | None = None
) -> dict[str, list[dict[str, Any]]]:
    """
    Deler et lemmas ordformer inn i:
      - 'helt_entydige': ordformer som kun har 1 analyse i hele ordbanken (ett lemma, én bøyningskategori)
      - 'leksem_entydige': ordformer som kun tilhører dette lemma_id, men ev. flere bøyningskategorier (f.eks. 'gå' = inf/imp)
      - 'flertydige_mellom_lemma': ordformer som deles med andre lemma_id (f.eks. 'fisker', 'går')
    """
    rows = get_paradigm(lemma_id=lemma_id, conn=conn)
    result: dict[str, list[dict[str, Any]]] = {
        "helt_entydige": [],
        "leksem_entydige": [],
        "flertydige_mellom_lemma": [],
    }
    for r in rows:
        if r["antall_analyser"] == 1:
            result["helt_entydige"].append(r)
        elif r["antall_lemma_id"] == 1:
            result["leksem_entydige"].append(r)
        else:
            result["flertydige_mellom_lemma"].append(r)
    return result
