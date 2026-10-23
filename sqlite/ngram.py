"""
Modul for å hente og cache historiske n-gramdata fra Nasjonalbiblioteket (NB DH-lab)
og koble dem sammen med bøyningsparadigmer fra Norsk Ordbank (sqlite/ordbank.db).

Støtter begge API-endepunktene:
  1. https://api.nb.no/dhlab/ngram_book (og /ngram_newspapers) - tar mange ord i ett POST-kall
  2. https://www.nb.no/sp_tjenester/beta/ngram_1/ngram/query - tar opptil 10 ord i ett GET-kall

Alle hentede tidsserier mellomlagres lokalt i `sqlite/ngram_cache.db` slik at gjentatte oppslag
i notebooks og skript skjer umiddelbart (< 1 ms).
"""

import json
import sqlite3
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from sqlite.queries import (
    NOUN_CORE_SLOTS,
    VERB_CORE_SLOTS,
    VERB_TENSE_SLOTS,
    get_noun_profile_forms,
    get_paradigm,
    get_verb_profile_forms,
)

CACHE_DB_PATH = Path(__file__).resolve().parent / "ngram_cache.db"
DHLAB_BASE_URL = "https://api.nb.no/dhlab"
SP_NGRAM_URL = "https://www.nb.no/sp_tjenester/beta/ngram_1/ngram/query"


