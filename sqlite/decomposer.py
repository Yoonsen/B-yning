#!/usr/bin/env python3
"""
Generell paradigme-basert estimator for flertydige ordformer (homografer) i Norsk Ordbank + NB-korpuset.

Gitt en hvilken som helst ordform `oppslag` (f.eks. 'fisker', 'hatt', 'kroner', 'viser', 'landet', 'møter'),
finner modulen alle normerte kandidat-paradigmer i `sqlite/ordbank.db` og estimerer hvor stor andel av
ordformens frekvens som stammer fra hvert enkelt leksem (`lemma_id`) ved å bruke frekvensen til
resten av paradigmet (de entydige / ikke-kolliderende bøyningsformene).
"""

import sqlite3
from typing import Any
import numpy as np
from sqlite.queries import get_conn, get_paradigm, lookup_wordform

# Empiriske overgangsforhold (median f(mål_slot) / f(anker_slot)) beregnet fra
# 100 % entydige høyfrekvente paradigmer i Norsk Ordbank + nb_totals:
#
# For SUBSTANTIV (1=ent ub, 2=ent be, 3=fl ub, 4=fl be):
#   - Fra samme tallkategori (beste anker!):
#       ent_ub / ent_be ≈ 2.20
#       fl_ub  / fl_be  ≈ 3.30
#   - Fra hele resten av paradigmet (når 2 eller 3 øvrige former er entydige):
#       ent_ub / (ent_be + fl_ub + fl_be) ≈ 0.85 (eller vektet: 1.5*ent_be + 0.18*(fl_ub+fl_be))
#       ent_be / (ent_ub + fl_ub + fl_be) ≈ 0.28
#       fl_ub  / (ent_ub + ent_be + fl_be) -> bruker primært fl_be * 3.30 hvis fl_be er kjent!
#
# For VERB (1=inf, 2=pres, 3=passiv, 4=pret, 5=perf-part, 10=pres-part, 11=imp):
#   - Normalfordeling i kjerneverb (inf, pres, pret, perf-part):
#       inf ≈ 32 %, pres ≈ 24 %, pret ≈ 26 %, perf-part ≈ 18 %
#   - For sjeldnere verbkategorier mot kjerneformene:
#       passiv (3)    ≈ 0.08 * inf  (dvs. pres / passiv ≈ 2.6)
#       pres-part (10)≈ 0.015 * (inf + pres + pret)
#       imp (11)      ≈ 0.005 * (inf + pres + pret)  (imperativ er ekstremt lavfrekvent i bok/avis!)


