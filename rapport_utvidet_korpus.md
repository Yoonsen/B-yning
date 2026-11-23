# Rapport: Analysene på nytt med det utvidede korpuset (lag 1–5)

*Delrapport i MONS-prosjektet, 2026-11-23. Analysene i `rapport_morfologisk_variasjon.md`,
`rapport_dekomponering_obt.md` og stabilitetsanalysen (logg del 45) er kjørt på nytt på hele det
OBT-taggede korpuset. Arbeidslogg: `logg.md`, del 64–65. Resultatfilene står i `resultater/alle_lag/`.
Resultatene for lag 1 i `resultater/` er ikke endret.*

---

## 1. Data

- **Korpus.** Det utvidede korpuset (logg del 46) har 1 097 dokumenter i fem lag. Hvert lag er balansert
  på 3 teksttyper × 8 tiår (1950–2026). **1 076 dokumenter er tagget** (logg del 64).
  - 21 dokumenter (1,8 % av ordene) fikk tidsavbrudd i `mtag.py`. De er spredt over teksttyper og tiår,
    og ingen celle mister mer enn 7,4 %.
  - Det taggede korpuset har 43,7 mill. tokens, hvorav 41,3 mill. med minst én bokstav. Lag 1 alene
    hadde 8,4 mill.
- **Kobling mot Ordbanken.** Andelene er praktisk talt de samme som for lag 1: eksakt for substantiv
  80,5 %, verb 90,6 % og adjektiv 90,0 %.
- **Hvor databasen ligger.** Databasen med alle lag, `obt_frekvenser_alle_lag.db` (1,37 GB, bare
  telletall), ligger utenfor repoet. Den finnes på Linux-maskinen og som kopi på Windows-maskinen.
  Delingsdatabasen i repoet (`korpus/obt_frekvenser.db`) har fortsatt bare lag 1 (logg del 62).

## 2. Morfologisk variasjon

`python -m sqlite.morfologisk_variasjon --db <alle lag> --utvalg 200000`. Med samme utvalgsstørrelse
som i `rapport_morfologisk_variasjon.md` kan tallene sammenlignes direkte.

| | lag 1 (8,4 mill.) | alle lag (41,3 mill.) |
|---|---|---|
| former per lemma, alle ord (hele korpuset) | 1,13 | 1,10 |
| former per lemma, subst/verb/adj (hele korpuset) | 1,39 | 1,35 |
| andel bøyde tokens, alle ord | 0,30 | 0,30 |
| andel bøyde tokens, subst/verb/adj | 0,58 | 0,58 |
| andel bøyde tokens, verb | 0,79 | 0,79 |
| former per lemma, lemmaer med 1000+ forekomster (subst / verb / adj) | 6,3 / 6,3 / 5,2 | 7,1 / 6,7 / 4,8 |

- **Andelen bøyde tokens er helt stabil.** I løpende tekst står 30 % av ordene i en annen form enn
  oppslagsformen, uansett korpusstørrelse.
- **Forholdet former/lemma synker litt med korpusstørrelsen** (1,13 → 1,10). Stadig nye sjeldne ord med
  én form kommer til. Det bekrefter at tallet mest måler hvor mange sjeldne ord det er, og at det
  avhenger av korpusstørrelsen. Det må tas med i en sammenligning med andre undersøkelser (f.eks. 1,2).
- **Teksttype og tiår** (typer ved 200 000 tokens) gir samme bilde som før:
  - skjønnlitteratur har mest bøyning (andel bøyd 0,33) og aviser minst (0,26);
  - over tid er tallene stabile (0,29–0,31).
- **Aviser:** andelen bøyde ord faller fra 0,28 (1950-tallet) til 0,22 (2020-tallet). Med fem ganger så
  mange avisnumre er tendensen fra lag 1 (0,28 → 0,23) bekreftet.

## 3. Decomposer mot OBT

