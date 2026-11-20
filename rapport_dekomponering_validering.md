# Rapport: Validering av dekomponereren

*Delrapport i MONS-prosjektet. Tallene i §1–3 gjenskapes med `python3 -m sqlite.valider_dekomponering`, og per-par-resultatene står i `resultater/dekomponering_validering.tsv`. Tallene i §4 gjenskapes med `python3 -m sqlite.figurer`.*

---

## 1. Oppsett

Dekomponereren anslår hvor mye av en flertydig ordform som tilhører hvert leksem. Den gjør det ved å anslå frekvensen til formen i hvert kandidatparadigme ut fra resten av paradigmet. I gullstandardene er alle kjerneformer entydige, så der kjenner vi fasiten:

- **Substantiv:** 2 772 lemmaer fra `rapport_substantivtyper.md` der alle fire kategorier er belagt i `nb_totals`.
- **Verb:** de 533 verbene i Sett A der alle fire kategorier er belagt i `nb_totals`.

Tre metoder sammenlignes:

| Metode | Hva den gjør |
| :--- | :--- |
| **regler** | De faste forholdstallene i `sqlite/decomposer.py` (`estimate_from_slots`), slik de brukes i dag |
| **lært** | Median av forholdet mellom målkategorien og summen av de andre, lært på gullstandarden |
| **logreg** | Lineær regresjon av log-frekvensen i målkategorien på log-frekvensene i de andre kategoriene |

`lært` og `logreg` er testet med 5-delt kryssvalidering, så ingen lemmaer brukes til å anslå seg selv. Alle tall er fra `nb_totals`, som er det korpuset dekomponereren bruker.

## 2. Test 1: én kategori holdes ute

Hvor nær kommer anslaget for én kategori den faktiske frekvensen? «Typisk avvik» er medianen av |log(anslag / fasit)|, uttrykt som en faktor.

| | Kategori | Typisk avvik: regler / lært / logreg | Innen ×2 (logreg) | Skjevhet med regler |
| :--- | :--- | :---: | ---: | ---: |
| subst | ent ub | ×2,03 / ×1,88 / ×1,66 | 65 % | ×0,60 |
| subst | ent be | ×2,45 / ×2,02 / ×1,75 | 59 % | ×2,07 |
| subst | fl ub | ×1,74 / ×2,14 / ×1,61 | 68 % | ×0,99 |
| subst | fl be | ×1,74 / ×2,03 / ×1,61 | 66 % | ×1,01 |
| verb | inf | ×1,89 / ×1,76 / ×1,55 | 67 % | ×1,36 |
| verb | pres | ×2,15 / ×2,11 / ×1,80 | 59 % | ×1,62 |
| verb | pret | ×2,27 / ×1,77 / ×1,68 | 62 % | ×2,02 |
| verb | perf-part | ×2,65 / ×2,24 / ×2,04 | 49 % | ×0,53 |

- Log-regresjonen er best i alle kategoriene, men selv den bommer typisk med en faktor på 1,6–2.
- Flere av de faste reglene er systematisk skjeve. De overvurderer `ent be` og `pret` med omtrent en faktor 2. De undervurderer `ent ub` (×0,60) og `perf-part` (×0,53).

## 3. Test 2: kunstige homografer

En substantivform og en verbform med kjent fasit slås sammen til én kunstig flertydig form, 3 000 tilfeldige par per type. Feilen måles som anslått minus faktisk substantivandel, i prosentpoeng (pp).

| Homograftype | Median feil, regler / logreg | Riktig leksem i flertall, regler / logreg | Skjevhet med regler | Sum / obs. med regler |
| :--- | :---: | :---: | ---: | ---: |
| fl ub + pres (*fisker, ønsker*) | 13,3 / 11,0 pp | 71 / 78 % | −3,8 pp | 1,21 |
| ent be + pret (*landet*) | 14,6 / 11,5 pp | 76 / 78 % | +2,7 pp | 1,92 |
| ent ub + inf (*fiske*) | 14,4 / 10,5 pp | 72 / 80 % | −9,8 pp | 0,94 |
| ent ub + pres (*dør*) | 16,8 / 10,1 pp | 66 / 80 % | −13,2 pp | 0,88 |