def estimate_from_slots(
    bg: str,
    tslots: set[int],
    slot_info: dict[int, dict[str, Any]],
    unamb_total_in_paradigm: float,
) -> tuple[float, str]:
    """
    Kjerneregelen: anslår frekvensen til mål-kategoriene `tslots` ut fra resten av paradigmet.

    `slot_info` har én post per øvrig bøyningskategori med nøklene `freq`, `eff_freq`
    (nedvektet hvis formen deles med andre lemmaer), `min_lem_cnt` og `boy_tekst`.
    Brukes av `estimate_wordform_shares` og av valideringen i `sqlite/valider_dekomponering.py`.
    """
    est_freq = 0.0
    anchor_explanation = ""

    if bg == "substantiv":
        f1 = slot_info.get(1, {}).get("eff_freq", 0.0)
        f2 = slot_info.get(2, {}).get("eff_freq", 0.0)
        f3 = slot_info.get(3, {}).get("eff_freq", 0.0)
        f4 = slot_info.get(4, {}).get("eff_freq", 0.0)

        # Hvis paradigmet ikke har NOEN entydige former i det hele tatt (som 'et fiske' id=17310,
        # der alle former kolliderer med 'å fiske' eller 'en fisk'), nedskaler kraftig
        scale = 1.0 if unamb_total_in_paradigm > 0 else 0.05

        if 1 in tslots:  # Vi skal estimere ent ub (f.eks. 'en fisker', 'en hatt')
            est_freq = scale * (0.85 * f2 + 0.22 * (f3 + f4))
            anchor_explanation = f"0.85*ent_be({f2:,.0f}) + 0.22*fl({f3+f4:,.0f})"
        elif 2 in tslots:  # Vi skal estimere ent be (f.eks. 'landet')
            if f4 > 0 and slot_info.get(4, {}).get("min_lem_cnt", 99) == 1:
                est_freq = scale * (3.50 * f4 + 0.25 * f1)
                anchor_explanation = f"3.50*fl_be({f4:,.0f}) + 0.25*ent_ub({f1:,.0f})"
            else:
                est_freq = scale * (0.45 * f1 + 1.50 * f4)
                anchor_explanation = f"0.45*ent_ub({f1:,.0f}) + 1.50*fl_be({f4:,.0f})"
        elif 3 in tslots:  # Vi skal estimere fl ub (f.eks. 'fisker', 'kroner', 'dager', 'ønsker')
            # Hvis kun ent_be er 100% entydig (som 'fisken' for 'en fisk'), mens fl_be ('fiskene') har 2 lemmaer:
            f4_raw = slot_info.get(4, {}).get("freq", 0) if unamb_total_in_paradigm > 0 else f4
            if f4_raw > 0:
                est_freq = scale * (3.34 * f4_raw)
                anchor_explanation = f"3.34*fl_be({f4_raw:,.0f})"
            else:
                est_freq = scale * (0.22 * (f1 + f2))
                anchor_explanation = f"0.22*(ent_ub+ent_be)({f1+f2:,.0f})"
        elif 4 in tslots:  # Vi skal estimere fl be
            est_freq = scale * (0.30 * f3 if f3 > 0 else 0.08 * (f1 + f2))
            anchor_explanation = f"0.30*fl_ub({f3:,.0f})"

    elif bg == "verb, normal":
        # Finn beste entydige verb-ankere (inf=1, pres=2, pass=3, pret=4, perf=5)
        # Prioriter kjerneformer (1, 2, 4, 5) som har min_lem_cnt == 1
        unamb_core = {
            b: slot_info[b]["freq"]
            for b in (1, 2, 4, 5)
            if b in slot_info and slot_info[b]["min_lem_cnt"] == 1
        }
        all_core = {
            b: slot_info[b]["freq"] for b in (1, 2, 4, 5) if b in slot_info
        }
        ref_core = unamb_core if unamb_core else all_core

        # Normalvekter for kjerneverb: 1(inf)=0.32, 2(pres)=0.24, 4(pret)=0.26, 5(perf)=0.18
        w_map = {1: 0.32, 2: 0.24, 4: 0.26, 5: 0.18}
        target_w = sum(w_map.get(b, 0.005) for b in tslots if b in w_map)
        if 11 in tslots and target_w == 0:
            # Imperativ alene (f.eks. 'fisk!', 'hatt!', 'mann!', 'land!') er ~0.5% av verbets kjerne
            target_w = 0.005

        if ref_core and sum(w_map[b] for b in ref_core) > 0:
            denom_w = sum(w_map[b] for b in ref_core)
            sum_ref = sum(ref_core.values())
            # Hvis vi ikke hadde noen 100% entydige kjerneformer, men vi har en 100% entydig s-passiv (3):
            if not unamb_core and 3 in slot_info and slot_info[3]["min_lem_cnt"] == 1 and slot_info[3]["freq"] > 0:
                f_pass = slot_info[3]["freq"]
                est_freq = (target_w / 0.24) * (2.61 * f_pass)
                anchor_explanation = f"fra entydig s-passiv ({f_pass:,.0f})"
            else:
                est_freq = (target_w / denom_w) * sum_ref
                used_names = "+".join(slot_info[b]["boy_tekst"] for b in ref_core)
                anchor_explanation = f"fra verbkjerne {used_names} ({sum_ref:,.0f})"
        elif 3 in slot_info and slot_info[3]["freq"] > 0:
            f_pass = slot_info[3]["freq"]
            est_freq = (target_w / 0.24) * (2.61 * f_pass)
            anchor_explanation = f"fra s-passiv ({f_pass:,.0f})"

    else:
        # Ubøyelige ord / andre ordklasser uten andre former i paradigmet
        est_freq = 0.0
        anchor_explanation = "ingen andre bøyningsformer i paradigmet"

    return est_freq, anchor_explanation


