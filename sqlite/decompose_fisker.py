#!/usr/bin/env python3
"""
Dekomponering av den flertydige ordformen «fisker» ved hjelp av:
  1. Entydige holdepunkter i paradigmene for:
     - subst. «en fisker» (lemma_id=17348, der «fisker» er ent ub, og holdepunktene er fiskeren, fiskere, fiskerne)
     - subst. «en fisk»   (lemma_id=17301, der «fisker» er fl ub, og holdepunktene er fisk, fisken, fiskene)
     - verb   «å fiske»   (lemma_id=17307, der «fisker» er pres, og holdepunktene er fiske, fisket/fiska, fiskes, fiskende)
     - (samt subst. nøyt. «et fiske», lemma_id=17310)
  2. Empiriske normalprofiler fra 100 % entydige referanseparadigmer i Norsk Ordbank + NB-korpuset.
  3. Diakron dekomponering (1950–2020) over tid.
"""

import numpy as np
from sqlite.ngram import fetch_ngram_dhlab
from sqlite.queries import get_conn


def analyze_fisker_decomposition():
    conn = get_conn()

    # 0. Observerte totalfrekvenser i nb_totals for alle relevante former rundt «fisker»
    target_words = [
        "fisker",
        # subst. «en fisker» (id=17348)
        "fiskeren", "fiskere", "fiskerne",
        # subst. «en fisk» (id=17301)
        "fisk", "fisken", "fiskene",
        # verb «å fiske» (id=17307) & subst. «et fiske» (id=17310)
        "fiske", "fisket", "fiska", "fiskes", "fiskende", "fiskede", "fiskete",
    ]
    freqs = {}
    for w in target_words:
        row = conn.execute("SELECT freq FROM nb_totals WHERE oppslag = ?", (w,)).fetchone()
        freqs[w] = row["freq"] if row else 0

    obs_fisker = freqs["fisker"]
    print("==========================================================================")
    print(f"OBSERVERTE FREKVENSER I NB-KORPUSET (nb_totals) FOR «FISKER»-FAMILIEN")
    print("==========================================================================")
    print(f"  Flertydig målform : fisker   = {obs_fisker:10,d} (100.0 % som skal fordeles)\n")
    print(f"  1. Holdepunkter for subst. «en fisker» (lemma_id=17348, mangler ent ub «fisker»):")
    print(f"     - ent be : fiskeren = {freqs['fiskeren']:10,d} (100 % entydig)")
    print(f"     - fl ub  : fiskere  = {freqs['fiskere']:10,d} (100 % entydig)")
    print(f"     - fl be  : fiskerne = {freqs['fiskerne']:10,d} (100 % entydig)")
    rest_fisker_noun = freqs["fiskeren"] + freqs["fiskere"] + freqs["fiskerne"]
    print(f"     Sum øvrige former i paradigmet = {rest_fisker_noun:10,d}\n")

    print(f"  2. Holdepunkter for subst. «en fisk» (lemma_id=17301, mangler fl ub «fisker»):")
    print(f"     - ent ub : fisk     = {freqs['fisk']:10,d} (deles kun med marginal imp. av «fiske»)")
    print(f"     - ent be : fisken   = {freqs['fisken']:10,d} (100 % entydig)")
    print(f"     - fl be  : fiskene  = {freqs['fiskene']:10,d} (deles med sjeldent fl be av «et fiske»)")
    rest_fisk_noun = freqs["fisk"] + freqs["fisken"] + freqs["fiskene"]
    print(f"     Sum øvrige former i paradigmet = {rest_fisk_noun:10,d}\n")

    print(f"  3. Holdepunkter for verb «å fiske» (id=17307) + subst. «et fiske» (id=17310):")
    print(f"     - inf / subst ent ub      : fiske    = {freqs['fiske']:10,d}")
    print(f"     - pret+perf / subst ent be: fisket   = {freqs['fisket']:10,d} (+ fiska = {freqs['fiska']:,d})")
    print(f"     - passiv (100 % verb)     : fiskes   = {freqs['fiskes']:10,d} (100 % entydig verb)")
    print(f"     - pres-part (100 % verb)  : fiskende = {freqs['fiskende']:10,d} (100 % entydig verb)\n")

    # -------------------------------------------------------------------------
    # STEG 1: Estimer «en fisker» (ent ub) ut fra entydige personord på -er (-eren, -ere, -erne)
    # -------------------------------------------------------------------------
    rows_er = conn.execute("""
        SELECT lf.lemma_id, lf.grunnform, lf.boy_nummer, lf.oppslag,
               of.antall_lemma_id, COALESCE(nt.freq, 0) as freq
        FROM lemma_former lf
        JOIN ordform_flertydighet of ON lf.oppslag = of.oppslag
        LEFT JOIN nb_totals nt ON lf.oppslag = nt.oppslag
        WHERE lf.boy_gruppe = 'substantiv' AND lf.boy_nummer IN (1, 2, 3, 4)
          AND lf.grunnform LIKE '%er'
    """).fetchall()

    by_lid = {}
    for r in rows_er:
        by_lid.setdefault((r["lemma_id"], r["grunnform"]), []).append(r)

    er_nouns = []
    for (lid, gf), items in by_lid.items():
        if len({x["boy_nummer"] for x in items}) < 4 or any(x["antall_lemma_id"] > 1 for x in items):
            continue
        fl_ub_forms = [x["oppslag"] for x in items if x["boy_nummer"] == 3]
        if not any(f.endswith("ere") for f in fl_ub_forms):
            continue
        sf = {}
        for x in items:
            sf[x["boy_nummer"]] = sf.get(x["boy_nummer"], 0) + x["freq"]
        rest = sf[2] + sf[3] + sf[4]
        tot = sf[1] + rest
        if tot < 200000 or rest < 50000 or sf[2] < 5000:
            continue
        # For «en fisker» er flertall svært dominerende i resten: (fiskere+fiskerne)/rest = 93.3%
        plural_share_in_rest = (sf[3] + sf[4]) / rest
        er_nouns.append((gf, tot, sf[1] / tot, sf[1] / rest, sf[1] / sf[2], plural_share_in_rest, sf))

    # Se på flertallsdominerte person-/yrkesord på -er (der flertall > 75 % av resten, som hos fisker: 93.3 %)
    plural_er = [x for x in er_nouns if x[5] >= 0.75]
    med_ratio_er_rest = float(np.median([x[3] for x in plural_er]))
    q25_er_rest, q75_er_rest = np.percentile([x[3] for x in plural_er], [25, 75])
    # Regresjonsbasert / vektet prediksjon av ent_ub som funksjon av (ent_be, fl_ub, fl_be) i log- eller lineær skala:
    X_er = np.array([[x[6][2], x[6][3], x[6][4]] for x in plural_er], dtype=float)
    y_er = np.array([x[6][1] for x in plural_er], dtype=float)
    # Normaliser hver rad på rest-summen slik at alle ord veier likt
    X_er_norm = X_er / X_er.sum(axis=1, keepdims=True)
    y_er_norm = y_er / X_er.sum(axis=1)
    weights_er, _, _, _ = np.linalg.lstsq(X_er_norm, y_er_norm, rcond=None)
    fisker_rest_vec = np.array([freqs["fiskeren"], freqs["fiskere"], freqs["fiskerne"]], dtype=float)
    est_fisker_noun_ols = float(np.dot(weights_er, fisker_rest_vec))
    est_fisker_noun_med = float(med_ratio_er_rest * rest_fisker_noun)

    print("==========================================================================")
    print("STEG 1: ESTIMAT FOR SUBSTANTIVET «EN FISKER» (ent ub)")
    print("==========================================================================")
    print(f"  Referansegruppe: {len(plural_er)} helt entydige person-/yrkesord på -er med høy flertallsandel")
    print("  Eksempler fra referansegruppen:")
    for gf, tot, sh1, r_rest, r_be, pl_sh, sf in sorted(plural_er, key=lambda x: -x[1])[:8]:
        print(f"    {gf:16s}: ent_ub={sh1*100:5.1f}% av paradigmet | ent_ub/rest={r_rest:.3f} | (be={sf[2]:,}, fl_ub={sf[3]:,}, fl_be={sf[4]:,})")
    print(f"  -> Median (ent_ub / rest) = {med_ratio_er_rest:.3f} (kvartilbredde {q25_er_rest:.3f} – {q75_er_rest:.3f})")
    print(f"  -> Estimat (median-ratio) : {est_fisker_noun_med:10,.0f} forekomster av «en fisker»")
    print(f"  -> Estimat (profil-vektet): {est_fisker_noun_ols:10,.0f} forekomster av «en fisker»\n")

    # -------------------------------------------------------------------------
    # STEG 2: Estimer «en fisk» (fl ub = «flere fisker») ut fra (fisk, fisken, fiskene)
    # -------------------------------------------------------------------------
    # Merk at for «fisk» er entall ekstremt dominerende (fisk=5.78M, fisken=2.04M) mens fl be «fiskene» kun er 181,593!
    # Hva er forholdet (fl_ub / fl_be) for maskuline tellelige dyr/konkreter, eller når fl_be er liten relativt til ent_be?
    rows_m = conn.execute("""
        SELECT lf.lemma_id, lf.grunnform, lf.boy_nummer, lf.oppslag,
               of.antall_lemma_id, COALESCE(nt.freq, 0) as freq
        FROM lemma_former lf
        JOIN ordform_flertydighet of ON lf.oppslag = of.oppslag
        JOIN leddanalyse la ON lf.lemma_id = la.lemma_id
        LEFT JOIN nb_totals nt ON lf.oppslag = nt.oppslag
        WHERE lf.boy_gruppe = 'substantiv' AND lf.boy_nummer IN (1, 2, 3, 4)
          AND la.leddmarkert_bob = 'simplex'
    """).fetchall()
    by_lid_m = {}
    for r in rows_m:
        by_lid_m.setdefault((r["lemma_id"], r["grunnform"]), []).append(r)

    ent_dom_nouns = []
    for (lid, gf), items in by_lid_m.items():
        if len({x["boy_nummer"] for x in items}) < 4 or any(x["antall_lemma_id"] > 1 for x in items):
            continue
        # Sjekk ingen synkretisme
        slot_sets = {}
        for x in items:
            slot_sets.setdefault(x["boy_nummer"], set()).add(x["oppslag"])
        s_list = list(slot_sets.values())
        if any(s_list[i] & s_list[j] for i in range(len(s_list)) for j in range(i + 1, len(s_list))):
            continue
        sf = {}
        for x in items:
            sf[x["boy_nummer"]] = sf.get(x["boy_nummer"], 0) + x["freq"]
        tot = sum(sf.values())
        if tot < 300000 or sf[4] < 5000 or sf[2] < 5000:
            continue
        # Ser på substantiv der entall (1+2) er minst 70% (som for fisk) og fl_be / ent_be er mellom 0.03 og 0.25 (for fisk: 181k/2041k = 0.089)
        if 0.03 <= (sf[4] / sf[2]) <= 0.25 and (sf[1] + sf[2]) / tot >= 0.70:
            ent_dom_nouns.append((gf, tot, sf[3] / sf[4], sf[3] / (sf[1] + sf[2] + sf[4]), sf))

    # Sjekk også spesifikt dyre-/fiskeord (fugl, ulv, bjørn, hest, hund, katt, hval, ku, sau, gris, rev, kalv, ørn, krabbe, ørret, gjedde)
    animals = ["fugl", "ulv", "bjørn", "hest", "hund", "katt", "hval", "ku", "sau", "gris", "rev", "kalv", "ørn", "krabbe", "ørret", "gjedde"]
    animal_ratios = []
    for a in animals:
        a_rows = conn.execute("""
            SELECT lf.boy_nummer, COALESCE(nt.freq, 0) as freq
            FROM lemma_former lf
            LEFT JOIN nb_totals nt ON lf.oppslag = nt.oppslag
            WHERE lf.grunnform = ? AND lf.boy_gruppe = 'substantiv' AND lf.boy_nummer IN (1, 2, 3, 4)
        """, (a,)).fetchall()
        sf_a = {}
        for r in a_rows:
            sf_a[r["boy_nummer"]] = sf_a.get(r["boy_nummer"], 0) + r["freq"]
        if len(sf_a) == 4 and sf_a[4] > 0:
            animal_ratios.append((a, sf_a[3] / sf_a[4], sf_a))

    med_fl_ratio = float(np.median([x[2] for x in ent_dom_nouns]))
    med_animal_fl_ratio = float(np.median([x[1] for x in animal_ratios]))
    est_fisk_fl_ub = float(med_animal_fl_ratio * freqs["fiskene"])

    print("==========================================================================")
    print("STEG 2: ESTIMAT FOR SUBSTANTIVET «EN FISK» I UBESTEMT FLERTALL («flere fisker»)")
    print("==========================================================================")
    print(f"  Nøkkelobservasjon: Mens «fisk» (5,78M) og «fisken» (2,04M) er enorme,")
    print(f"  har bestemt flertall «fiskene» kun {freqs['fiskene']:,d} treff (fordi «fisk» oftest brukes kollektivt i entall!).")
    print(f"  Referansegruppe A: {len(animal_ratios)} dyre-/fiskeord:")
    for a, fl_ratio, sf_a in animal_ratios[:10]:
        print(f"    {a:16s}: fl_ub/fl_be = {fl_ratio:4.2f} | [ent_ub={sf_a[1]:,}, ent_be={sf_a[2]:,}, fl_ub={sf_a[3]:,}, fl_be={sf_a[4]:,}]")
    print(f"  -> Median (fl_ub / fl_be) for dyreord = {med_animal_fl_ratio:.2f} (alle entallsdominerte subst.: {med_fl_ratio:.2f})")
    print(f"  -> Estimat for «fisk» (fl ub) = {freqs['fiskene']:,d} * {med_animal_fl_ratio:.2f} = {est_fisk_fl_ub:10,.0f} forekomster\n")

    # -------------------------------------------------------------------------
    # STEG 3: Estimer verbet «å fiske» i presens («han/hun fisker»)
    # -------------------------------------------------------------------------
    act_verbs = ["jakte", "høste", "dyrke", "plukke", "fange", "slakte", "koke", "bake", "steke", "seile"]
    verb_pres_ratios = []
    print("==========================================================================")
    print("STEG 3: ESTIMAT FOR VERBET «Å FISKE» I PRESENS («fisker»)")
    print("==========================================================================")
    for v in act_verbs:
        v_rows = conn.execute("""
            SELECT lf.boy_nummer, lf.oppslag, COALESCE(nt.freq, 0) as freq
            FROM lemma_former lf
            LEFT JOIN nb_totals nt ON lf.oppslag = nt.oppslag
            WHERE lf.grunnform = ? AND lf.boy_gruppe = 'verb, normal' AND lf.boy_nummer IN (1, 2, 3, 4, 5)
        """, (v,)).fetchall()
        sf = {}
        seen_opp = set()
        for r in v_rows:
            bnr = r["boy_nummer"]
            if bnr in (4, 5):
                if r["oppslag"] in seen_opp:
                    continue
                seen_opp.add(r["oppslag"])
                sf[45] = sf.get(45, 0) + r["freq"]
            else:
                sf[bnr] = sf.get(bnr, 0) + r["freq"]
        if 1 in sf and 2 in sf and 45 in sf:
            tot_v = sf[1] + sf[2] + sf[45]
            pres_to_inf = sf[2] / sf[1]
            pres_to_pret = sf[2] / sf[45]
            pres_to_pass = sf[2] / sf[3] if sf.get(3, 0) > 0 else 0
            pres_share = sf[2] / tot_v
            verb_pres_ratios.append((v, pres_share, pres_to_inf, pres_to_pret, pres_to_pass, sf))
            print(f"    {v:12s}: pres={pres_share*100:5.1f}% | pres/inf={pres_to_inf:.2f} | pres/pret={pres_to_pret:.2f} | pres/passiv={pres_to_pass:.2f}")

    med_pres_share = float(np.median([x[1] for x in verb_pres_ratios]))
    med_pres_to_pass = float(np.median([x[4] for x in verb_pres_ratios if x[4] > 0]))
    est_verb_from_pass = float(med_pres_to_pass * freqs["fiskes"])
    print(f"  -> Median presens-andel for aktivitetsverb = {med_pres_share*100:.1f}%")
    print(f"  -> Median (pres / s-passiv) = {med_pres_to_pass:.2f} -> fra «fiskes» ({freqs['fiskes']:,d}) gir det ~{est_verb_from_pass:,.0f} presens-forekomster")

    # Samlet proporsjonal tilordning (uavhengige punktestimater + normalisert til 1,435,424)
    raw_1 = est_fisker_noun_ols
    raw_2 = est_fisk_fl_ub
    raw_3 = est_verb_from_pass
    raw_sum = raw_1 + raw_2 + raw_3
    norm_1 = obs_fisker * (raw_1 / raw_sum)
    norm_2 = obs_fisker * (raw_2 / raw_sum)
    norm_3 = obs_fisker * (raw_3 / raw_sum)

    print("\n==========================================================================")
    print("SAMLET DEKOMPONERING AV ORDFORMEN «FISKER» (1 435 424 FOREKOMSTER)")
    print("==========================================================================")
    print(f"  Observert total for ordformen «fisker» : {obs_fisker:10,d} (100.0 %)")
    print(f"  Sum av 3 uavhengige paradigme-estimater: {raw_sum:10,.0f} ({raw_sum/obs_fisker*100:5.1f}% av observert total!)")
    print("  ------------------------------------------------------------------------")
    print(f"  Paradigme / Lemma                      | Uavhengig est. | Normalisert andel")
    print("  ------------------------------------------------------------------------")
    print(f"  1. Subst. «en fisker» (ent ub, yrke)   | {raw_1:14,.0f} | {norm_1:10,.0f} ({norm_1/obs_fisker*100:5.1f} %)")
    print(f"  2. Subst. «en fisk»   (fl ub, dyr)     | {raw_2:14,.0f} | {norm_2:10,.0f} ({norm_2/obs_fisker*100:5.1f} %)")
    print(f"  3. Verb   «å fiske»   (presens)        | {raw_3:14,.0f} | {norm_3:10,.0f} ({norm_3/obs_fisker*100:5.1f} %)")
    print("  ------------------------------------------------------------------------")


if __name__ == "__main__":
    analyze_fisker_decomposition()
