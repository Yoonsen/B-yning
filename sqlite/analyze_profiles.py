#!/usr/bin/env python3
"""
Analyserer bøyningsprofiler og tidsstabilitet (1950–2020) for et utvalg verb og substantiv
ved hjelp av Norsk Ordbank (sqlite/ordbank.db) og NB DH-lab n-gram (sqlite/ngram_cache.db).
"""

from sqlite.ngram import compute_paradigm_profile, fetch_ngram_dhlab
from sqlite.queries import (
    NOUN_CORE_SLOTS,
    VERB_CORE_SLOTS,
    VERB_TENSE_SLOTS,
    get_noun_profile_forms,
    get_verb_profile_forms,
)

SAMPLE_VERBS = [
    "gå", "komme", "ta", "si", "fortelle", "svare", "stille", "legge", "sette",
    "vite", "spise", "forstå", "forklare", "høre", "kjøpe", "selge", "bygge",
    "snakke", "lese", "skrive", "tenke", "ligge", "finne", "gjøre", "ha",
    "fiske", "leve", "dø", "vinne", "tape",
]

SAMPLE_NOUNS = [
    "eple", "buss", "fisk", "fisker", "bil", "bok", "hus", "dag", "år",
    "mann", "kvinne", "barn", "by", "vei", "kirke", "konge", "sol", "krig",
]


def run_analysis(period: tuple[int, int] = (1950, 2020)):
    all_words = []
    for v in SAMPLE_VERBS:
        all_words.extend(r["oppslag"] for r in get_verb_profile_forms(grunnform=v, slots=VERB_CORE_SLOTS))
    for n in SAMPLE_NOUNS:
        all_words.extend(r["oppslag"] for r in get_noun_profile_forms(grunnform=n, slots=NOUN_CORE_SLOTS))

    fetch_ngram_dhlab(all_words, period=period, batch_size=80)

    print("=== 1. VERB: FORDELING MELLOM INF, PRES, PRET (1950–2020) ===")
    header = (
        f"{'Verb':10s} | {'Topp':5s} | {'Topp%':6s} | {'Stabil%':7s} | "
        f"{'inf':6s} {'pres':6s} {'pret':6s} | {'Std(topp)':9s} | {'1950s -> 2010s (topp)'}"
    )
    print(header)
    print("-" * len(header))

    verb_profiles = [
        compute_paradigm_profile(grunnform=v, pos="verb", slots=VERB_TENSE_SLOTS, period=period)
        for v in SAMPLE_VERBS
    ]
    verb_profiles.sort(key=lambda x: (x["dominant_slot"], -x["dominant_share"]))

    for p in verb_profiles:
        dom = p["dominant_slot"]
        pr = p["overall_proportions"]
        d50 = p["decade_profiles"].get("1950-tallet", {}).get(dom, 0.0)
        d10 = p["decade_profiles"].get("2010-tallet", {}).get(dom, 0.0)
        print(
            f"{p['grunnform']:10s} | {dom:5s} | {p['dominant_share']*100:5.1f}% | "
            f"{p['top_slot_consistency']*100:6.1f}% | "
            f"{pr.get('inf', 0)*100:5.1f}% {pr.get('pres', 0)*100:5.1f}% {pr.get('pret', 0)*100:5.1f}% | "
            f"{p['std_per_slot'].get(dom, 0)*100:7.1f}pp | {d50*100:5.1f}% -> {d10*100:5.1f}%"
        )

    print("\n=== 2. SUBSTANTIV: FORDELING MELLOM ENT UB, ENT BE, FL UB, FL BE (1950–2020) ===")
    header_n = (
        f"{'Substantiv':10s} | {'Topp':6s} | {'Topp%':6s} | {'Stabil%':7s} | "
        f"{'ent ub':6s} {'ent be':6s} {'fl ub':6s} {'fl be':6s} | {'Std(topp)':9s} | {'1950s -> 2010s (topp)'}"
    )
    print(header_n)
    print("-" * len(header_n))

    noun_profiles = [
        compute_paradigm_profile(grunnform=n, pos="subst", slots=NOUN_CORE_SLOTS, period=period)
        for n in SAMPLE_NOUNS
    ]
    noun_profiles.sort(key=lambda x: (x["dominant_slot"], -x["dominant_share"]))

    for p in noun_profiles:
        dom = p["dominant_slot"]
        pr = p["overall_proportions"]
        d50 = p["decade_profiles"].get("1950-tallet", {}).get(dom, 0.0)
        d10 = p["decade_profiles"].get("2010-tallet", {}).get(dom, 0.0)
        print(
            f"{p['grunnform']:10s} | {dom:6s} | {p['dominant_share']*100:5.1f}% | "
            f"{p['top_slot_consistency']*100:6.1f}% | "
            f"{pr.get('ent ub', 0)*100:5.1f}% {pr.get('ent be', 0)*100:5.1f}% "
            f"{pr.get('fl ub', 0)*100:5.1f}% {pr.get('fl be', 0)*100:5.1f}% | "
            f"{p['std_per_slot'].get(dom, 0)*100:7.1f}pp | {d50*100:5.1f}% -> {d10*100:5.1f}%"
        )


if __name__ == "__main__":
    run_analysis()