# -----------------------------------------------------------------------------
# Log-regresjon lært på gullstandarden (standardmetoden fra 2026-11-20)
# -----------------------------------------------------------------------------
# Valideringen (rapport_dekomponering_validering.md) viste at de faste reglene over er skjeve
# (f.eks. ent be og pret ×2), mens log-regresjon av mål-kategorien på de entydige ankerkategoriene,
# lært på gullstandarden i samme korpus, er uten skjevhet og har lavest feil. Reglene brukes nå bare
# som reserve når mål-kategorien ikke finnes i gullstandarden (imperativ, s-passiv, adjektiv osv.)
# eller når kandidaten mangler entydige ankre.

GOLD_SLOTS = {"substantiv": (1, 2, 3, 4), "verb, normal": (1, 2, 4, 5), "adjektiv": (1, 2, 4)}
# Adjektiv: kategori 2 (fl) og 3 (be ent) har samme form (*store*) og behandles som én «e-form» (2).
SLOT_ALIAS = {"adjektiv": {3: 2}}
BOOK_PERIOD = (1950, 2020)
MIN_ANCHORS = 2  # minst to helt entydige ankerkategorier for å bruke log-regresjon
# Adjektivparadigmet har bare to mulige ankre (m/f og nøytrum). For *død* er «død» også et substantiv,
# så nøytrum (*dødt*) er eneste anker. Kryssvalidert feil med bare nøytrum: se sqlite/adjektiv_gold.py.
MIN_ANCHORS_BY_BG = {"adjektiv": 1}
# Sum ukappede anslag / observert utenfor dette intervallet gir advarsel i CLI-et. I valideringen
# (kunstige homografer, log-regresjon) lå medianen på 0,9–1,0.
CALIBRATION_OK = (0.5, 2.0)
_GOLD_CACHE: dict[tuple[str, str], list[dict[int, float]]] = {}
_MODEL_CACHE: dict[tuple, tuple[np.ndarray, int]] = {}


def corpus_freqs(words: list[str], corpus: str, conn: sqlite3.Connection) -> dict[str, float]:
    """Totalfrekvens per ordform: 'nb_totals' (hele NB) eller 'book' (bokkorpuset 1950–2020)."""
    words = list(dict.fromkeys(words))
    if corpus == "nb_totals":
        out = {w: 0.0 for w in words}
        for i in range(0, len(words), 500):
            chunk = words[i:i + 500]
            q = f"SELECT oppslag, freq FROM nb_totals WHERE oppslag IN ({','.join('?' * len(chunk))})"
            for w, f in conn.execute(q, chunk).fetchall():
                out[w] = float(f)
        return out
    if corpus == "book":
        from sqlite.ngram import fetch_ngram_dhlab

        series = fetch_ngram_dhlab(words, period=BOOK_PERIOD, batch_size=80)
        return {w: float(sum(series.get(w, {}).values())) for w in words}
    raise ValueError(f"ukjent korpus: {corpus}")


def gold_profiles(bg: str, corpus: str, conn: sqlite3.Connection) -> list[dict[int, float]]:
    """Kategorifrekvenser for gullstandarden (Sett A for verb, substantiv-gullstandarden), alle kategorier > 0."""
    key = (bg, corpus)
    if key not in _GOLD_CACHE:
        slots = GOLD_SLOTS[bg]
        if bg == "substantiv":
            from sqlite.substantivtyper import load_noun_forms, select_gold

            gold, _ = select_gold(load_noun_forms(conn))
        elif bg == "adjektiv":
            from sqlite.adjektiv_gold import select_adjective_gold

            gold = select_adjective_gold(conn)
        else:
            from sqlite.verbtyper import load_verbs, select_sets

            gold = select_sets(load_verbs(conn))[0]["580"]
        forms = [{s: list(d["forms"][s]) for s in slots} for d in gold]
        freqs = corpus_freqs([w for f in forms for s in slots for w in f[s]], corpus, conn)
        profiles = [{s: sum(freqs[w] for w in f[s]) for s in slots} for f in forms]
        _GOLD_CACHE[key] = [p for p in profiles if all(p[s] > 0 for s in slots)]
    return _GOLD_CACHE[key]