def _get_cache_conn(db_path: Path = CACHE_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ngram_cache (
            corpus TEXT,
            lang TEXT,
            word TEXT,
            year INTEGER,
            freq REAL,
            PRIMARY KEY (corpus, lang, word, year)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ngram_fetched_ranges (
            corpus TEXT,
            lang TEXT,
            word TEXT,
            year_from INTEGER,
            year_to INTEGER,
            PRIMARY KEY (corpus, lang, word)
        )
    """)
    return conn


def fetch_ngram_dhlab(
    words: list[str],
    period: tuple[int, int] = (1950, 2020),
    corpus: str = "book",
    lang: str = "nob",
    use_cache: bool = True,
    batch_size: int = 80,
) -> dict[str, dict[int, float]]:
    """
    Henter årlige frekvenser (absolutte treff per år) fra https://api.nb.no/dhlab/ngram_{corpus}
    for en liste med ordformer. Mellomlagrer resultatene i sqlite/ngram_cache.db.

    Returnerer: {ordform: {år: frekvens, ...}, ...}
    """
    y_from, y_to = period
    unique_words = list(dict.fromkeys(words))
    conn = _get_cache_conn()

    missing_words = []
    if use_cache:
        for w in unique_words:
            row = conn.execute(
                """
                SELECT year_from, year_to FROM ngram_fetched_ranges
                WHERE corpus = ? AND lang = ? AND word = ?
                """,
                (f"dhlab_{corpus}", lang, w),
            ).fetchone()
            if row is None or row[0] > y_from or row[1] < y_to:
                missing_words.append(w)
    else:
        missing_words = unique_words

    if missing_words:
        endpoint = f"{DHLAB_BASE_URL}/ngram_{corpus}"
        for i in range(0, len(missing_words), batch_size):
            batch = missing_words[i : i + batch_size]
            payload: dict[str, Any] = {
                "word": batch,
                "period": [y_from, y_to],
            }
            if corpus in ("book", "periodicals") and lang:
                payload["lang"] = lang

            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (MONS-Boyningsprofiler)",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw_data = json.loads(resp.read().decode("utf-8"))

            rows_to_insert = []
            for key, count in raw_data.items():
                parts = key.rsplit(" ", 1)
                if len(parts) == 2:
                    w_key, yr_str = parts
                    try:
                        yr = int(yr_str)
                        rows_to_insert.append(
                            (f"dhlab_{corpus}", lang, w_key, yr, float(count))
                        )
                    except ValueError:
                        pass

            conn.executemany(
                """
                INSERT OR REPLACE INTO ngram_cache (corpus, lang, word, year, freq)
                VALUES (?, ?, ?, ?, ?)
                """,
                rows_to_insert,
            )
            for w in batch:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO ngram_fetched_ranges (corpus, lang, word, year_from, year_to)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (f"dhlab_{corpus}", lang, w, y_from, y_to),
                )
            conn.commit()

    result: dict[str, dict[int, float]] = {
        w: {yr: 0.0 for yr in range(y_from, y_to + 1)} for w in unique_words
    }
    placeholders = ",".join("?" for _ in unique_words)
    cached_rows = conn.execute(
        f"""
        SELECT word, year, freq
        FROM ngram_cache
        WHERE corpus = ? AND lang = ?
          AND year BETWEEN ? AND ?
          AND word IN ({placeholders})
        """,
        [f"dhlab_{corpus}", lang, y_from, y_to, *unique_words],
    ).fetchall()
    conn.close()

    for w, yr, freq in cached_rows:
        if w in result:
            result[w][int(yr)] = float(freq)

    return result


def fetch_ngram_sp(
    words: list[str],
    period: tuple[int, int] = (1950, 2020),
    corpus: str = "bok",
    lang: str = "nob",
    freq_mode: str = "rel",
    case_sens: int = 0,
) -> dict[str, dict[int, float]]:
    """
    Henter n-gram fra det raske 10-ords-endepunktet:
    https://www.nb.no/sp_tjenester/beta/ngram_1/ngram/query
    Deler automatisk opp i bolker på maks 10 ord.
    """
    y_from, y_to = period
    unique_words = list(dict.fromkeys(words))
    result: dict[str, dict[int, float]] = {
        w: {yr: 0.0 for yr in range(y_from, y_to + 1)} for w in unique_words
    }

    for i in range(0, len(unique_words), 10):
        batch = unique_words[i : i + 10]
        params = urllib.parse.urlencode(
            {
                "terms": ",".join(batch),
                "corpus": corpus,
                "lang": lang,
                "case_sens": str(case_sens),
                "freq": freq_mode,
            }
        )
        url = f"{SP_NGRAM_URL}?{params}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "Referer": "https://www.nb.no/sp_tjenester/beta/ngram_1/",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            series_list = json.loads(resp.read().decode("utf-8"))

        for series in series_list:
            w = series.get("key")
            if w in result:
                for pt in series.get("values", []):
                    yr = int(pt["x"])
                    if y_from <= yr <= y_to:
                        result[w][yr] = float(pt["y"])

    return result


def compute_paradigm_profile(
    grunnform: str | None = None,
    lemma_id: int | None = None,
    pos: str = "verb",
    slots: tuple[int, ...] | None = None,
    period: tuple[int, int] = (1950, 2020),
    corpus: str = "book",
    lang: str = "nob",
) -> dict[str, Any]:
    """
    Kobler et lemmas bøyningsparadigme i Norsk Ordbank med historiske n-grammer (1950-2020)
    og beregner:
      - frekvens per bøyningskategori (summerer ev. parallelle former i samme kategori,
        f.eks. 'vet'+'veit' i presens eller 'epla'+'eplene' i bestemt flertall)
      - relativ andel (proporsjon innenfor paradigmet) per år og samlet for hele perioden
      - hvilken bøyningsform som dominerer ("på topp"), samt stabilitetsmål over tid:
          * std_per_slot: standardavvik for andelen fra år til år
          * top_slot_consistency: andel av årene der hovedkategorien ligger på 1. plass
          * decade_profiles: gjennomsnittlig bøyningsprofil per tiår (1950s, 1960s, ..., 2010s)
    """
    if pos == "verb":
        if slots is None:
            slots = VERB_TENSE_SLOTS
        forms = get_verb_profile_forms(grunnform=grunnform, lemma_id=lemma_id, slots=slots)
    elif pos == "subst":
        if slots is None:
            slots = NOUN_CORE_SLOTS
        forms = get_noun_profile_forms(grunnform=grunnform, lemma_id=lemma_id, slots=slots)
    else:
        forms = get_paradigm(grunnform=grunnform, lemma_id=lemma_id, pos=pos)
        if slots is not None:
            forms = [r for r in forms if r["boy_nummer"] in slots]

    if not forms:
        raise ValueError(f"Fant ingen normerte former for grunnform={grunnform}, lemma_id={lemma_id}, pos={pos}")

    wordforms = list(dict.fromkeys(r["oppslag"] for r in forms))
    ts_by_word = fetch_ngram_dhlab(wordforms, period=period, corpus=corpus, lang=lang)

    y_from, y_to = period
    years = list(range(y_from, y_to + 1))

    # Hvis flere homografe lemma_id matcher samme grunnform (f.eks. 'vinne' med pret 'vinte' vs 'vant',
    # 'bok' med flertall 'boker' vs 'bøker', eller 'sol' (musikknote) vs 'sol' (solen/sola)),
    # velger vi det lemma_id som har flest fylte bøyningskategorier og høyest totalfrekvens i korpuset.
    if lemma_id is not None:
        target_lemma_id = lemma_id
    else:
        candidate_lids = sorted({r["lemma_id"] for r in forms})
        if len(candidate_lids) == 1:
            target_lemma_id = candidate_lids[0]
        else:
            def _score_lemma(lid: int) -> tuple[int, float]:
                l_forms = [r for r in forms if r["lemma_id"] == lid]
                n_slots = len({r["boy_nummer"] for r in l_forms})
                tot_freq = sum(
                    sum(ts_by_word.get(r["oppslag"], {}).values())
                    for r in l_forms
                )
                return (n_slots, tot_freq)

            target_lemma_id = max(candidate_lids, key=_score_lemma)

    forms = [r for r in forms if r["lemma_id"] == target_lemma_id]

    # Gruppér ordformer etter bøyningskategori (boy_nummer, boy_tekst)
    slot_meta: dict[int, dict[str, Any]] = {}
    for r in forms:
        bnr = r["boy_nummer"]
        if bnr not in slot_meta:
            slot_meta[bnr] = {
                "boy_nummer": bnr,
                "boy_tekst": r["boy_tekst"],
                "ordbok_tekst": r["ordbok_tekst"],
                "former": [],
                "max_antall_lemma_id": 0,
            }
        slot_meta[bnr]["former"].append(r["oppslag"])
        slot_meta[bnr]["max_antall_lemma_id"] = max(
            slot_meta[bnr]["max_antall_lemma_id"], r["antall_lemma_id"]
        )

    ordered_slots = sorted(slot_meta.keys())
    slot_labels = {bnr: slot_meta[bnr]["boy_tekst"] for bnr in ordered_slots}

    # Beregn årlige frekvenser per bøyningskategori (slot)
    yearly_slot_counts: dict[int, dict[int, float]] = {
        bnr: {yr: 0.0 for yr in years} for bnr in ordered_slots
    }
    for bnr in ordered_slots:
        for w in slot_meta[bnr]["former"]:
            for yr in years:
                yearly_slot_counts[bnr][yr] += ts_by_word.get(w, {}).get(yr, 0.0)

    # Beregn totale treff og proporsjoner per år og samlet
    total_per_slot = {bnr: sum(yearly_slot_counts[bnr].values()) for bnr in ordered_slots}
    grand_total = sum(total_per_slot.values())

    overall_proportions = {
        slot_labels[bnr]: (total_per_slot[bnr] / grand_total if grand_total > 0 else 0.0)
        for bnr in ordered_slots
    }

    yearly_proportions: dict[str, dict[int, float]] = {
        slot_labels[bnr]: {} for bnr in ordered_slots
    }
    top_slot_by_year: dict[int, str] = {}

    for yr in years:
        yr_tot = sum(yearly_slot_counts[bnr][yr] for bnr in ordered_slots)
        if yr_tot > 0:
            for bnr in ordered_slots:
                yearly_proportions[slot_labels[bnr]][yr] = yearly_slot_counts[bnr][yr] / yr_tot
            best_bnr = max(ordered_slots, key=lambda b: yearly_slot_counts[b][yr])
            top_slot_by_year[yr] = slot_labels[best_bnr]

    # Finn dominerende kategori ("på topp") og måle stabilitet over tid
    dominant_slot = (
        max(overall_proportions, key=lambda k: overall_proportions[k])
        if grand_total > 0
        else None
    )
    active_years = list(top_slot_by_year.keys())
    top_slot_consistency = (
        sum(1 for yr in active_years if top_slot_by_year[yr] == dominant_slot) / len(active_years)
        if active_years and dominant_slot
        else 0.0
    )

    # Standardavvik over aktive år (med minst 50 totale forekomster i året for å unngå småtallsstøy)
    reliable_years = [
        yr for yr in years if sum(yearly_slot_counts[bnr][yr] for bnr in ordered_slots) >= 50
    ]
    if not reliable_years:
        reliable_years = active_years

    std_per_slot: dict[str, float] = {}
    for bnr in ordered_slots:
        lbl = slot_labels[bnr]
        vals = [yearly_proportions[lbl][yr] for yr in reliable_years if yr in yearly_proportions[lbl]]
        if len(vals) > 1:
            mean_v = sum(vals) / len(vals)
            var_v = sum((v - mean_v) ** 2 for v in vals) / len(vals)
            std_per_slot[lbl] = var_v**0.5
        else:
            std_per_slot[lbl] = 0.0

    # Tiårsprofiler (1950-tallet, 1960-tallet, ..., 2010-tallet)
    decade_profiles: dict[str, dict[str, float]] = {}
    for dec_start in range((y_from // 10) * 10, y_to + 1, 10):
        dec_years = [yr for yr in years if dec_start <= yr < dec_start + 10]
        dec_tot = sum(yearly_slot_counts[bnr][yr] for bnr in ordered_slots for yr in dec_years)
        if dec_tot > 0:
            dec_label = f"{dec_start}-tallet"
            decade_profiles[dec_label] = {
                slot_labels[bnr]: sum(yearly_slot_counts[bnr][yr] for yr in dec_years) / dec_tot
                for bnr in ordered_slots
            }

    return {
        "lemma_id": target_lemma_id,
        "grunnform": forms[0]["grunnform"],
        "pos": pos,
        "period": period,
        "grand_total": int(grand_total),
        "dominant_slot": dominant_slot,
        "dominant_share": overall_proportions.get(dominant_slot, 0.0) if dominant_slot else 0.0,
        "top_slot_consistency": top_slot_consistency,
        "overall_proportions": overall_proportions,
        "std_per_slot": std_per_slot,
        "slot_meta": {slot_labels[bnr]: slot_meta[bnr] for bnr in ordered_slots},
        "decade_profiles": decade_profiles,
        "yearly_proportions": yearly_proportions,
        "yearly_slot_counts": {slot_labels[bnr]: yearly_slot_counts[bnr] for bnr in ordered_slots},
        "yearly_word_counts": ts_by_word,
    }
