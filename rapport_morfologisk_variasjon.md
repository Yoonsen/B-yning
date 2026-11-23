# Ordformer og lemmaer: hvor mye morfologisk variasjon er det i korpuset?

*Grunnlag: det OBT-taggede bokmålskorpuset, tagget i to omganger: lag 1 (2026-11-19, 222 dokumenter)
og hele korpuset, lag 1–5 (2026-11-23, 1 076 dokumenter). Tallene er laget med
`python -m sqlite.morfologisk_variasjon`. Arbeidslogg: `logg.md`, del 34–39 (lag 1) og 64–66
(lag 1–5).*

## Spørsmål

Hvor mye endrer antallet seg når de ulike bøyningsformene av et ord slås sammen til lemma? Er det
mye morfologisk variasjon i tekstene?

## Kort svar

Tallene er fra hele korpuset (41,3 mill. ord). Lag 1 alene (8,4 mill. ord) gir samme bilde, se
«Lag 1» nederst.

- **Telt som ulike ord i ordforrådet blir forskjellen liten.** 1 308 593 ulike ordformer blir til
  1 190 959 lemmaer, altså 1,10 former per lemma (lag 1: 1,13). Det skyldes at de fleste lemmaene er
  sjeldne:
  - 61 % av alle substantivlemmaer forekommer bare én gang, og har da bare én form;
  - egennavn og ord taggeren ikke kjenner (OCR-feil, eldre rettskrivning, fremmedord), har nesten
    ingen bøyning.

  Tallet synker når korpuset vokser, fordi stadig nye sjeldne ord kommer til. Det er altså ikke en
  fast størrelse.
- **I løpende tekst er variasjonen stor.** 30 % av alle ord, og 58 % av substantiv, verb og
  adjektiv, står i en annen form enn oppslagsformen. For verb gjelder det 79 %. Disse andelene er de
  samme i lag 1 og i hele korpuset.
- **Hyppige ord brukes i mange former.** Substantiv og verb med over 1 000 forekomster opptrer i
  gjennomsnitt i om lag 7 ulike former, adjektiv i 5.
- **Variasjonen er stabil over tid, men varierer med teksttype.** Skjønnlitteratur har mest bøyning
  og aviser minst. I aviser går andelen bøyde former ned over perioden, fra 0,28 til 0,22.

## Data og metode

- **Korpus, tagget i to omganger.** Korpuset er balansert på 3 teksttyper (skjønnlitteratur,
  faglitteratur, aviser) × 8 tiår (1950–2026) og tagget med Oslo-Bergen-taggeren (OBT med CG-3 og
  OBT-Stat). Se `korpus/korpusoversikt.tsv`.

  | | dokumenter trukket | tagget | ord |
  |---|---|---|---|
  | **lag 1** (første, lille korpus) | 224 | 222 | 8,4 mill. |
  | **lag 1–5** (hele korpuset) | 1 097 | 1 076 | 41,3 mill. |

  - Lag 1 ble tagget først. Med 5–20 dokumenter per teksttype og tiår ble det for lite til enkelte
    analyser, og korpuset ble derfor utvidet med fire nye lag, hvert balansert som det første.
  - 21 dokumenter fikk tidsavbrudd i taggeren (1,8 % av ordene). De er spredt over teksttyper og
    tiår.
- **Ord** er tokens med minst én bokstav. Tegnsetting, tall og symboler er ikke med.
- **Ordform** er formen OBT slo opp, med små bokstaver.
  - Tegn som ikke er bokstaver eller tall, er fjernet i starten og slutten av formen. Det gjelder
    rester fra tokenisering og OCR, som «er.», «er|», «_vært» og «kl.».
  - I lag 1 gjaldt det ca. 2 % av tokens og 9 % av formtypene. Uten rensingen blir forholdet
    former/lemma for høyt; for verb i lag 1 2,53 i stedet for 2,32.
- **Lemma** er OBT-lemma + ordklasse. Homografe oppføringer i Ordbanken skilles ikke (OBT-lemmaet er
  en streng).
- **Mål:**
  - *former per lemma* = antall ulike ordformer / antall ulike lemmaer;
  - *andel bøyd* = andel tokens der formen er en annen enn lemmaet, altså bøyde former og
    skrivevarianter. Infinitiv, ubestemt entall og positiv grunnform regnes som ikke bøyd.