`python -m sqlite.valider_dekomponering_obt --db <alle lag> --ut resultater/alle_lag`. Decomposer er i
versjonen fra 2026-11-21: adjektivankre, flertydighet per leksem og delte former vektet etter entydig
bruk (logg del 47–56).

**Samme former, samme kodeversjon.** For å skille effekten av korpusstørrelsen fra endringene i
decomposer er lag 1 kjørt på nytt med samme kode, og de 1 722 innholdsordformene som finnes i begge
kjøringene, er sammenlignet:

| | lag 1 | alle lag |
|---|---|---|
| median avvik, logreg | 13,7 pp | 13,1 pp |
| riktig leksem størst, logreg | 74 % | 75 % |
| median avvik, regler | 18,5 pp | 17,4 pp |

**Korpusstørrelsen endrer nesten ikke hvor godt decomposer treffer i gjennomsnitt.** Log-regresjonen
er tydelig bedre enn reglene i begge (13 mot 18 pp). Det var den ikke i den første kjøringen
(`rapport_dekomponering_obt.md` §3), fordi kollegaens endringer gjør at log-regresjonen kan brukes
oftere.

**Bredt utvalg med alle lag:**
- 4 170 innholdsordformer har minst 100 forekomster (mot 1 721 i lag 1). Mange av dem er sjeldnere
  former.
- Når alle kandidatene er modellert (3 282 former): median avvik 10,4 pp og riktig leksem størst
  i 78 %.
- Når minst 5 % av forekomstene går til et umodellert leksem (888 former): fortsatt 50 pp.
- Med minst 500 forekomster (1 679 former, sammenlignbart med terskelen 100 i lag 1): median 12,5 pp
  og 75 % riktig.

**Enkeltformer kan endre seg mye selv om gjennomsnittet står stille.** Både fasiten og decomposer
flytter seg:

| form | OBT lag 1 | OBT alle lag | decomposer lag 1 | decomposer alle lag |
|---|---|---|---|---|
| *fisker* | verb 74, *fisker* 19, *fisk* 8 | verb 57, *fisker* 33, *fisk* 10 | verb 59, *fisk* 21, *fisker* 19 | *fisk* 50, verb 26, *fisker* 23 |
| *kroner* | subst 99 | subst 99 | subst 74, verb 26 | subst 59, verb 41 |
| *dør* | verb 52, subst 48 | 50 / 50 | subst 71 | subst 76 |
| *døde* | verb 72, adj 28 | verb 71, adj 29 | verb 71, adj 29 | verb 65, adj 33 |

- Fasiten for *fisker* var ikke stabil i lag 1 (367 forekomster).
- Decomposer lærer forholdstallene fra korpuset og bruker korpusets frekvenser for ankerformene, så
  anslagene for enkeltord avhenger av hvilket korpus den kjøres på. For *kroner* og *fisker* går
  anslagene lenger bort fra fasiten med mer data.
- *døde* treffer godt etter at adjektivankrene kom inn (avvik 5 pp).

**Profiler (alle lag)** gir samme mønster som før:
- substantivprofilene blir bedre med decomposer enn med rå formtall (*fisker* 5,2 mot 23,1 pp; *fisk*
  7,9 mot 15,9);
- verbprofilene er blandet: *dø* er nå bedre enn rå tall (6,5 mot 7,4); *legge* (25,0 mot 10,1) og
  *stille* (41,7 mot 37,4) er dårligere.

## 4. Stabilitet over tid

`python -m sqlite.stabilitet_obt --db <alle lag> --ut resultater/alle_lag`. Metoden er som i logg
del 45: n-gram for bøker 1950–2020, der flertydige former fordeles med OBT-andelen fra bøkene i samme
tiår. Hver celle (teksttype × tiår) har nå 32–47 bøker, mot 6–10 i lag 1.

**Andelene per tiår er mye mindre støyete.** Spennet over de åtte tiårene:

