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


def estimate_wordform_shares(
    oppslag: str,
    conn: sqlite3.Connection | None = None,
) -> dict[str, Any]:
    """
    Tar en flertydig ordform `oppslag` og beregner forventet frekvens og prosentandel
    for hvert kandidat-lemma i Norsk Ordbank ut fra resten av kandidatens paradigme.
    """
    close = conn is None
    if conn is None:
        conn = get_conn()

    try:
        obs_row = conn.execute(
            "SELECT freq FROM nb_totals WHERE oppslag = ?", (oppslag,)
        ).fetchone()
        obs_freq = int(obs_row["freq"]) if obs_row else 0

        raw_candidates = lookup_wordform(oppslag, conn=conn)
        if not raw_candidates:
            return {"oppslag": oppslag, "obs_freq": obs_freq, "candidates": []}

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
                    "target_ labels": [],
                }
            if c["boy_nummer"] not in by_lemma[lid]["target_slots"]:
                by_lemma[lid]["target_slots"].append(c["boy_nummer"])
                by_lemma[lid]["target_ labels"].append(c["boy_tekst"] or c["pos"])

        results = []
        for lid, meta in by_lemma.items():
            paradigm = get_paradigm(lemma_id=lid, conn=conn)
            # Hent frekvens for alle ordformer i dette paradigmet som IKKE er selve oppslagsordet.
            # Vi skiller mellom helt entydige ankerformer (antall_lemma_id == 1) og delte former.
            slot_info: dict[int, dict[str, Any]] = {}
            unamb_total_in_paradigm = 0
            for r in paradigm:
                bnr = r["boy_nummer"]
                w = r["oppslag"]
                if w == oppslag:
                    continue
                fr_row = conn.execute(
                    "SELECT freq FROM nb_totals WHERE oppslag = ?", (w,)
                ).fetchone()
                fr = int(fr_row["freq"]) if fr_row else 0
                is_unamb = r["antall_lemma_id"] == 1
                if is_unamb:
                    unamb_total_in_paradigm += fr
                # Hvis en form deles med andre lemmaer, nedvekter vi den hvis den ikke er entydig
                eff_fr = fr if is_unamb else (fr / (r["antall_lemma_id"] ** 2))
                if bnr not in slot_info:
                    slot_info[bnr] = {
                        "boy_tekst": r["boy_tekst"],
                        "freq": 0,
                        "eff_freq": 0.0,
                        "min_lem_cnt": r["antall_lemma_id"],
                        "forms": [],
                    }
                slot_info[bnr]["freq"] += fr
                slot_info[bnr]["eff_freq"] += eff_fr
                slot_info[bnr]["min_lem_cnt"] = min(
                    slot_info[bnr]["min_lem_cnt"], r["antall_lemma_id"]
                )
                slot_info[bnr]["forms"].append(
                    f"{w} ({fr:,d}{'*' if is_unamb else ''})"
                )

            bg = meta["boy_gruppe"]
            tslots = set(meta["target_slots"])
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
                        anchor_explanation = f"fra entydig s-passiv ({f_pass:,d})"
                    else:
                        est_freq = (target_w / denom_w) * sum_ref
                        used_names = "+".join(slot_info[b]["boy_tekst"] for b in ref_core)
                        anchor_explanation = f"fra verbkjerne {used_names} ({sum_ref:,d})"
                elif 3 in slot_info and slot_info[3]["freq"] > 0:
                    f_pass = slot_info[3]["freq"]
                    est_freq = (target_w / 0.24) * (2.61 * f_pass)
                    anchor_explanation = f"fra s-passiv ({f_pass:,d})"

            else:
                # Ubøyelige ord / andre ordklasser uten andre former i paradigmet
                est_freq = 0.0
                anchor_explanation = "ingen andre bøyningsformer i paradigmet"

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
                    "boy_tekst": "/".join(meta["target_ labels"]),
                    "raw_est": capped_est,
                    "uncapped_est": est_freq,
                    "anchor_explanation": anchor_explanation,
                    "paradigm_rest": anchor_summary,
                }
            )

        total_est = sum(r["raw_est"] for r in results)
        for r in results:
            r["share"] = (r["raw_est"] / total_est) if total_est > 0 else 0.0
            r["norm_est"] = obs_freq * r["share"]

        results.sort(key=lambda x: -x["share"])
        return {
            "oppslag": oppslag,
            "obs_freq": obs_freq,
            "total_raw_est": total_est,
            "candidates": results,
        }
    finally:
        if close:
            conn.close()


if __name__ == "__main__":
    conn = get_conn()
    for word in ["fisker", "hatt", "kroner", "dager", "ønsker", "møter", "viser", "landet"]:
        res = estimate_wordform_shares(word, conn=conn)
        print(f"\n======================================================================================")
        print(f"ORDFORM: «{word}» (Observert i NB: {res['obs_freq']:,d} | Sum uavh. paradigme-est.: {res['total_raw_est']:,.0f})")
        print(f"======================================================================================")
        for c in res["candidates"]:
            print(
                f"  -> {c['share']*100:5.1f}% ({c['norm_est']:10,.0f}) | "
                f"lemma_id={c['lemma_id']:6d} {c['grunnform']:8s} ({c['pos']:5s}: {c['boy_tekst']:14s}) | "
                f"Anker: {c['anchor_explanation']}"
            )
            if c["paradigm_rest"]:
                print(f"       Resten av paradigmet: {c['paradigm_rest']}")