def fit_logreg(bg: str, target: int, anchors: tuple[int, ...], corpus: str, conn: sqlite3.Connection) -> tuple[np.ndarray, int]:
    """log f(target) = b0 + sum_a b_a * log f(a), lært på gullstandarden i `corpus`."""
    key = (bg, target, anchors, corpus)
    if key not in _MODEL_CACHE:
        gold = gold_profiles(bg, corpus, conn)
        X = np.array([[1.0] + [np.log(p[a]) for a in anchors] for p in gold])
        y = np.array([np.log(p[target]) for p in gold])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        _MODEL_CACHE[key] = (beta, len(gold))
    return _MODEL_CACHE[key]


def estimate_logreg(
    bg: str, tslots: set[int], slot_info: dict[int, dict[str, Any]], corpus: str, conn: sqlite3.Connection
) -> tuple[float, str] | None:
    """Anslag med log-regresjon, eller None hvis metoden ikke kan brukes (da brukes reglene)."""
    slots = GOLD_SLOTS.get(bg)
    if not slots:
        return None
    # Mål-kategorier utenfor gullstandarden (f.eks. adjektivisk partisipp som deler form med pret/perf-part)
    # ignoreres; finnes ingen mål-kategori i gullstandarden, brukes reglene.
    alias = SLOT_ALIAS.get(bg, {})
    tslots = {alias.get(t, t) for t in tslots}
    targets = sorted(t for t in tslots if t in slots)
    if not targets:
        return None
    # Ankre: kategorier der alle former er entydige. Med bare én slik kategori (eller med delvis
    # entydige kategorier) ble anslagene åpenbart gale (f.eks. «landet» 63 % verb), så da brukes reglene.
    anchors = tuple(
        s for s in slots
        if s not in tslots and s in slot_info and slot_info[s]["freq"] > 0
        and (slot_info[s]["max_lem_cnt"] == 1 or slot_info[s].get("min_ext_weight", 0.0) >= EXT_ANCHOR_MIN)
    )
    if len(anchors) < MIN_ANCHORS_BY_BG.get(bg, MIN_ANCHORS):
        return None
    est = 0.0
    for t in targets:
        beta, n = fit_logreg(bg, t, anchors, corpus, conn)
        est += float(np.exp(beta @ np.array([1.0] + [np.log(slot_info[a]["eff_freq"]) for a in anchors])))
    names = "+".join(slot_info[a]["boy_tekst"] for a in anchors)
    return est, f"log-regresjon fra {names} (gullstandard N={n}, {corpus})"


# Flertydighet regnes per leksem (grunnform + ordklasse), ikke per lemma_id (logg del 56). Homografe
# oppslag av samme leksem i Ordbanken (f.eks. to oppføringer for subst. *tro*, to for *far*) deler alle
# former; med antall_lemma_id ble de regnet som flertydige, slik at leksemet mistet ankrene sine.
LEXEME_LEVEL = True


def _amb_count(r) -> int:
    return r["antall_leksem_pos"] if LEXEME_LEVEL else r["antall_lemma_id"]


