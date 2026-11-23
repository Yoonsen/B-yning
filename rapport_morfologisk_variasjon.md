# Ordformer og lemmaer: hvor mye morfologisk variasjon er det i korpuset?

*2026-11-19. Grunnlag: det OBT-taggede bokmålskorpuset (`korpus/obt_frekvenser.db`, 222 dokumenter,
1950–2026). Tallene er laget med `python -m sqlite.morfologisk_variasjon`. Bakgrunn og arbeidslogg:
`logg.md`, del 34–39.*

*Oppdatert 2026-11-23: analysen er kjørt på nytt med hele det taggede korpuset (lag 1–5, 1 076 dokumenter, 41,3 mill. ord), se avsnittet «Hele korpuset (lag 1–5)» til slutt. Avsnittene før det gjelder lag 1. Logg del 64–66.*

## Spørsmål

Hvor mye endrer antallet seg når de ulike bøyningsformene av et ord slås sammen til lemma? Er det
mye morfologisk variasjon i tekstene?

## Kort svar

- **Telt som ulike ord i ordforrådet blir forskjellen liten.** 410 711 ulike ordformer blir til
  363 042 lemmaer, altså 1,13 former per lemma. Det skyldes at de fleste lemmaene er sjeldne:
  - 60 % av alle substantivlemmaer forekommer bare én gang, og har da bare én form;
  - egennavn og ord taggeren ikke kjenner (OCR-feil, eldre rettskrivning, fremmedord), har nesten
    ingen bøyning.
- **I løpende tekst er variasjonen stor.** 30 % av alle ord, og 58 % av substantiv, verb og
  adjektiv, står i en annen form enn oppslagsformen. For verb gjelder det 79 %.
- **Hyppige ord brukes i mange former.** Substantiv og verb med over 1 000 forekomster opptrer i
  gjennomsnitt i over 6 ulike former, adjektiv i 5.
- **Variasjonen er stabil over tid, men varierer med teksttype.** Skjønnlitteratur har mest bøyning
  og aviser minst. I aviser går andelen bøyde former ned over perioden.

## Data og metode

- **Korpus.** 224 dokumenter ble trukket, balansert på 3 teksttyper × 8 tiår
  (`korpus/korpusoversikt.tsv`). 222 ble tagget med Oslo-Bergen-taggeren (OBT med CG-3 og OBT-Stat).
  To faglitterære bøker fra 1950-tallet feilet.
- **Ord** er tokens med minst én bokstav: 8,36 mill. Tegnsetting, tall og symboler er ikke med.
  Dokumentlengdene i korpusoversikten (10,7 mill.) teller også tegnsetting og tall.
- **Ordform** er formen OBT slo opp, med små bokstaver. Tegn som ikke er bokstaver eller tall, er
  fjernet i starten og slutten av formen. Det gjelder rester fra tokenisering og OCR, som «er.»,
  «er|», «_vært» og «kl.», og omfatter ca. 2 % av tokens og 9 % av formtypene. Uten rensingen blir
  forholdet former/lemma for høyt; for verb 2,53 i stedet for 2,32.
- **Lemma** er OBT-lemma + ordklasse. Homografe oppføringer i Ordbanken skilles ikke (OBT-lemmaet er
  en streng). Et ord taggeren har lemmatisert feil, telles under feil lemma, men det er få slike.
- **Mål:**
  - *former per lemma* = antall ulike ordformer / antall ulike lemmaer;
  - *andel bøyd* = andel tokens der formen er en annen enn lemmaet, altså bøyde former og
    skrivevarianter. Infinitiv, ubestemt entall og positiv grunnform regnes som ikke bøyd.
- **Sammenligning mellom grupper.** Antall typer vokser med tekstmengden. Tiår og teksttyper
  sammenlignes derfor ved samme antall tokens, med forventet antall typer i et tilfeldig utvalg
  (rarefaction, regnet eksakt). Andel bøyd påvirkes ikke av tekstmengden.

## Resultater

### Hele korpuset

| | tokens | ordformer | lemmaer | former per lemma | andel bøyd |
|---|---|---|---|---|---|
| alle ord | 8 357 379 | 410 711 | 363 042 | 1,13 | 0,30 |
| substantiv (appellativ), verb, adjektiv | 3 822 244 | 243 026 | 175 001 | 1,39 | 0,58 |

### Per ordklasse