- **Leksemet i flertall:** med log-regresjon er det riktig i omtrent 4 av 5 tilfeller.
- **Andelene:** de bommer med 10–15 pp i median, og 90-persentilen ligger rundt 30 pp. Når fasiten ligger mellom 20 og 80 %, er medianfeilen 13–14 pp.
- **Skjevheten i reglene forklarer to tidligere observasjoner:**
  - *dør:* for denne typen (ent ub + pres) undervurderer reglene substantivandelen med 13 pp i median. Anslaget på 71 % substantiv for «dør» (`rapport_verbtyper.md` §7.2) er derfor trolig for lavt.
  - *landet:* for denne typen (ent be + pret) blir summen av de ukappede anslagene 1,9 × observert, fordi både `ent be` og `pret` overvurderes med omtrent en faktor 2.
- **Kalibrering:** med log-regresjon ligger summen av anslagene på 0,9–1,0 × observert (median).

## 4. «fisker» over tid: forholdstallene må læres i samme korpus

`sqlite/decompose_fisker.py` lærer forholdstallene på `nb_totals`. Når de brukes år for år på bokkorpuset, blir summen av de ukappede anslagene median 2,0 × observert. Årsaken er at forholdet mellom formene ikke er det samme i bøker og aviser. *fiskene* er for eksempel relativt nesten dobbelt så vanlig i bøker: andelen av treffene som er i bokkorpuset er 0,27 for *fiskene*, mot 0,16 for *fisker*. `book_decomposition()` lærer derfor forholdstallene i bokkorpuset, med log-regresjon på 5 799 gullstandard-substantiv og forholdet presens / s-passiv for aktivitetsverb.

| Andel av «fisker» 1950 / 2020 | Lært i hele NB-korpuset | Lært i bokkorpuset |
| :--- | :---: | :---: |
| *en fisker* | 57 / 51 % | 21 / 14 % |
| *fisk* (flertall) | 33 / 42 % | 57 / 74 % |
| *å fiske* (presens) | 11 / 7 % | 22 / 12 % |
| Sum anslag / observert (median) | 2,0 | 1,3 |

Hvilken referansegruppe man bruker, betyr enda mer. Med forholdstall lært i bokkorpuset blir anslaget for *en fisker* (hele perioden) slik:

| Referansegruppe | Log-regresjon | Medianforhold |
| :--- | ---: | ---: |
| Alle gullstandard-substantiv | 39 000 | 322 000 |
| -er-personord (361 lemmaer) | 59 000 | 266 000 |

Til sammenligning er det observert 224 000 forekomster av «fisker» i alt. Nivået for *fisker* er altså ikke bestemt av dataene. Det eneste som holder i begge variantene, er at andelen *fisk* (flertall) øker over perioden.

## 5. Konklusjon for foredraget

- Metoden finner riktig leksem i flertall for omtrent 80 % av de kunstige homografene. Prosentandelene bør vises med en usikkerhet på minst ±10–15 pp.
- Log-regresjon på de øvrige formene i paradigmet er bedre enn de faste reglene i `decomposer.py` og er ikke skjev. Reglene bør byttes ut, og forholdstallene bør læres i samme korpus som de brukes på.
- Enkeltord med uvanlige profiler, som *fisker* med svært mye flertall, er ekstra følsomme for valget av referansegruppe.

## 6. Begrensninger

- Gullstandarden består av høyfrekvente, entydige lemmaer. Ekte homografer kan ha andre profiler, for eksempel fordi sjeldne ordbokshomografer er overrepresentert.
- De kunstige homografene parer tilfeldige substantiv og verb. Ekte homografpar kan være korrelerte, for eksempel i semantikk eller frekvens.
- Testen er gjort på `nb_totals`. Bokkorpuset er ikke validert på samme måte.
