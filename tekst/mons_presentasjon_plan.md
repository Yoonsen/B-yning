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
| 6 | Seks verbtyper | Fordeling 1A–3B, «infinitiv på 2. plass»-asymmetrien | rapport §3 | 🟡 trenger ternærplott |
| 7 | Stabilitet | Full rangering uendret 71/71 år for *vurdere, undersøke, overta, forsvinne, ankomme, rope, trenge, bestå* | rapport §4 | 🟡 trenger tidsseriefigur |
| 8 | Substantiv | Fire hovedtyper, «tall før bestemthet», stabilitet | `rapport_substantivtyper.md`, `sqlite/substantivtyper.py` | ✅ (diagram i decket) |
| 9 | Enkeltbøker | Bøker realiserer sjelden hele paradigmet; den globale profilen styrer hvilken form som blir med | `sqlite/book_dispersion.py`, logg del 11 | ✅ (trenger figur) |
| 10 | Dekomponering: *dør* | 71 % subst. / 29 % verb; *dø* flytter fra 2B til 2A | rapport §7.2 | 🟡 se hull 4–5 |
| 11 | Dekomponering over tid: *fisker* | Leksemandeler per år | `sqlite/decompose_fisker.py` | 🟡 trenger figur |
| 12 | Hvor godt virker metoden? | Validering mot kjent fasit | — | ❌ (se hull 4) |
| 13 | Litteratur og hva som er nytt | Karlsson, Arppe, Janda & Lyashevskaya, Milin mfl. | rapport §7.1 | 🟡 referanser må sjekkes (hull 6) |
| 14 | Oppsummering | | | ❌ |

## Hull som må tettes (prioritert)

1. ~~**Substantivresultatene mangler.**~~ Løst 2026-11-17: `rapport_substantivtyper.md` (N = 5 799). **Nytt:** abstractets eksempler stemmer ikke med dataene for *eple* (epler 45 % > eple 30 %) og *vite* (vet > visste > vite). Abstract/foredrag må samkjøres.
2. **Ingen ferdige figurer.** Foredraget trenger minst: (a) ternærplott inf/pres/pret for Sett A, (b) tidsserier for 4–6 stabile verb, (c) søyler før/etter dekomponering for *dø*, (d) leksemandeler for *fisker* over tid, (e) paradigmedekning i enkeltbøker.
3. ~~**Sett A-tallene kan ikke reproduseres fra kode.**~~ Løst 2026-11-19: `python3 -m sqlite.verbtyper` gjenskaper alle tall i rapportens §2–4 nøyaktig. **Beslutning 2026-11-19:** foredraget bruker bokkorpuset 1950–2020 for alle verb- og substantivtall. §3 i rapporten og lysbilde 6 er regnet om; `nb_totals`-tallene står bare som sammenligning.
4. **Dekomponereren er ikke validert.** For *dør* summerer de ukappede estimatene til 4,7 M mot 3,4 M observert (ca. 40 % for mye) før normalisering. Forslag: velg entydige lemmaer, lat som en form er flertydig, og mål feilen i estimatet. Det gir lysbilde 12.
5. **`«døde»` er flertydig (adjektivet *død*), og dekomponereren har ingen ankerregler for adjektiv.** Rangeringen for *dø* (2A) holder i et sensitivitetsoverslag, men prosenttallene på lysbilde 10 må beregnes på nytt. Se rapport §7.2 punkt 5.
6. **Referanser må sjekkes mot kildene.** Særlig: Milin, Filipović Đurđević & Baayen, «Paradigms bit by bit» står oppført i *Cognitive Linguistics* 20(1); vi tror det er et kapittel i Blevins & Blevins (red.), *Analogy in Grammar* (OUP 2009). Newman 2008 og Karlsson 1986 bør også verifiseres.
7. **Over tid-delen av dekomponeringen.** Abstractet sier «over tid»; *dør* er bare beregnet på totaler. Minst ett eksempel bør vises som tidsserie (*fisker* er nærmest ferdig).