| ordklasse | tokens | ordformer | lemmaer | former per lemma | andel bøyd |
|---|---|---|---|---|---|
| substantiv (appellativ) | 1 718 578 | 190 689 | 137 228 | 1,39 | 0,43 |
| verb | 1 418 488 | 23 757 | 10 256 | 2,32 | 0,79 |
| adjektiv | 685 178 | 37 998 | 27 517 | 1,38 | 0,53 |
| egennavn | 906 660 | 145 350 | 141 476 | 1,03 | 0,05 |
| determinativ | 501 171 | 949 | 837 | 1,13 | 0,25 |
| pronomen | 704 946 | 60 | 40 | 1,50 | 0,12 |
| adverb, preposisjon, konjunksjon, subjunksjon | 2 122 079 | 4 927 | 4 767 | ≈1,0 | ≈0,00 |
| ukjent for taggeren | 165 959 | 55 475 | 55 475 | 1,00 | 0,00 |

Egennavn og ukjente ord utgjør til sammen 13 % av tokens, men 49 % av formtypene. Det er
hovedgrunnen til at forholdet former/lemma for alle ord ligger så nær 1.

### Former per lemma etter hvor hyppig lemmaet er

| forekomster av lemmaet | substantiv: lemmaer | substantiv: former per lemma | verb: lemmaer | verb: former per lemma | adjektiv: lemmaer | adjektiv: former per lemma |
|---|---|---|---|---|---|---|
| 1 | 82 041 | 1,00 | 4 247 | 1,00 | 14 911 | 1,00 |
| 2–9 | 41 655 | 1,59 | 2 744 | 1,91 | 8 272 | 1,51 |
| 10–99 | 11 314 | 2,88 | 2 340 | 3,95 | 3 580 | 2,29 |
| 100–999 | 1 961 | 4,76 | 776 | 5,52 | 653 | 3,21 |
| 1000+ | 257 | 6,28 | 149 | 6,30 | 101 | 5,20 |

Forholdet former/lemma for hele korpuset er altså mest et mål på hvor mange sjeldne ord det er. For
ord som er hyppige nok til at paradigmet kan vise seg, er bøyningsvariasjonen stor.
Formtallene omfatter også skrivevarianter (f.eks. *ble/blei*) og en del OCR-feil.

### Per teksttype

Formtyper og lemmatyper ved 200 000 tokens (alle ord) og ved 100 000 tokens (substantiv, verb og
adjektiv):

| teksttype | alle ord: former per lemma | alle ord: andel bøyd | subst/verb/adj: former per lemma | subst/verb/adj: andel bøyd |
|---|---|---|---|---|
| avis | 1,12 | 0,26 | 1,31 | 0,52 |
| faglitteratur | 1,18 | 0,30 | 1,36 | 0,57 |
| skjønnlitteratur | 1,26 | 0,32 | 1,39 | 0,64 |

Skjønnlitteratur har færrest lemmaer per 200 000 ord, altså det minst varierte ordforrådet, men
bruker hvert lemma i flest former. Aviser er motsatt: de har mange ulike ord og navn, men mindre
bøyning.

### Per tiår

| tiår | alle ord: former per lemma | alle ord: andel bøyd | subst/verb/adj: former per lemma | subst/verb/adj: andel bøyd |
|---|---|---|---|---|
| 1950–1959 | 1,19 | 0,30 | 1,36 | 0,60 |
| 1960–1969 | 1,15 | 0,29 | 1,33 | 0,56 |
| 1970–1979 | 1,19 | 0,30 | 1,37 | 0,57 |
| 1980–1989 | 1,20 | 0,30 | 1,36 | 0,58 |
| 1990–1999 | 1,18 | 0,28 | 1,36 | 0,56 |
| 2000–2009 | 1,19 | 0,30 | 1,37 | 0,59 |
| 2010–2019 | 1,17 | 0,29 | 1,38 | 0,58 |
| 2020–2026 | 1,20 | 0,30 | 1,40 | 0,59 |

Det er ingen tydelig endring over tid for korpuset samlet. Variasjonen mellom tiårene er mindre enn
mellom teksttypene.

**Aviser er et unntak.** Andelen bøyde ord går ned fra 0,28 (1950-tallet) til 0,23 (2020-tallet).
Det skyldes delvis sammensetningen av ordklasser:
- egennavn øker fra 14 % til 21 % av tokens, og verb går ned fra 15 % til 13 %;
- men også innenfor substantiv, verb og adjektiv faller andelen bøyde former, fra 0,55 til 0,49.

Det kan henge sammen med f.eks. mer presens og færre bestemte former i nyhetsspråket. Det er ikke
undersøkt nærmere.

## Forbehold

- **Taggerfeil.** Lemmatiseringen kommer fra OBT og er ikke kontrollert manuelt. Ord taggeren ikke
  kjenner (2 % av tokens), regnes som egne lemmaer med én form.
- **OCR.** Eldre tekster har OCR-feil som gir ekstra formtyper. Et eksempel er *seiv* for *selv*
  (logg del 31).
