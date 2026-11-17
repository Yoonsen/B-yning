# Rapport: Kvantitative substantivtyper og rang-stabilitet

*Delrapport i MONS-prosjektet «Leksikalske bøyningsprofiler: ordboksdata og historiske n-gram». Motstykke til `rapport_verbtyper.md`. Alle tall kan gjenskapes med `python3 -m sqlite.substantivtyper`; per-lemma-resultater ligger i `resultater/substantivtyper.tsv`.*

---

## 1. Hovedspørsmål

For substantiv med fire kjerneformer (`ent_ub`, `ent_be`, `fl_ub`, `fl_be`):
1. Hvilken form dominerer, og hvordan fordeler substantivene seg på hovedtyper?
2. Følger 2. plass av 1. plass, og er det tall eller bestemthet som styrer?
3. Hvor stabil er rangeringen fra år til år, 1950–2020?

## 2. Gullstandard (Sett A for substantiv)

Samme logikk som for verbene: alle kjerneformer skal være entydige i hele Norsk Ordbank, og ingen form kan gå igjen i to kategorier.

| Steg | Krav | Lemmaer igjen |
| :--- | :--- | ---: |
| 1 | Alle fire kjerneformer finnes (`pos = 'subst'`, `boy_gruppe = 'substantiv'`) | 116 748 |
| 2 | Vanlig grunnform (bare små bokstaver, minst tre tegn) og ikke på listen over falske venner | 114 103 |
| 3 | Ingen kjerneform deler ordform med noe annet lemma (`antall_lemma_id = 1`) | 104 282 |
| 4 | Internt distinkte: ingen form står i to kategorier (utelukker *hus – hus*, *politi – politi*) | 79 786 |
| 5 | ≥ 100 000 treff i `nb_totals` (sum av kjerneformene) | 6 007 |
| 6 | Alle fire kategorier belagt i bokkorpuset 1950–2020 | **5 799** |

- Alternative former i samme kategori summeres (*døren/døra*, *epla/eplene*).
- Steg 2 fjerner bokstavnavn (*j, v, Z*), forkortelser (*TV, PR, SMS*) og bindestreksord. I tillegg er 25 falske venner tatt ut for hånd etter gjennomgang av lemmaer med > 97 % `ent_ub`. Her er `ent_ub`-formen i praksis et annet ord: riksmål og svensk (*nogen, vor, slig, hon*), personnavn (*jan, lian*), engelsk tekst (*used, during, being, half*) eller OCR-feil (*forst* for *først*). Listen står i `FALSKE_VENNER` i skriptet. Det kan finnes flere slike; resten av listen over lemmaer med > 97 % `ent_ub` er mest ekte massesubstantiv og faste uttrykk (*på bekostning av, i favør, i varetekt*).
- Steg 6 bruker bokkorpuset fordi `nb_totals` mangler sjeldne ordformer. Krever man at alle formene finnes i `nb_totals`, faller over halvparten av lemmaene ut.
- Profiler og stabilitet er regnet i bokkorpuset (`dhlab ngram_book`, `nob`, 1950–2020), som verbene i `rapport_verbtyper.md` §4.

## 3. Fire hovedtyper og den sekundære rangeringen

| Hovedtype (1. plass) | Andel av N = 5 799 | 2. plass (andel innen hovedtypen) | Eksempler |
| :--- | ---: | :--- | :--- |
| **`ent_ub` på topp** | **67,1 %** | `ent_be` 72,0 %, `fl_ub` 27,3 %, `fl_be` 0,7 % | *tid, utvikling, betydning, kvalitet, kirke, stilling, kunde* |
| **`ent_be` på topp** | **16,5 %** | `ent_ub` 91,2 %, `fl_ub` 5,1 %, `fl_be` 3,7 % | *regjering, familie, sommer, stat, hode, gård, seng, befolkning* |
| **`fl_ub` på topp** | **14,5 %** | `ent_ub` 71,5 %, `fl_be` 24,3 %, `ent_be` 4,2 % | *medlem, representant, menneske, million, person, uke, måned* |
| **`fl_be` på topp** | **1,9 %** | `fl_ub` 82,3 %, `ent_ub` 10,6 %, `ent_be` 7,1 % | *amerikaner, engelskmann, brite, bonde, beboer, kommunist, omgivelse* |

Alle 24 mulige rekkefølger er belagt, men tre av dem dekker 74 %:

| Full rangering | Andel | Snittprofil `ent_ub / ent_be / fl_ub / fl_be` | Eksempler |
| :--- | ---: | :---: | :--- |
| `ent_ub > ent_be > fl_ub > fl_be` | 45,8 % | 70,2 / 21,7 / 6,2 / 1,9 | *tid, kommune, kirke, lørdag, bilde* |
| `ent_ub > fl_ub > ent_be > fl_be` | 16,1 % | 58,2 / 13,0 / 23,9 / 4,9 | *stilling, kunde, forbindelse, dame, verdi* |
| `ent_be > ent_ub > fl_ub > fl_be` | 12,0 % | 30,2 / 57,9 / 8,2 / 3,6 | *familie, regjering, sommer, periode, båt* |
| `fl_ub > ent_ub > fl_be > ent_be` | 5,2 % | 26,1 / 7,5 / 53,2 / 13,2 | *medlem, representant, myndighet, politiker* |
| `fl_ub > ent_ub > ent_be > fl_be` | 5,1 % | 30,8 / 14,5 / 46,6 / 8,1 | *uke, menneske, million, person, måned* |
| `fl_ub > fl_be > ent_ub > ent_be` | 3,2 % | 12,0 / 5,3 / 59,5 / 23,2 | *opplysning, jente, forelder, nordmann, student* |
| `ent_be > ent_ub > fl_be > fl_ub` | 3,1 % | 21,3 / 69,2 / 3,7 / 5,8 | *hode, gård, ettermiddag, formiddag, hjørne* |
| øvrige 17 rekkefølger | 9,5 % | | |

