"""
Undersøker hvordan bøyningsparadigmer realiseres i enkeltbøker (dokumentnivå / dispersjon)
via Nasjonalbibliotekets DH-lab API (/dhlab/build_corpus og /dhlab/frequencies).

Spørsmål som besvares:
1. Paradigmemetning i enkeltbøker: Hvor ofte har en bok kun 1, 2, 3 eller alle bøyningsformer
   av et leksem når leksemet først forekommer i boka?
2. Hvilken del av paradigmet blir med? Følger dokumentfrekvensen (andel bøker) og
   «overlevelsen» i enkeltbøker (når kun 1 eller 2 former er med) leksemets globale
   bøyningsprofil (1. > 2. > 3.)?
3. Sjangerforskjeller: Hvordan skiller skjønnlitteratur og faglitteratur seg på enkeltboknivå?
"""

import json
import urllib.request
from collections import defaultdict
from sqlite.queries import get_conn

BUILD_CORPUS_URL = "https://api.nb.no/dhlab/build_corpus"
FREQUENCIES_URL = "https://api.nb.no/dhlab/frequencies"


def fetch_book_corpus(
    from_year: int = 1980,
    to_year: int = 2020,
    limit: int = 300,
    literaryform: str | None = None,
) -> list[dict]:
    """Henter et tilfeldig utvalg bokmal-bøker fra DH-lab API."""
    payload = {
        "doctype": "digibok",
        "from_year": from_year,
        "to_year": to_year,
        "lang": "nob",
        "limit": limit,
    }
    if literaryform:
        payload["literaryform"] = literaryform

    req = urllib.request.Request(
        BUILD_CORPUS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    # Kolonne-orientert JSON -> liste av dicts
    keys = list(data.keys())
    if not keys:
        return []
    n_rows = len(data[keys[0]])
    rows = []
    for i in range(n_rows):
        row = {k: data[k][str(i)] for k in keys if str(i) in data[k]}
        rows.append(row)
    return rows


def fetch_book_frequencies(
    urns: list[str], words: list[str], urn_chunk_size: int = 200, word_chunk_size: int = 60
) -> list[list]:
    """
    Henter frekvenser per bok for en liste med URN-er og ordformer.
    Returnerer rader på formen [dhlabid, word, count_in_book, total_words_in_book].
    Merk: DH-lab API krever parameteren "cutoff": 1 i payloaden.
    """
    all_rows = []
    urns = [u for u in urns if u and isinstance(u, str)]
    for i in range(0, len(urns), urn_chunk_size):
        urn_chunk = urns[i : i + urn_chunk_size]
        for j in range(0, len(words), word_chunk_size):
            word_chunk = words[j : j + word_chunk_size]
            payload = {"urns": urns_chunk if False else urn_chunk, "words": word_chunk, "cutoff": 1}
            req = urllib.request.Request(
                FREQUENCIES_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    rows = json.loads(resp.read().decode("utf-8"))
                    if rows:
                        all_rows.extend(rows)
            except Exception as e:
                print(f"Advarsel ved chunk urn[{i}:{i+urn_chunk_size}], words[{j}:{j+word_chunk_size}]: {e}")
    return all_rows


# Representative, tilnærmet entydige verb fra alle de 6 undertypene i rapport_verbtyper.md
REPRESENTATIVE_VERBS = [
    # 1a: inf > pret > pres
    ("spise", "inf>pret>pres", {"inf": ["spise"], "pres": ["spiser"], "pret": ["spiste"]}),
    ("lese", "inf>pret>pres", {"inf": ["lese"], "pres": ["leser"], "pret": ["leste"]}),
    ("ta", "inf>pret>pres", {"inf": ["ta"], "pres": ["tar"], "pret": ["tok"]}),
    ("kjøpe", "inf>pret>pres", {"inf": ["kjøpe"], "pres": ["kjøper"], "pret": ["kjøpte"]}),
    # 1b: inf > pres > pret
    ("forstå", "inf>pres>pret", {"inf": ["forstå"], "pres": ["forstår"], "pret": ["forstod", "forsto"]}),
    ("forklare", "inf>pres>pret", {"inf": ["forklare"], "pres": ["forklarer"], "pret": ["forklarte"]}),
    ("skape", "inf>pres>pret", {"inf": ["skape"], "pres": ["skaper"], "pret": ["skapte"]}),
    # 2a: pret > inf > pres
    ("vinne", "pret>inf>pres", {"inf": ["vinne"], "pres": ["vinner"], "pret": ["vant"]}),
    ("legge", "pret>inf>pres", {"inf": ["legge"], "pres": ["legger"], "pret": ["la"]}),
    ("si", "pret>inf>pres", {"inf": ["si"], "pres": ["sier"], "pret": ["sa"]}),
    # 2b: pret > pres > inf
    ("dø", "pret>pres>inf", {"inf": ["dø"], "pres": ["dør"], "pret": ["døde"]}),
    ("svare", "pret>pres>inf", {"inf": ["svare"], "pres": ["svarer"], "pret": ["svarte"]}),
    ("komme", "pret>pres>inf", {"inf": ["komme"], "pres": ["kommer"], "pret": ["kom"]}),
    ("forsvinne", "pret>pres>inf", {"inf": ["forsvinne"], "pres": ["forsvinner"], "pret": ["forsvant"]}),
    # 3a: pres > inf > pret
    ("bety", "pres>inf>pret", {"inf": ["bety"], "pres": ["betyr"], "pret": ["betydde"]}),
    ("fungere", "pres>inf>pret", {"inf": ["fungere"], "pres": ["fungerer"], "pret": ["fungerte"]}),
    ("gjelde", "pres>inf>pret", {"inf": ["gjelde"], "pres": ["gjelder"], "pret": ["gjaldt"]}),
    # 3b: pres > pret > inf
    ("ha", "pres>pret>inf", {"inf": ["ha"], "pres": ["har"], "pret": ["hadde"]}),
    ("vite", "pres>pret>inf", {"inf": ["vite"], "pres": ["vet", "veit"], "pret": ["visste"]}),
    ("ligge", "pres>pret>inf", {"inf": ["ligge"], "pres": ["ligger"], "pret": ["lå"]}),
]

# Representative substantiv med ulike globale toppformer (ent ub, ent be, fl ub)
REPRESENTATIVE_NOUNS = [
    # ent ub > ent be / fl ub
    ("dag", "ent_ub-topp", {"ent_ub": ["dag"], "ent_be": ["dagen"], "fl_ub": ["dager"], "fl_be": ["dagene"]}),
    ("år", "ent_ub-topp", {"ent_ub": ["år"], "ent_be": ["året"], "fl_ub": ["år"], "fl_be": ["årene", "åra"]}),
    ("bok", "ent_ub-topp", {"ent_ub": ["bok"], "ent_be": ["boka", "boken"], "fl_ub": ["bøker"], "fl_be": ["bøkene"]}),
    ("eple", "ent_ub-topp", {"ent_ub": ["eple"], "ent_be": ["eplet"], "fl_ub": ["epler"], "fl_be": ["eplene", "epla"]}),
    ("bil", "ent_ub-topp", {"ent_ub": ["bil"], "ent_be": ["bilen"], "fl_ub": ["biler"], "fl_be": ["bilene"]}),
    # ent be > ent ub
    ("buss", "ent_be-topp", {"ent_ub": ["buss"], "ent_be": ["bussen"], "fl_ub": ["busser"], "fl_be": ["bussene"]}),
    ("kirke", "ent_be-topp", {"ent_ub": ["kirke"], "ent_be": ["kirken", "kirka"], "fl_ub": ["kirker"], "fl_be": ["kirkene"]}),
    ("konge", "ent_be-topp", {"ent_ub": ["konge"], "ent_be": ["kongen"], "fl_ub": ["konger"], "fl_be": ["kongene"]}),
    ("sol", "ent_be-topp", {"ent_ub": ["sol"], "ent_be": ["solen", "sola"], "fl_ub": ["soler"], "fl_be": ["solene"]}),
    ("politi", "ent_be-topp", {"ent_ub": ["politi"], "ent_be": ["politiet"], "fl_ub": ["politier"], "fl_be": ["politiene"]}),
    # fl ub-sterke substantiv
    ("kvinne", "fl_ub-sterk", {"ent_ub": ["kvinne"], "ent_be": ["kvinnen", "kvinna"], "fl_ub": ["kvinner"], "fl_be": ["kvinnene"]}),
    ("forelder", "fl_ub-topp", {"ent_ub": ["forelder"], "ent_be": ["forelderen"], "fl_ub": ["foreldre"], "fl_be": ["foreldrene"]}),
    ("politiker", "fl_ub-topp", {"ent_ub": ["politiker"], "ent_be": ["politikeren"], "fl_ub": ["politikere"], "fl_be": ["politikerne"]}),
]


def analyze_dispersion(books: list[dict], freq_rows: list[list], items: list[tuple], slot_names: list[str]):
    """
    Analyserer per-bok dekning av paradigmer.
    Returnerer detaljert statistikk per leksem og aggregert etter antall forekomster i boka.
    """
    book_meta = {int(b["dhlabid"]): b for b in books}
    # Map: dhlabid -> word -> count
    book_word_counts = defaultdict(lambda: defaultdict(int))
    for dhlabid, word, count, _total in freq_rows:
        book_word_counts[int(dhlabid)][word] += int(count)

    results = []
    # Aggregert: gitt at leksemet har totalfrekvens k i en bok, hvor mange slots er realisert?
    saturation_by_freq_bin = defaultdict(lambda: defaultdict(int))
    # Når kun 1 slot er realisert i en bok: er det global #1, #2, #3 (eller #4)?
    single_slot_match = defaultdict(int)
    # Når kun 2 slots er realisert i en bok: er det global {#1, #2}?
    two_slot_match = defaultdict(int)

    for lemma, subtype, slots_dict in items:
        # Beregn per-bok counts per slot
        book_slot_counts = {}
        global_slot_totals = {s: 0 for s in slot_names}
        doc_freq_per_slot = {s: 0 for s in slot_names}
        single_slot_winner_counts = {s: 0 for s in slot_names}

        books_with_lemma = 0
        active_slots_hist = defaultdict(int)  # n_active_slots -> antall bøker

        # Sjanger-fordeling (Skjønnlitteratur vs Fag)
        genre_slot_totals = {
            "Skjønnlitteratur": {s: 0 for s in slot_names},
            "Faglitteratur": {s: 0 for s in slot_names},
        }

        for dhlabid, meta in book_meta.items():
            w_counts = book_word_counts.get(dhlabid, {})
            s_counts = {}
            for s in slot_names:
                c = sum(w_counts.get(w, 0) for w in slots_dict[s])
                s_counts[s] = c
                global_slot_totals[s] += c
                if c > 0:
                    doc_freq_per_slot[s] += 1

            total_c = sum(s_counts.values())
            if total_c > 0:
                books_with_lemma += 1
                active_slots = [s for s in slot_names if s_counts[s] > 0]
                n_active = len(active_slots)
                active_slots_hist[n_active] += 1

                # Frekvens-bin i boka
                if total_c == 1:
                    fbin = "1 forekomst"
                elif total_c == 2:
                    fbin = "2 forekomster"
                elif 3 <= total_c <= 5:
                    fbin = "3-5 forekomster"
                elif 6 <= total_c <= 15:
                    fbin = "6-15 forekomster"
                else:
                    fbin = "16+ forekomster"
                saturation_by_freq_bin[fbin][n_active] += 1

                if n_active == 1:
                    single_slot_winner_counts[active_slots[0]] += 1

                book_slot_counts[dhlabid] = (total_c, s_counts, active_slots)

                litform = meta.get("literaryform", "Ukjent")
                if litform in genre_slot_totals:
                    for s in slot_names:
                        genre_slot_totals[litform][s] += s_counts[s]

        # Global rangering i dette korpuset (og/eller teoretisk)
        sorted_global_slots = sorted(slot_names, key=lambda s: global_slot_totals[s], reverse=True)
        sorted_df_slots = sorted(slot_names, key=lambda s: doc_freq_per_slot[s], reverse=True)

        # Sjekk hva som skjer når en bok kun har 1 eller 2 former av dette leksemet
        for dhlabid, (total_c, s_counts, active_slots) in book_slot_counts.items():
            if len(active_slots) == 1:
                only_s = active_slots[0]
                rank_idx = sorted_global_slots.index(only_s) + 1
                single_slot_match[rank_idx] += 1
            elif len(active_slots) == 2:
                top2_set = set(sorted_global_slots[:2])
                if set(active_slots) == top2_set:
                    two_slot_match["top_1_and_2"] += 1
                elif sorted_global_slots[0] in active_slots:
                    two_slot_match["includes_top_1"] += 1
                else:
                    two_slot_match["neither_top_1"] += 1

        total_tokens = sum(global_slot_totals.values()) or 1
        results.append({
            "lemma": lemma,
            "subtype": subtype,
            "books_with_lemma": books_with_lemma,
            "total_books": len(book_meta),
            "total_tokens": sum(global_slot_totals.values()),
            "global_shares": {s: global_slot_totals[s] / total_tokens for s in slot_names},
            "doc_freqs": {s: doc_freq_per_slot[s] / max(books_with_lemma, 1) for s in slot_names},
            "active_slots_hist": dict(active_slots_hist),
            "single_slot_winner_counts": single_slot_winner_counts,
            "sorted_global_slots": sorted_global_slots,
            "sorted_df_slots": sorted_df_slots,
            "genre_slot_totals": genre_slot_totals,
        })

    return {
        "items": results,
        "saturation_by_freq_bin": dict(saturation_by_freq_bin),
        "single_slot_match": dict(single_slot_match),
        "two_slot_match": dict(two_slot_match),
    }


def main():
    print("Henter bokkorpus fra Nasjonalbiblioteket (200 skjønnlitteratur + 200 faglitteratur, 1980-2020)...")
    fict_books = fetch_book_corpus(1980, 2020, limit=200, literaryform="Skjønnlitteratur")
    nonfict_books = fetch_book_corpus(1980, 2020, limit=200, literaryform="Faglitteratur")
    # Dedupliser på dhlabid
    books_by_id = {}
    for b in fict_books + nonfict_books:
        books_by_id[int(b["dhlabid"])] = b
    books = list(books_by_id.values())
    urns = [b["urn"] for b in books]
    print(f"Hentet {len(books)} unike bøker ({len(fict_books)} skjønnlitt, {len(nonfict_books)} faglitt).")

    # Samle alle ordformer vi trenger å spørre om
    all_words = set()
    for _, _, sdict in REPRESENTATIVE_VERBS:
        for wlist in sdict.values():
            all_words.update(wlist)
    for _, _, sdict in REPRESENTATIVE_NOUNS:
        for wlist in sdict.values():
            all_words.update(wlist)

    all_words_list = sorted(all_words)
    print(f"Henter dokumentfrekvenser for {len(all_words_list)} ordformer på tvers av {len(urns)} bøker...")
    freq_rows = fetch_book_frequencies(urns, all_words_list, urn_chunk_size=200, word_chunk_size=120)
    print(f"Mottok {len(freq_rows)} (bok, ordform)-rader.")

    verb_stats = analyze_dispersion(books, freq_rows, REPRESENTATIVE_VERBS, ["inf", "pres", "pret"])
    # For substantiv bruker vi 4 slots (unntatt 'år' der ent_ub == fl_ub, vi sjekker de 12 andre med 4 distinkte former)
    distinct_nouns = [n for n in REPRESENTATIVE_NOUNS if n[0] != "år"]
    noun_stats = analyze_dispersion(books, freq_rows, distinct_nouns, ["ent_ub", "ent_be", "fl_ub", "fl_be"])

    print("\n" + "=" * 95)
    print("1. PARADIGMEMETNING I ENKELTBØKER: HVOR MANGE FORMER ER MED NÅR ORDET BRUKES?")
    print("=" * 95)
    print("\nVERB (3 former: inf, pres, pret) — fordelt etter hvor mange ganger verbet forekommer i boka:")
    for fbin in ["1 forekomst", "2 forekomster", "3-5 forekomster", "6-15 forekomster", "16+ forekomster"]:
        hist = verb_stats["saturation_by_freq_bin"].get(fbin, {})
        tot = sum(hist.values()) or 1
        s1 = 100 * hist.get(1, 0) / tot
        s2 = 100 * hist.get(2, 0) / tot
        s3 = 100 * hist.get(3, 0) / tot
        print(f"  {fbin:<17} (N={tot:>4} bok-verb-par): Kun 1 form: {s1:>5.1f}% | 2 former: {s2:>5.1f}% | Alle 3 former: {s3:>5.1f}%")

    tot_v_1 = sum(verb_stats["single_slot_match"].values()) or 1
    print(f"\nNår en bok KUN har 1 form av et verb (N={tot_v_1} tilfeller):")
    for r in [1, 2, 3]:
        c = verb_stats["single_slot_match"].get(r, 0)
        print(f"  Det er verbets globale #{r}-form i {c:>4} bøker ({100*c/tot_v_1:>5.1f}%)")

    tot_v_2 = sum(verb_stats["two_slot_match"].values()) or 1
    print(f"\nNår en bok har NØYAKTIG 2 former av et verb (N={tot_v_2} tilfeller):")
    print(f"  Det er verbets globale #1 + #2-par i {verb_stats['two_slot_match'].get('top_1_and_2', 0):>4} bøker ({100*verb_stats['two_slot_match'].get('top_1_and_2', 0)/tot_v_2:>5.1f}%)")
    print(f"  Det inkluderer global #1 (#1 + #3) i {verb_stats['two_slot_match'].get('includes_top_1', 0):>4} bøker ({100*verb_stats['two_slot_match'].get('includes_top_1', 0)/tot_v_2:>5.1f}%)")
    print(f"  Det mangler global #1 (#2 + #3)    i {verb_stats['two_slot_match'].get('neither_top_1', 0):>4} bøker ({100*verb_stats['two_slot_match'].get('neither_top_1', 0)/tot_v_2:>5.1f}%)")

    print("\n" + "-" * 95)
    print("SUBSTANTIV (4 former: ent_ub, ent_be, fl_ub, fl_be) — etter antall forekomster i boka:")
    for fbin in ["1 forekomst", "2 forekomster", "3-5 forekomster", "6-15 forekomster", "16+ forekomster"]:
        hist = noun_stats["saturation_by_freq_bin"].get(fbin, {})
        tot = sum(hist.values()) or 1
        s1 = 100 * hist.get(1, 0) / tot
        s2 = 100 * hist.get(2, 0) / tot
        s3 = 100 * hist.get(3, 0) / tot
        s4 = 100 * hist.get(4, 0) / tot
        print(f"  {fbin:<17} (N={tot:>4} bok-subst-par): 1 form: {s1:>5.1f}% | 2 former: {s2:>5.1f}% | 3 former: {s3:>5.1f}% | Alle 4: {s4:>5.1f}%")

    tot_n_1 = sum(noun_stats["single_slot_match"].values()) or 1
    print(f"\nNår en bok KUN har 1 form av et substantiv (N={tot_n_1} tilfeller):")
    for r in [1, 2, 3, 4]:
        c = noun_stats["single_slot_match"].get(r, 0)
        print(f"  Det er substantivets globale #{r}-form i {c:>4} bøker ({100*c/tot_n_1:>5.1f}%)")

    print("\n" + "=" * 95)
    print("2. DETALJERT PER LEKSEM: HVILKEN FORM OVERLEVER I ENKELTBØKER?")
    print("=" * 95)
    print(f"{'Verb':<11} {'Undertype':<15} {'Bøker':>5} | {'Andel bøker med 1/2/3 former':<26} | {'Dokumentfrekvens (DF%: inf / pres / pret)':<38} | {'Vinner ved 1 form'}")
    print("-" * 125)
    for item in verb_stats["items"]:
        b_tot = item["books_with_lemma"] or 1
        h = item["active_slots_hist"]
        p1, p2, p3 = 100*h.get(1,0)/b_tot, 100*h.get(2,0)/b_tot, 100*h.get(3,0)/b_tot
        df = item["doc_freqs"]
        sw = item["single_slot_winner_counts"]
        sw_tot = sum(sw.values()) or 1
        top_sw = max(sw.items(), key=lambda x: x[1])
        print(
            f"{item['lemma']:<11} {item['subtype']:<15} {item['books_with_lemma']:>5} | "
            f"1:{p1:>4.0f}%  2:{p2:>4.0f}%  3:{p3:>4.0f}%    | "
            f"inf:{100*df['inf']:>4.0f}%  pres:{100*df['pres']:>4.0f}%  pret:{100*df['pret']:>4.0f}%       | "
            f"{top_sw[0]} ({100*top_sw[1]/sw_tot:.0f}% av {sw_tot})"
        )

    print("\n" + "-" * 125)
    print(f"{'Substantiv':<11} {'Profiltype':<15} {'Bøker':>5} | {'Andel bøker (1/2/3/4 former)':<28} | {'DF%: ent_ub / ent_be / fl_ub / fl_be':<40} | {'Vinner ved 1 form'}")
    print("-" * 125)
    for item in noun_stats["items"]:
        b_tot = item["books_with_lemma"] or 1
        h = item["active_slots_hist"]
        p1, p2, p3, p4 = 100*h.get(1,0)/b_tot, 100*h.get(2,0)/b_tot, 100*h.get(3,0)/b_tot, 100*h.get(4,0)/b_tot
        df = item["doc_freqs"]
        sw = item["single_slot_winner_counts"]
        sw_tot = sum(sw.values()) or 1
        top_sw = max(sw.items(), key=lambda x: x[1])
        print(
            f"{item['lemma']:<11} {item['subtype']:<15} {item['books_with_lemma']:>5} | "
            f"1:{p1:>3.0f}% 2:{p2:>3.0f}% 3:{p3:>3.0f}% 4:{p4:>3.0f}% | "
            f"eu:{100*df['ent_ub']:>3.0f}% eb:{100*df['ent_be']:>3.0f}% fu:{100*df['fl_ub']:>3.0f}% fb:{100*df['fl_be']:>3.0f}% | "
            f"{top_sw[0]} ({100*top_sw[1]/sw_tot:.0f}% av {sw_tot})"
        )

    print("\n" + "=" * 95)
    print("3. SJANGER-EFFEKTER PÅ BOKNIVÅ: SKJØNNLITTERATUR vs. FAGLITTERATUR")
    print("=" * 95)
    print(f"{'Verb':<11} {'Undertype':<15} | {'Skjønnlitteratur (inf / pres / pret)':<38} | {'Faglitteratur (inf / pres / pret)':<38}")
    print("-" * 110)
    for item in verb_stats["items"]:
        sk = item["genre_slot_totals"]["Skjønnlitteratur"]
        fa = item["genre_slot_totals"]["Faglitteratur"]
        sk_tot = sum(sk.values()) or 1
        fa_tot = sum(fa.values()) or 1
        sk_order = ">".join(sorted(["inf", "pres", "pret"], key=lambda s: sk[s], reverse=True))
        fa_order = ">".join(sorted(["inf", "pres", "pret"], key=lambda s: fa[s], reverse=True))
        print(
            f"{item['lemma']:<11} {item['subtype']:<15} | "
            f"{100*sk['inf']/sk_tot:>4.0f}% / {100*sk['pres']/sk_tot:>4.0f}% / {100*sk['pret']/sk_tot:>4.0f}% ({sk_order:<14}) | "
            f"{100*fa['inf']/fa_tot:>4.0f}% / {100*fa['pres']/fa_tot:>4.0f}% / {100*fa['pret']/fa_tot:>4.0f}% ({fa_order:<14})"
        )


if __name__ == "__main__":
    main()