- **Sammenligning mellom grupper.** Antall typer vokser med tekstmengden. Tiår og teksttyper
  sammenlignes derfor ved samme antall tokens, med forventet antall typer i et tilfeldig utvalg
  (rarefaction, regnet eksakt): 200 000 tokens for alle ord og 100 000 for substantiv, verb og
  adjektiv. Andel bøyd påvirkes ikke av tekstmengden.

## Resultater: hele korpuset (lag 1–5)

*Databasen med alle lag (`obt_frekvenser_alle_lag.db`) ligger utenfor repoet, se logg del 67.*

### Hele korpuset

| | tokens | ordformer | lemmaer | former per lemma | andel bøyd |
|---|---|---|---|---|---|
| alle ord | 41 298 189 | 1 308 593 | 1 190 959 | 1,10 | 0,30 |
| substantiv (appellativ), verb, adjektiv | 19 181 848 | 732 165 | 541 592 | 1,35 | 0,58 |

### Per ordklasse

| ordklasse | tokens | ordformer | lemmaer | former per lemma | andel bøyd |
|---|---|---|---|---|---|
| substantiv (appellativ) | 8 756 979 | 605 253 | 439 332 | 1,38 | 0,43 |
| verb | 6 961 635 | 46 765 | 24 308 | 1,92 | 0,79 |
| adjektiv | 3 463 234 | 102 578 | 77 952 | 1,32 | 0,54 |
| egennavn | 4 279 279 | 472 436 | 461 011 | 1,02 | 0,04 |
| determinativ | 2 530 816 | 2 583 | 2 381 | 1,08 | 0,25 |
| pronomen | 3 317 091 | 71 | 42 | 1,69 | 0,11 |
| adverb, preposisjon, konjunksjon, subjunksjon | 10 514 806 | 16 336 | 15 969 | ≈1,0 | ≈0,00 |
| ukjent for taggeren | 803 269 | 211 256 | 211 256 | 1,00 | 0,00 |

Egennavn og ukjente ord utgjør til sammen 12 % av tokens, men 52 % av formtypene. Det er
hovedgrunnen til at forholdet former/lemma for alle ord ligger så nær 1.

### Former per lemma etter hvor hyppig lemmaet er

| forekomster av lemmaet | substantiv: lemmaer | substantiv: former per lemma | verb: lemmaer | verb: former per lemma | adjektiv: lemmaer | adjektiv: former per lemma |
|---|---|---|---|---|---|---|
| 1 | 270 104 | 1,00 | 13 542 | 1,00 | 47 104 | 1,00 |
| 2–9 | 125 439 | 1,57 | 5 226 | 1,53 | 20 049 | 1,44 |
| 10–99 | 36 096 | 2,86 | 3 147 | 3,81 | 8 181 | 2,26 |
| 100–999 | 6 405 | 4,69 | 1 826 | 5,44 | 2 172 | 3,05 |
| 1000+ | 1 288 | 7,05 | 567 | 6,69 | 446 | 4,76 |

Forholdet former/lemma for hele korpuset er altså mest et mål på hvor mange sjeldne ord det er. For
ord som er hyppige nok til at paradigmet kan vise seg, er bøyningsvariasjonen stor.
Formtallene omfatter også skrivevarianter (f.eks. *ble/blei*) og en del OCR-feil.

### Per teksttype

| teksttype | alle ord: former per lemma | alle ord: andel bøyd | subst/verb/adj: former per lemma | subst/verb/adj: andel bøyd |
|---|---|---|---|---|
| avis | 1,11 | 0,26 | 1,31 | 0,52 |
| faglitteratur | 1,18 | 0,30 | 1,34 | 0,57 |
| skjønnlitteratur | 1,25 | 0,33 | 1,39 | 0,64 |

Skjønnlitteratur har færrest lemmaer per 200 000 ord, altså det minst varierte ordforrådet, men
bruker hvert lemma i flest former. Aviser er motsatt: de har mange ulike ord og navn, men mindre
bøyning.

### Per tiår

| tiår | alle ord: former per lemma | alle ord: andel bøyd | subst/verb/adj: former per lemma | subst/verb/adj: andel bøyd |
|---|---|---|---|---|
| 1950–1959 | 1,17 | 0,30 | 1,34 | 0,58 |
| 1960–1969 | 1,16 | 0,29 | 1,33 | 0,57 |
| 1970–1979 | 1,19 | 0,30 | 1,35 | 0,57 |
| 1980–1989 | 1,20 | 0,31 | 1,36 | 0,58 |
| 1990–1999 | 1,18 | 0,30 | 1,35 | 0,57 |
| 2000–2009 | 1,18 | 0,30 | 1,36 | 0,59 |
| 2010–2019 | 1,17 | 0,30 | 1,36 | 0,59 |
| 2020–2026 | 1,19 | 0,29 | 1,39 | 0,58 |