# Delte former i paradigmet (logg del 55). Tidligere ble en form som deles av n lemmaer, nedvektet med
# 1/n² for alle. Da straffer et sjeldent ordbokshomograf (subst. *ei grunne* i «grunnen») det vanlige
# leksemet like hardt som seg selv. Med SHARE_MODE = "masse" fordeles den delte formen i stedet på
# lemmaene etter hvor mye entydig bruk hvert av dem har (sum av formene med antall_lemma_id = 1), med
# et gulv på SHARE_FLOOR / n per lemma. Har ingen av lemmaene entydig bruk (f.eks. subst. *grunn* og
# *grunne*, som deler hele paradigmet), brukes 1/n² som før; da kan paradigmet ikke skille dem.
# Testet mot OBT-korpuset (rapport_dekomponering_obt.md §4.2): gulv 0,1 / 0,3 / 0,6 ga median 13,8 /
# 13,7 / 13,5 pp mot 13,9 uten; 0,6 er valgt.
SHARE_MODE = "masse"
SHARE_FLOOR = 0.6


# Valgfri ekstern kilde for hvordan delte former fordeles på lemmaer (logg del 56): en funksjon
# form -> {lemma_id: antall}. `set_anchor_split(obt_anchor_split())` bruker det OBT-taggede korpuset.
# Gjelder bare formene i resten av paradigmet (ankrene), aldri selve oppslagsordet.
ANCHOR_SPLIT = None
EXT_ANCHOR_MIN = 0.95  # OBT-andel som gjør en delt kategori brukbar som anker i log-regresjonen
ANCHOR_SPLIT_MIN_N = 5  # færre OBT-forekomster av formen enn dette: bruk entydig bruk (masse) i stedet


def set_anchor_split(provider) -> None:
    global ANCHOR_SPLIT
    ANCHOR_SPLIT = provider


def obt_anchor_split(db_path: str | None = None):
    """Leverandør for set_anchor_split: OBT-fordelingen av en form på lemma_id i korpus/obt_frekvenser.db."""
    from sqlite.korpus_profiler import DEFAULT_SHARED_DB, _ro_uri, form_split

    k = sqlite3.connect(_ro_uri(db_path or DEFAULT_SHARED_DB), uri=True)
    k.row_factory = sqlite3.Row
    cache: dict[str, dict[int, float]] = {}

    def split(form: str) -> dict[int, float]:
        if form not in cache:
            out: dict[int, float] = {}
            for r in form_split(k, form):
                if r["lemma_id"] is not None:
                    out[r["lemma_id"]] = out.get(r["lemma_id"], 0.0) + r["n"]
            cache[form] = out
        return cache[form]

    return split