- **Lite utvalg per celle.** Hvert tiår × teksttype har 5–20 dokumenter, så enkeltdokumenter kan
  påvirke tallene. Det er ikke regnet usikkerhet.
- **Skrivevarianter.** Former som *ble/blei* eller *boka/boken* telles som ulike former av samme
  lemma. Målene fanger derfor både bøyning og valgfrihet i rettskrivningen.

## Hele korpuset (lag 1–5)

*2026-11-23. Grunnlag: databasen med alle lag (`obt_frekvenser_alle_lag.db`, 1 076 dokumenter,
41,3 mill. ord med minst én bokstav; ligger utenfor repoet, se logg del 64). Kjørt med
`python -m sqlite.morfologisk_variasjon --db <alle lag> --utvalg 200000`, altså samme utvalgsstørrelse
som tallene for lag 1 over.*

### Lag 1 og alle lag

| | lag 1 (8,4 mill.) | alle lag (41,3 mill.) |
|---|---|---|
| former per lemma, alle ord | 1,13 | 1,10 |
| former per lemma, subst/verb/adj | 1,39 | 1,35 |
| andel bøyd, alle ord | 0,30 | 0,30 |
| andel bøyd, subst/verb/adj | 0,58 | 0,58 |
| andel bøyd, verb | 0,79 | 0,79 |
| former per lemma, verb | 2,32 | 1,92 |
| egennavn + ukjente ord: andel av tokens / av formtyper | 13 % / 49 % | 12 % / 52 % |
| substantivlemmaer som forekommer én gang | 60 % | 61 % |

- **Andelen bøyde ord er helt stabil.** Den avhenger ikke av korpusstørrelsen.
- **Forholdet former/lemma synker når korpuset vokser.** Stadig nye sjeldne ord, egennavn og ukjente
  ord med én form kommer til. Nedgangen er størst for verb (2,32 → 1,92): ordforrådet av verb vokser
  med mange sjeldne verb, mens de hyppige verbene allerede var godt dekket. Tallet må derfor alltid
  oppgis sammen med korpusstørrelsen og definisjonen (med eller uten egennavn osv.).

### Former per lemma etter hvor hyppig lemmaet er

| forekomster av lemmaet | substantiv | verb | adjektiv |
|---|---|---|---|
| 1 | 1,00 | 1,00 | 1,00 |
| 2–9 | 1,57 | 1,53 | 1,44 |
| 10–99 | 2,86 | 3,81 | 2,26 |
| 100–999 | 4,69 | 5,44 | 3,05 |
| 1000+ | 7,05 (1 288 lemmaer) | 6,69 (567) | 4,76 (446) |

Bildet er det samme som for lag 1: hyppige ord brukes i mange former.

### Per teksttype og tiår

Typer ved 200 000 tokens (alle ord) og 100 000 tokens (subst/verb/adj); lag 1 i parentes.

| teksttype | alle ord: former per lemma | alle ord: andel bøyd | subst/verb/adj: former per lemma | subst/verb/adj: andel bøyd |
|---|---|---|---|---|
| avis | 1,11 (1,12) | 0,26 (0,26) | 1,31 (1,31) | 0,52 (0,52) |
| faglitteratur | 1,18 (1,18) | 0,30 (0,30) | 1,34 (1,36) | 0,57 (0,57) |
| skjønnlitteratur | 1,25 (1,26) | 0,33 (0,32) | 1,39 (1,39) | 0,64 (0,64) |

- Over tid ligger andelen bøyde ord på 0,29–0,31 og former per lemma på 1,16–1,20 (alle ord) i alle
  tiår, omtrent som for lag 1.
- **Aviser:** andelen bøyde ord faller fra 0,28 (1950-tallet) til 0,22 (2020-tallet). Med fem ganger
  så mange avisnumre er nedgangen fra lag 1 (0,28 → 0,23) bekreftet.

  | tiår | 1950 | 1960 | 1970 | 1980 | 1990 | 2000 | 2010 | 2020 |
  |---|---|---|---|---|---|---|---|---|
  | lag 1 | 0,28 | 0,28 | 0,28 | 0,27 | 0,26 | 0,26 | 0,24 | 0,23 |
  | alle lag | 0,28 | 0,28 | 0,27 | 0,27 | 0,26 | 0,25 | 0,26 | 0,22 |

### Konklusjon

Hovedfunnene for lag 1 står seg med fem ganger så mye tekst:
- 30 % av alle ord og 79 % av verbene står i en annen form enn oppslagsformen;
- hyppige ord brukes i mange former;
- skjønnlitteratur har mest bøyning og aviser minst;
- i aviser går andelen bøyde ord ned.

Forholdet former/lemma er ikke en fast størrelse: det synker med korpusstørrelsen.