| form | leksem | lag 1 | alle lag |
|---|---|---|---|
| *satt* | *sette* (mot *sitte*) | 19–43 % | 29–38 % |
| *dør* | *dø* (mot subst *dør*) | 33–72 % | 42–53 % |
| *dør* | subst *dør* | 28–67 % | 47–58 % |
| *svart* | *svare* (mot adj *svart*) | 6–29 % | 10–23 % |
| *døde* | *dø* (mot adj *død*) | 58–87 % | 60–68 %, 2000-tallet 83 % |

**Støyen fra fordelingene er mindre.** Forskjellen mellom å fordele per tiår (`obt_tiaar`) og med én
fast andel (`obt_fast`) viser hvor mye svingningene i andelene bidrar til ustabiliteten i profilen
(snitt endring mellom tiår, pp):

| lemma | lag 1: per tiår / fast | alle lag: per tiår / fast |
|---|---|---|
| *sette* | 10,4 / 6,6 | 7,7 / 6,6 |
| *dør* (subst) | 3,8 / 2,9 | 2,8 / 2,9 |
| *dø* | 5,1 / 2,2 | 4,6 / 2,2 |
| *fisker* (subst) | 5,9 / 3,3 | 8,3 / 4,2 |

- For *sette* og *dør* er det meste av ekstrastøyen borte.
- **Én bok kan fortsatt styre et tiår.** For *dø* skyldes resten 2000-tallet: én slektsbok (faglitteratur)
  står for 57 % av alle forekomstene av *døde* i bøkene fra 2000-tallet, nesten bare som verb
  («døde i 1823»).
- *fisker* er fortsatt for sjelden (35–253 koblede forekomster per tiår) til at andelen er stabil.

**Utviklingstrekk som er robuste** (samme mønster med OBT per tiår, fast andel, decomposer og rå
formtall):
- *gå*: preteritum går ned fra 41 % (1950-tallet) til 33 % (1980–90-tallet) og opp igjen til 39 %
  (2020). Presens beveger seg motsatt.
- *krone*: ubestemt flertall stiger fra 81 til 89 %.
- *dør* (subst): bestemt entall ligger på 65–72 % fram til 2000-tallet og stiger til 75–76 % på 2010-
  og 2020-tallet. Ubestemt entall faller fra 16–18 % til 12–13 %.
- *sette*: preteritum faller fra 32 % til 16 % på 1980-tallet og stiger til 34 % (2020), mens
  infinitiv beveger seg motsatt.
- *fisk*: profilen er stabil, med ubestemt entall 66–70 % (OBT). Rå formtall gir 52–61 %, fordi
  *fisker* (flertall) blir overtelt.

## 5. Konklusjoner

1. **Morfologisk variasjon:** andelen bøyde ord (30 %, verb 79 %) er robust. Forholdet former/lemma
   avhenger av korpusstørrelsen og må alltid oppgis sammen med den.
2. **Decomposer:** treffer like godt i gjennomsnitt med fem ganger så mye data (13 pp median, 75 %
   riktig). Enkeltanslag kan likevel endre seg mye, så andeler for enkeltord bør vises med usikkerhet.
3. **Stabilitet:** det utvidede korpuset gjør fordelingen per tiår brukbar for flere former, f.eks.
   *satt* og *dør*. Enkeltbøker kan fortsatt dominere en form i et tiår (*døde* på 2000-tallet), og
   sjeldne former (*fisker*) er fortsatt usikre. Usikkerhet med boka som enhet (bootstrap over
   dokumenter) vil vise hvilke endringer som er større enn variasjonen mellom bøkene. Det er ikke
   gjort.

## 6. Gjenskaping

```bash
DB=/sti/til/obt_frekvenser_alle_lag.db
python -m sqlite.morfologisk_variasjon --db $DB --utvalg 200000
python -m sqlite.valider_dekomponering_obt --db $DB --ut resultater/alle_lag
python -m sqlite.stabilitet_obt --db $DB --ut resultater/alle_lag
```

Kjøretid på en vanlig PC: ca. 6, 13 og under 1 minutt. Analysen av morfologisk variasjon bruker ca.
1,6 GB minne.