def shared_form_weights(
    oppslag: str, paradigms: dict[int, list], corpus: str, conn: sqlite3.Connection
) -> dict[tuple[int, str], tuple[float, float]]:
    """{(lemma_id, form): (vekt med gulv, ren masseandel)} for delte former i kandidatparadigmene."""
    shared = sorted({r["oppslag"] for p in paradigms.values() for r in p
                     if _amb_count(r) > 1 and r["oppslag"] != oppslag})
    if not shared:
        return {}
    owners: dict[str, set[int]] = {}
    for i in range(0, len(shared), 500):
        chunk = shared[i:i + 500]
        q = f"SELECT DISTINCT oppslag, lemma_id FROM lemma_former WHERE oppslag IN ({','.join('?' * len(chunk))})"
        for w, lid in conn.execute(q, chunk).fetchall():
            owners.setdefault(w, set()).add(lid)
    lemmas = sorted({lid for s in owners.values() for lid in s})
    unamb_forms: dict[int, set[str]] = {}
    for i in range(0, len(lemmas), 500):
        chunk = lemmas[i:i + 500]
        q = (f"SELECT DISTINCT lf.lemma_id, lf.oppslag FROM lemma_former lf "
             f"JOIN ordform_flertydighet o ON o.oppslag = lf.oppslag "
             f"WHERE o.antall_lemma_id = 1 AND lf.lemma_id IN ({','.join('?' * len(chunk))})")
        for lid, w in conn.execute(q, chunk).fetchall():
            unamb_forms.setdefault(lid, set()).add(w)
    freqs = corpus_freqs(sorted({w for s in unamb_forms.values() for w in s}), corpus, conn)
    mass = {lid: sum(freqs.get(w, 0.0) for w in unamb_forms.get(lid, ())) for lid in lemmas}
    out: dict[tuple[int, str], tuple[float, float]] = {}
    lexeme = {}
    if ANCHOR_SPLIT is not None:
        q = f"SELECT lemma_id, MIN(grunnform), MIN(pos) FROM lemma_former WHERE lemma_id IN ({','.join('?' * len(lemmas))}) GROUP BY lemma_id"
        lexeme = {lid: (g, pos) for lid, g, pos in conn.execute(q, lemmas).fetchall()}
    pooled: dict[frozenset, dict[int, float]] = {}
    if ANCHOR_SPLIT is not None:
        # Sjeldne former arver fordelingen fra de andre formene med samme sett av lemmaer
        # (f.eks. *troa*, *troer* fra *troen*: subst. *tro* mot *troe*)
        for w, lids in owners.items():
            acc = pooled.setdefault(frozenset(lids), {})
            for lid, n in ANCHOR_SPLIT(w).items():
                if lid in lids:
                    acc[lid] = acc.get(lid, 0.0) + n
    for w, lids in owners.items():
        if ANCHOR_SPLIT is not None:
            ext = ANCHOR_SPLIT(w)
            n_ext = sum(ext.get(lid, 0.0) for lid in lids)
            if n_ext < ANCHOR_SPLIT_MIN_N:
                ext = pooled.get(frozenset(lids), {})
                n_ext = sum(ext.values())
            if n_ext >= ANCHOR_SPLIT_MIN_N:
                for lid in lids:
                    if lid in paradigms:
                        # Leksemnivå: homografe oppslag av samme leksem regnes sammen
                        same = [o for o in lids if lexeme.get(o) == lexeme.get(lid)]
                        sh = sum(ext.get(o, 0.0) for o in same) / n_ext
                        out[(lid, w)] = (sh, sh)
                continue
        tot = sum(mass[lid] for lid in lids)
        if tot <= 0:
            continue
        # Gulv: hvert lemma får minst SHARE_FLOOR / n av formen, så leksemer uten entydige former
        # (f.eks. subst. *tro*) ikke faller helt bort.
        n = len(lids)
        for lid in lids:
            if lid in paradigms:
                out[(lid, w)] = (SHARE_FLOOR / n + (1 - SHARE_FLOOR) * mass[lid] / tot, mass[lid] / tot)
    return out