Det er ingen tydelig endring over tid for korpuset samlet. Variasjonen mellom tiårene er mindre enn
mellom teksttypene.

**Aviser er et unntak.** Andelen bøyde ord går ned fra 0,28 (1950-tallet) til 0,22 (2020-tallet):

| tiår | 1950 | 1960 | 1970 | 1980 | 1990 | 2000 | 2010 | 2020 |
|---|---|---|---|---|---|---|---|---|
| andel bøyd, alle ord | 0,28 | 0,28 | 0,27 | 0,27 | 0,26 | 0,25 | 0,26 | 0,22 |
| andel bøyd, subst/verb/adj | 0,55 | 0,54 | 0,53 | 0,53 | 0,51 | 0,52 | 0,52 | 0,47 |
| egennavn, andel av tokens | 14 % | 15 % | 15 % | 16 % | 20 % | 22 % | 21 % | 24 % |
| verb, andel av tokens | 15 % | 15 % | 14 % | 14 % | 13 % | 13 % | 13 % | 12 % |

Nedgangen skyldes delvis sammensetningen av ordklasser: flere egennavn og færre verb. Men også
innenfor substantiv, verb og adjektiv faller andelen bøyde former. Det kan henge sammen med
f.eks. mer presens og færre bestemte former i nyhetsspråket. Det er ikke undersøkt nærmere.

## Lag 1 (første korpus, 2026-11-19)

Den første analysen ble gjort på lag 1 alene (222 dokumenter, 8,4 mill. ord;
`korpus/obt_frekvenser.db` i repoet). Hovedtallene sammenlignet med hele korpuset:

| | lag 1 (8,4 mill.) | lag 1–5 (41,3 mill.) |
|---|---|---|
| former per lemma, alle ord | 1,13 | 1,10 |
| former per lemma, subst/verb/adj | 1,39 | 1,35 |
| former per lemma, verb | 2,32 | 1,92 |
| andel bøyd, alle ord / subst/verb/adj / verb | 0,30 / 0,58 / 0,79 | 0,30 / 0,58 / 0,79 |
| egennavn + ukjente ord: andel av tokens / av formtyper | 13 % / 49 % | 12 % / 52 % |
| substantivlemmaer som forekommer én gang | 60 % | 61 % |
| former per lemma, lemmaer med 1000+ forekomster (subst / verb / adj) | 6,3 / 6,3 / 5,2 | 7,1 / 6,7 / 4,8 |
| andel bøyd i aviser, 1950-tallet → 2020-tallet | 0,28 → 0,23 | 0,28 → 0,22 |

- **Andelen bøyde ord er helt stabil.** Den er den samme i lag 1 og i hele korpuset.
- **Forholdet former/lemma synker når korpuset vokser.** Nedgangen er størst for verb
  (2,32 → 1,92): ordforrådet av verb vokser med mange sjeldne verb, mens de hyppige verbene allerede
  var godt dekket i lag 1. Tallet må derfor alltid oppgis sammen med korpusstørrelsen og
  definisjonen (med eller uten egennavn osv.).
- **Teksttyper og tiår** gir samme bilde i lag 1. Tallene per teksttype er like med to desimaler
  (±0,01–0,02), og nedgangen i avisene var allerede synlig.

## Forbehold

- **Taggerfeil.** Lemmatiseringen kommer fra OBT og er ikke kontrollert manuelt. Ord taggeren ikke
  kjenner (2 % av tokens), regnes som egne lemmaer med én form.
- **OCR.** Eldre tekster har OCR-feil som gir ekstra formtyper. Et eksempel er *seiv* for *selv*
  (logg del 31).
- **Utvalg per celle.** Hvert tiår × teksttype har ca. 30–88 dokumenter i hele korpuset (5–20 i lag 1).
  Enkeltdokumenter kan fortsatt påvirke tallene for en celle. Det er ikke regnet usikkerhet.
- **Skrivevarianter.** Former som *ble/blei* eller *boka/boken* telles som ulike former av samme
  lemma. Målene fanger derfor både bøyning og valgfrihet i rettskrivningen.