### Tolkning
1. **Tall er en sterkere skillelinje enn bestemthet.** Når entall er på topp, er 2. plass nesten alltid den andre entallsformen (`ent_ub → ent_be` 72 %, `ent_be → ent_ub` 91 %). Når `fl_be` er på topp, er 2. plass `fl_ub` i 82 %. Substantivene velger altså først tall, deretter bestemthet.
   - Unntaket er `fl_ub` på topp, der 2. plass er `ent_ub` i 71,5 %. Det er tellbare substantiv som brukes enten som én enhet eller som en mengde (*en person / tre personer*, *en uke / to uker*), sjelden med bestemt artikkel.
2. **`fl_be` er nesten alltid sist.** Den står på topp for bare 1,9 % og på 2. plass under `ent_ub` for 0,7 %.
3. **Hovedtypene har semantiske profiler** (foreløpige karakteristikker, ikke testet systematisk):
   - `ent_ub`: abstrakte substantiv, massesubstantiv og prosesssubstantiv (*tid, utvikling, betydning, kvalitet, kompetanse*).
   - `ent_be`: unike eller situasjonsgitte referenter: institusjoner, årstider og tid på døgnet, kroppsdeler, hjem og omgivelser (*regjering, staten, sommeren, hodet, gården, senga*).
   - `fl_ub`: tellbare substantiv om personer og mengder (*medlemmer, millioner, personer, måneder*).
   - `fl_be`: gruppe- og nasjonalitetsbetegnelser omtalt som kollektiv (*amerikanerne, britene, bøndene, kommunistene*).
4. **Entall dominerer samlet:** 73,9 % av alle tokens, og entall > flertall for 84,8 % av lemmaene.

## 4. Stabilitet 1950–2020

Målt for de 4 355 lemmaene som har ≥ 50 treff i minst 60 av de 71 årene. For hvert lemma sammenlignes rangeringen hvert år med rangeringen for hele perioden.

| Hva er likt som totalrangeringen? | Median andel av årene | Lemmaer med 100 % (71 av 71 år) |
| :--- | ---: | ---: |
| 1. plass | 100,0 % | 2 314 (53,1 %) |
| 1. og 2. plass | 90,1 % | 1 284 (29,5 %) |
| Hele rangeringen (alle fire) | 78,9 % | 343 (7,9 %) |

Eksempler med samme fullstendige rekkefølge i alle 71 år: *tid, utvikling, betydning, virksomhet, historie, kvalitet* (`ent_ub > ent_be > fl_ub > fl_be`), *retning, mengde* (`ent_ub > fl_ub > ent_be > fl_be`), *sommer, begynnelse, seng, befolkning, virkelighet* (`ent_be > ent_ub > fl_ub > fl_be`), *medlem, egenskap* (`fl_ub > ent_ub > fl_be > ent_be`), *utgift* (`fl_ub > fl_be > ent_ub > ent_be`).

Med fire former er det flere naboplasser som kan bytte enn med verbenes tre, så kravet til full stabilitet er strengere enn i verbrapporten. Tallene kan derfor ikke sammenlignes direkte.

## 5. Eksempelordene fra abstractet (Sett B)

Bokkorpuset 1950–2020, uten dekomponering:

| Ord | Rangering | `ent_ub / ent_be / fl_ub / fl_be` | Merknad |
| :--- | :--- | :---: | :--- |
| *eple* | `fl_ub > ent_ub > fl_be > ent_be` | 30,2 / 11,1 / **45,1** / 13,5 | Ingen kollisjon; under 100 000-grensen, derfor ikke i Sett A |
| *buss* | `ent_be > ent_ub > fl_ub > fl_be` | 36,9 / **41,9** / 15,3 / 6,0 | Alle former kolliderer med *busse* (subst.) og *busse* (verb) |
| *kirke* | `ent_ub > ent_be > fl_ub > fl_be` | **45,0** / 43,4 / 7,8 / 3,8 | Sett A |
| *sol* | `ent_be > ent_ub > fl_ub > fl_be` | 31,2 / **67,1** / 1,5 / 0,1 | Kollisjoner: *sol, sola, soler* |
| *bil* | `ent_be > ent_ub > fl_ub > fl_be` | 35,3 / **41,3** / 17,7 / 5,7 | Alle former kolliderer i Ordbanken |
| *dag* | `ent_ub > fl_ub > ent_be > fl_be` | **59,5** / 17,1 / 19,9 / 3,4 | Kollisjoner: *dag, dager* |

**Abstractet må rettes for *eple*.** Abstractet sier at ubestemt entall *eple* dominerer over *eplet* og *epler*. Bokkorpuset gir **epler 45 % > eple 30 % > eplet 11 %**, og `nb_totals` peker samme vei (*epler* 643 903, *eple* 362 239, *eplet* 106 184). *buss* stemmer med abstractet (*bussen* på topp), men alle formene til *buss* er formelt flertydige i Ordbanken. Se også avviket for *vite* i `logg.md` del 14.

## 6. Begrensninger og neste steg

- Falske venner er bare fjernet der `ent_ub` dominerer. Tilsvarende støy i andre kategorier er ikke undersøkt.
- Sammensatte substantiv er med. Det kan være verdt å skille simplex fra sammensetninger med `leddanalyse`.
- Den semantiske karakteristikken av hovedtypene er en tolkning av eksempellistene, ikke en systematisk klassifisering.
- Genus, tellbarhet og animathet er ikke koblet på. Det er de mest naturlige forklaringsvariablene å teste.
