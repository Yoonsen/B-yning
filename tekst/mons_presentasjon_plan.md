# MONS-presentasjon: plan og hull (utkast 2026-11-17)

Arbeidsdokument for presentasjonen. Status per punkt: ✅ finnes i repoet, 🟡 finnes men må sjekkes eller pusses, ❌ mangler.

## Foreslått lysbilderekke (ca. 20 min)

| # | Lysbilde | Innhold | Kilde | Status |
|---|---|---|---|---|
| 1 | Tittel | Leksikalske bøyningsprofiler: ordboksdata og historiske n-gram | `abstract.md` | ✅ |
| 2 | Spørsmålet | *gikk > gå/går*, men *vite > vet/visste*; *eple > eplet/epler*, men *bussen > buss/busser* | `abstract.md` | ✅ (trenger figur) |
| 3 | Data | Norsk Ordbank (paradigmer) + NB n-gram (former, 1950–2020) | `sqlite/build_db.py`, `sqlite/ngram.py` | ✅ |
| 4 | Problemet: former ≠ leksemer | *fisker* = 4 analyser; paradigmegrafen: 87,4 % av lemmaene er isolert, 97,3 % i komponenter ≤ 4 | `sqlite/paradigm_graph.py`, rapport 7.3 | 🟡 trenger figur |
| 5 | Gullstandard | Sett A (N = 580 globalt POS-isolerte verb) / Sett B | rapport §2, `sqlite/verbtyper.py` | ✅ |
| 6 | Seks verbtyper | Fordeling 1A–3B, «infinitiv på 2. plass»-asymmetrien | rapport §3, `tekst/figurer/verb_ternaer.png` (eget lysbilde 6b) | ✅ |
| 7 | Stabilitet | Full rangering uendret 71/71 år for *vurdere, undersøke, overta, forsvinne, ankomme, rope, trenge, bestå* | rapport §4, `tekst/figurer/verb_stabilitet.png` | ✅ |
| 8 | Substantiv | Fire hovedtyper, «tall før bestemthet», stabilitet | `rapport_substantivtyper.md`, `sqlite/substantivtyper.py` | ✅ (diagram i decket) |
| 9 | Enkeltbøker | Bøker realiserer sjelden hele paradigmet; den globale profilen styrer hvilken form som blir med | `sqlite/book_dispersion.py`, logg del 11 | ✅ (trenger figur) |
| 10 | Dekomponering: *dør* | 64 % subst. / 36 % verb; *dø* flytter fra 2B til 2A | rapport §7.2 | ✅ rangeringen er robust for adjektivet i «døde»; prosentene usikre (hull 5) |
| 11 | Dekomponering over tid: *fisker* | Leksemandeler per år | `sqlite/figurer.py`, `tekst/figurer/fisker_over_tid.png` | 🟡 figur med to varianter; nivået er ikke bestemt, bare trenden for *fisk* (fl) er robust |
| 12 | Hvor godt virker metoden? | Validering mot kjent fasit | `rapport_dekomponering_validering.md`, `sqlite/valider_dekomponering.py` | ✅ |
| 13 | Litteratur og hva som er nytt | Karlsson, Arppe, Janda & Lyashevskaya, Milin mfl. | rapport §7.1 | ✅ referanser sjekket (hull 6) |
| 14 | Oppsummering | | | ❌ |

## Hull som må tettes (prioritert)

1. ~~**Substantivresultatene mangler.**~~ Løst 2026-11-17: `rapport_substantivtyper.md` (N = 5 799). **Nytt:** abstractets eksempler stemmer ikke med dataene for *eple* (epler 45 % > eple 30 %) og *vite* (vet > visste > vite). Abstract/foredrag må samkjøres.
2. ~~**Ingen ferdige figurer.**~~ Stort sett løst 2026-11-20: `python3 -m sqlite.figurer` lager (a) ternærplott, (b) tidsserier for *vurdere, undersøke, forsvinne, trenge* og (d) *fisker* over tid i `tekst/figurer/`. (c) *dø* og (e) enkeltbøker er native diagrammer i decket. Gjenstår: (4) paradigmegrafen har ingen figur.
3. ~~**Sett A-tallene kan ikke reproduseres fra kode.**~~ Løst 2026-11-19: `python3 -m sqlite.verbtyper` gjenskaper alle tall i rapportens §2–4 nøyaktig. **Beslutning 2026-11-19:** foredraget bruker bokkorpuset 1950–2020 for alle verb- og substantivtall. §3 i rapporten og lysbilde 6 er regnet om; `nb_totals`-tallene står bare som sammenligning.
4. ~~**Dekomponereren er ikke validert.**~~ Løst 2026-11-20 (`rapport_dekomponering_validering.md`): riktig leksem i flertall for 78–80 % av kunstige homografer med log-regresjon, median feil 10–11 pp. De faste reglene i `decomposer.py` er skjeve (dør-typen: −13 pp for substantivet). Reglene er byttet ut med log-regresjon lært i samme korpus, og *dør* er regnet om: 64 % substantiv i bøker (lysbilde 10).
5. ~~**`«døde»` er flertydig (adjektivet *død*).**~~ Avklart 2026-11-20: dekomponereren har adjektivankre (`sqlite/adjektiv_gold.py`), men ankrene i ordfamilien *dø/død* er atypiske (sum anslag / obs. 0,05), så adjektivandelen er ikke bestemt (overslag 2–46 %). *dø* er 2A så lenge adjektivet er under 77 % av «døde». Lysbilde 11 viser tallene uten adjektivkorreksjon og sier dette. En presis andel krever bigramdata (ikke tilgjengelig nå).
6. ~~**Referanser må sjekkes mot kildene.**~~ Løst 2026-11-21: full referanseliste i `rapport_verbtyper.md` §7.1. Rettet: «Paradigms bit by bit» er Milin, Kuperman, Kostić & Baayen i *Analogy in Grammar* (OUP 2009, 214–252); funnet om relativ entropi er Milin, Filipović Đurđević & Moscoso del Prado Martín, *JML* 60(1) 2009. Janda & Lyashevskaya har sidene 717–762. Newman 2008 er et konferansebidrag (IsCLL-11). Karlsson 1986 er bekreftet (ZPSK 39(1), 19–28). «Fokalformer» er tatt ut som Karlsson-begrep inntil fulltekst er lest.
7. **Over tid-delen av dekomponeringen.** *Delvis løst 2026-11-20:* *fisker* er dekomponert år for år (lysbilde 12) med forholdstall lært i bokkorpuset (sum anslag / obs. 1,3) og vist mot de overførte tallene fra `nb_totals` (2,0). Nivået for *en fisker* er ikke bestemt; bare økningen for *fisk* (fl) er robust. Abstractet sier «over tid»; *dør* er bare beregnet på totaler. Minst ett eksempel bør vises som tidsserie (*fisker* er nærmest ferdig).