def estimate_wordform_shares(
    oppslag: str,
    conn: sqlite3.Connection | None = None,
    corpus: str = "nb_totals",
    method: str = "logreg",
    share_mode: str | None = None,
) -> dict[str, Any]:
    """
    Tar en flertydig ordform `oppslag` og beregner forventet frekvens og prosentandel
    for hvert kandidat-lemma i Norsk Ordbank ut fra resten av kandidatens paradigme.

    corpus: 'nb_totals' (hele NB) eller 'book' (bokkorpuset 1950–2020); frekvensene og
            gullstandarden for log-regresjonen hentes fra samme korpus.
    method: 'logreg' (standard; faller tilbake på reglene der den ikke kan brukes) eller 'regler'.
    """
    share_mode = SHARE_MODE if share_mode is None else share_mode
    close = conn is None
    if conn is None:
        conn = get_conn()

    try:
        raw_candidates = lookup_wordform(oppslag, conn=conn)
        if not raw_candidates:
            obs = corpus_freqs([oppslag], corpus, conn)[oppslag]
            return {"oppslag": oppslag, "obs_freq": obs, "candidates": []}

        # Gruppér kandidater per lemma_id (siden ett lemma kan ha flere interne analyser for samme form,
        # f.eks. pret + perf-part for svake verb som 'landet' eller 'fisket')
        by_lemma: dict[int, dict[str, Any]] = {}
        for c in raw_candidates:
            lid = c["lemma_id"]
            if lid not in by_lemma:
                by_lemma[lid] = {
                    "lemma_id": lid,
                    "grunnform": c["grunnform"],
                    "pos": c["pos"],
                    "boy_gruppe": c["boy_gruppe"],
                    "target_slots": [],
                    "target_labels": [],
                }
            if c["boy_nummer"] not in by_lemma[lid]["target_slots"]:
                by_lemma[lid]["target_slots"].append(c["boy_nummer"])
                by_lemma[lid]["target_labels"].append(c["boy_tekst"] or c["pos"])

        paradigms = {lid: get_paradigm(lemma_id=lid, conn=conn) for lid in by_lemma}
        freqs = corpus_freqs([oppslag] + [r["oppslag"] for p in paradigms.values() for r in p], corpus, conn)
        shared_weight = (
            shared_form_weights(oppslag, paradigms, corpus, conn) if share_mode == "masse" else {}
        )
        obs_freq = freqs[oppslag]

        results = []
        for lid, meta in by_lemma.items():
            # Frekvens for alle ordformer i paradigmet som IKKE er selve oppslagsordet.
            # Vi skiller mellom helt entydige ankerformer (antall_lemma_id == 1) og delte former.
            slot_info: dict[int, dict[str, Any]] = {}
            unamb_total_in_paradigm = 0.0
            anchor_weights: dict[str, float] = {}  # form -> vekt brukt i anslaget (1 = entydig)
            seen: set[tuple[int, str]] = set()
            for r in paradigms[lid]:
                bnr = r["boy_nummer"]
                w = r["oppslag"]
                if w == oppslag or (bnr, w) in seen:
                    continue
                seen.add((bnr, w))
                fr = freqs[w]
                amb = _amb_count(r)
                is_unamb = amb == 1
                if is_unamb:
                    unamb_total_in_paradigm += fr
                # Hvis en form deles med andre lemmaer, nedvekter vi den hvis den ikke er entydig
                if is_unamb:
                    eff_fr = fr
                elif (lid, w) in shared_weight:
                    eff_fr = fr * shared_weight[(lid, w)][0]
                else:
                    eff_fr = fr / (amb ** 2)
                if bnr not in slot_info:
                    slot_info[bnr] = {
                        "boy_tekst": r["boy_tekst"],
                        "freq": 0,
                        "eff_freq": 0.0,
                        "min_lem_cnt": amb,
                        "max_lem_cnt": amb,
                        "forms": [],
                    }
                slot_info[bnr]["freq"] += fr
                slot_info[bnr]["eff_freq"] += eff_fr
                anchor_weights[w] = (eff_fr / fr) if fr > 0 else (1.0 if is_unamb else 0.0)
                # Vekt fra ekstern kilde (OBT): kategorien kan brukes som anker hvis alle formene
                # nesten bare tilhører dette leksemet
                ext_w = shared_weight[(lid, w)][0] if (lid, w) in shared_weight and ANCHOR_SPLIT is not None else (1.0 if is_unamb else 0.0)
                slot_info[bnr]["min_ext_weight"] = min(slot_info[bnr].get("min_ext_weight", 1.0), ext_w)
                slot_info[bnr]["min_lem_cnt"] = min(slot_info[bnr]["min_lem_cnt"], amb)
                slot_info[bnr]["max_lem_cnt"] = max(slot_info[bnr]["max_lem_cnt"], amb)
                slot_info[bnr]["forms"].append(f"{w} ({fr:,.0f}{'*' if is_unamb else ''})")

            tslots = set(meta["target_slots"])
            lr = estimate_logreg(meta["boy_gruppe"], tslots, slot_info, corpus, conn) if method == "logreg" else None
            if lr is not None:
                est_freq, anchor_explanation = lr
            else:
                est_freq, anchor_explanation = estimate_from_slots(
                    meta["boy_gruppe"], tslots, slot_info, unamb_total_in_paradigm
                )
                if method == "logreg":
                    anchor_explanation = "regler (reserve): " + anchor_explanation

            # En kandidat kan aldri bidra med flere forekomster av oppslagsordet enn obs_freq
            capped_est = min(est_freq, float(obs_freq)) if obs_freq > 0 else est_freq
            anchor_summary = ", ".join(
                f"{v['boy_tekst']}: {'/'.join(v['forms'])}"
                for k, v in sorted(slot_info.items())
                if k in (1, 2, 3, 4, 5)
            )
            results.append(
                {
                    "lemma_id": lid,
                    "grunnform": meta["grunnform"],
                    "pos": meta["pos"],
                    "boy_tekst": "/".join(meta["target_labels"]),
                    "raw_est": capped_est,
                    "uncapped_est": est_freq,
                    "anchor_weights": anchor_weights,
                    "method_used": "logreg" if lr is not None else "regler",
                    "anchor_explanation": anchor_explanation,
                    "paradigm_rest": anchor_summary,
                }
            )

        if LEXEME_LEVEL:
            # Homografe oppslag av samme leksem slås sammen: leksemet telles én gang (største anslag)
            by_lex: dict[tuple[str, str], dict[str, Any]] = {}
            for r in results:
                key = (r["grunnform"], r["pos"])
                if key not in by_lex or r["uncapped_est"] > by_lex[key]["uncapped_est"]:
                    lids = by_lex[key]["lemma_ids"] if key in by_lex else []
                    by_lex[key] = {**r, "lemma_ids": lids + [r["lemma_id"]]}
                else:
                    by_lex[key]["lemma_ids"].append(r["lemma_id"])
            results = list(by_lex.values())

        total_est = sum(r["raw_est"] for r in results)
        total_uncapped = sum(r["uncapped_est"] for r in results)
        for r in results:
            r["share"] = (r["raw_est"] / total_est) if total_est > 0 else 0.0
            r["norm_est"] = obs_freq * r["share"]

        results.sort(key=lambda x: -x["share"])
        return {
            "oppslag": oppslag,
            "obs_freq": obs_freq,
            "total_raw_est": total_est,
            "total_uncapped_est": total_uncapped,
            # Sum av ukappede anslag / observert. Langt unna 1 betyr at ankrene er atypiske for minst én
            # kandidat, og da er andelene lite pålitelige (f.eks. «døde»: 0,05, se rapport_verbtyper.md §7.2).
            "calibration": (total_uncapped / obs_freq) if obs_freq > 0 else None,
            "candidates": results,
        }
    finally:
        if close:
            conn.close()


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Dekomponer flertydige ordformer.")
    ap.add_argument("ord", nargs="*", default=["fisker", "hatt", "kroner", "dager", "ønsker", "møter", "viser", "landet"])
    ap.add_argument("--korpus", choices=["nb_totals", "book"], default="nb_totals")
    ap.add_argument("--metode", choices=["logreg", "regler"], default="logreg")
    args = ap.parse_args()
    conn = get_conn()
    for word in args.ord:
        res = estimate_wordform_shares(word, conn=conn, corpus=args.korpus, method=args.metode)
        print(f"\n======================================================================================")
        print(f"ORDFORM: «{word}» (Observert i {args.korpus}: {res['obs_freq']:,.0f} | Sum uavh. paradigme-est.: {res['total_raw_est']:,.0f})")
        print(f"======================================================================================")
        cal = res.get("calibration")
        if cal is not None and not (CALIBRATION_OK[0] <= cal <= CALIBRATION_OK[1]):
            print(f"  ADVARSEL: sum ukappede anslag / observert = {cal:.2f}. Ankrene passer dårlig; andelene er usikre.")
        for c in res["candidates"]:
            print(
                f"  -> {c['share']*100:5.1f}% ({c['norm_est']:10,.0f}) | "
                f"lemma_id={c['lemma_id']:6d} {c['grunnform']:8s} ({c['pos']:5s}: {c['boy_tekst']:14s}) | "
                f"Anker: {c['anchor_explanation']}"
            )
            if c["paradigm_rest"]:
                print(f"       Resten av paradigmet: {c['paradigm_rest']}")
