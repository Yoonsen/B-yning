# Rapport: Stabilitet over tid med flertydige former fordelt etter OBT

*Delrapport i MONS-prosjektet, 2026-11-23. Tallene gjenskapes med `python -m sqlite.stabilitet_obt`.
Resultatene for hele korpuset står i `resultater/alle_lag/stabilitet_obt_*.tsv`, og for lag 1 i
`resultater/stabilitet_obt_*.tsv`. Arbeidslogg: `logg.md`, del 45 (lag 1) og 65–66 (alle lag).*

---

## 1. Spørsmål

Er bøyningsprofilene stabile over tid? N-gram-dataene (NB, bøker 1950–2020) teller ordformer. For ord
med flertydige former (*dør*, *døde*, *satt*) må formtallene fordeles på leksemene før profilen kan
regnes ut. Denne analysen bruker det OBT-taggede korpuset til fordelingen, **per tiår**, slik at
fordelingen selv kan endre seg over tid.

## 2. Metode

For hvert eksempellemma (leksem = grunnform + ordklasse):

1. **Kjernekategoriene** i paradigmet:
   - verb: infinitiv, presens, preteritum, perfektum partisipp og imperativ;
   - substantiv: entall og flertall, ubestemt og bestemt.

   Kategorier som deler form innen leksemet (f.eks. infinitiv/imperativ), slås sammen.
2. **Entydige former** (bare dette leksemet i Ordbanken): årlige frekvenser rett fra n-gram for bøker
   (bokmål).
3. **Flertydige former:** n-gram-frekvensen × leksemets andel av formen i det OBT-taggede korpuset,
   regnet ut fra bøkene (skjønn- og faglitteratur) i samme tiår.
   - Under 30 koblede forekomster i tiåret: andelen for hele perioden brukes.
   - Aviser er holdt utenfor, fordi n-gram for aviser ikke kan avgrenses til bokmål (logg del 45).

Fire varianter sammenlignes:

| variant | fordeling av flertydige former |
|---|---|
| OBT per tiår | andel fra OBT i samme tiår (hovedvarianten) |
| OBT fast | én andel fra OBT for hele perioden; antar at fordelingen ikke endrer seg |
| decomposer | `decomposer.py` (regler) på n-gram-tallene per tiår |
| naiv | ingen fordeling, rå formfrekvens |

**Stabilitetsmål:** gjennomsnittlig endring mellom profilene i to påfølgende tiår (total
variasjonsavstand i prosentpoeng), og største avvik fra gjennomsnittsprofilen.

Eksempellemmaer:
- substantiv: *fisk*, *fisker*, *dør*, *krone*;
- verb: *dø*, *gå*, *svare*, *sette*, *bygge*.

## 3. Lag 1 var for lite

Med bare lag 1 (222 dokumenter, 6–10 bøker per teksttype og tiår) svingte OBT-andelene for de
flertydige formene mye mellom tiårene. Svingningene skyldtes i stor grad hvilke bøker som var med:
- Innenfor ett tiår varierte andelen av *satt* som tilhører *sette*, fra 6 til 78 % mellom bøkene.
- Fordelingen per tiår gjorde derfor profilene *mindre* stabile enn rå formtall, særlig for *sette*
  og *dø*. Det var målestøy, ikke språkendring.

Analysen ble lagt til side (logg del 45) til korpuset ble utvidet til fem lag (logg del 46 og 64).

## 4. Resultater med hele korpuset (lag 1–5)

1 076 taggede dokumenter, 32–47 bøker per teksttype og tiår.

### 4.1 Andelene per tiår er mye mindre støyete

Spennet i OBT-andelen over de åtte tiårene:

| form | leksem | lag 1 | alle lag |
|---|---|---|---|
| *satt* | *sette* (mot *sitte*) | 19–43 % | 29–38 % |
| *dør* | *dø* (mot subst *dør*) | 33–72 % | 42–53 % |
| *dør* | subst *dør* | 28–67 % | 47–58 % |
| *svart* | *svare* (mot adj *svart*) | 6–29 % | 10–23 % |
| *døde* | *dø* (mot adj *død*) | 58–87 % | 60–68 %, unntatt 2000-tallet (83 %) |
| *går* | *gå* (mot subst «i går») | 91–96 % | 91–96 % |
| *kroner* | *krone* (subst) | 96–99 % | 98–100 % |

**Én bok kan fortsatt styre et tiår.** På 2000-tallet står én slektsbok (faglitteratur) for 57 % av
alle forekomstene av *døde* i bøkene, nesten bare som verb («døde i 1823»). Andelen for det tiåret blir
derfor 83 %.

*fisker* er fortsatt for sjelden (35–253 koblede forekomster per tiår). Andelen som tilhører substantivet
*fisker*, varierer fra 13 til 49 %.

### 4.2 Stabilitet per lemma

Snitt endring mellom tiår / største avvik fra snittprofilen, i pp:

| lemma | flertydige former | OBT per tiår | OBT fast | decomposer | naiv |
|---|---|---|---|---|---|
| *fisk* | fisk, fiskene, fisker | 2,2 / 2,5 | 1,7 / 2,2 | 2,7 / 4,9 | 3,2 / 9,8 |
| *fisker* | fisker | 8,3 / 11,7 | 4,2 / 5,5 | 4,1 / 7,3 | 5,8 / 8,0 |
| *dør* (subst) | dør | 2,8 / 5,9 | 2,9 / 5,8 | 3,3 / 6,8 | 3,4 / 6,9 |
| *krone* | krona, krone, kroner | 1,4 / 5,7 | 1,4 / 5,6 | 1,8 / 7,1 | 1,4 / 5,7 |
| *dø* | døde, dør | 4,6 / 5,1 | 2,2 / 3,8 | 1,9 / 2,9 | 2,0 / 3,7 |
| *gå* | går | 2,1 / 5,1 | 2,1 / 4,8 | 2,1 / 4,9 | 2,1 / 4,9 |
| *svare* | svar, svare, svarer, svart, svarte | 4,7 / 8,4 | 3,4 / 6,1 | 3,6 / 5,7 | 4,1 / 8,6 |
| *sette* | satt, satte, sett, sette, setter | 7,7 / 10,6 | 6,6 / 9,9 | 6,3 / 8,5 | 5,3 / 7,4 |
| *bygge* | bygd, bygg, bygger, bygget | 4,3 / 10,3 | 3,6 / 9,4 | 3,5 / 6,6 | 3,5 / 9,3 |

**Hvor mye støy fordelingen per tiår tilfører:** forskjellen mellom «OBT per tiår» og «OBT fast».

| lemma | lag 1 (per tiår / fast) | alle lag (per tiår / fast) |
|---|---|---|
| *sette* | 10,4 / 6,6 | 7,7 / 6,6 |
| *dør* (subst) | 3,8 / 2,9 | 2,8 / 2,9 |
| *dø* | 5,1 / 2,2 | 4,6 / 2,2 |
| *fisker* | 5,9 / 3,3 | 8,3 / 4,2 |

- For *sette* og *dør* er det meste av ekstrastøyen borte.
- For *dø* skyldes resten 2000-tallet (slektsboka).
- *fisker* er fortsatt for sjelden.

### 4.3 Utviklingstrekk som er robuste

Disse mønstrene er like i alle fire variantene. De avhenger altså ikke av hvordan de flertydige formene
fordeles. Andel i prosent, OBT per tiår:

| lemma | kategori | 1950 | 1960 | 1970 | 1980 | 1990 | 2000 | 2010 | 2020 |
|---|---|---|---|---|---|---|---|---|---|
| *gå* | preteritum | 41 | 38 | 34 | 33 | 33 | 34 | 38 | 39 |
| *gå* | presens | 25 | 29 | 31 | 31 | 31 | 31 | 27 | 27 |
| *krone* | ubestemt flertall | 81 | 82 | 85 | 88 | 89 | 89 | 90 | 89 |
| *dør* (subst) | bestemt entall | 71 | 69 | 68 | 65 | 68 | 72 | 76 | 75 |
| *dør* (subst) | ubestemt entall | 16 | 16 | 17 | 18 | 17 | 14 | 12 | 13 |
| *sette* | preteritum | 32 | 24 | 20 | 16 | 22 | 19 | 29 | 34 |
| *sette* | infinitiv | 29 | 29 | 36 | 38 | 36 | 37 | 28 | 25 |
| *fisk* | ubestemt entall | 67 | 66 | 69 | 68 | 70 | 68 | 68 | 70 |

- ***gå* og *sette*:** preteritum går ned fram til 1980–90-tallet og opp igjen etter 2000. Presens
  eller infinitiv beveger seg motsatt. Det kan henge sammen med hvor stor andel av bøkene som er
  fortellende tekst i preteritum.
- ***krone*:** ubestemt flertall (*kroner*) øker jevnt fra 81 til 89 %.
- ***dør*:** bestemt entall (*døra/døren*) øker etter 2000.
- ***fisk*:** stabil profil. Med rå formtall er ubestemt entall bare 52–61 %, fordi *fisker* telles som
  flertall av *fisk*. Fordelingen er altså avgjørende for nivået, men ikke for stabiliteten.

Profilen for *dø* er stabil innenfor støyen: preteritum 58–67 %, infinitiv 17–24 % og presens 12–17 %.

## 5. Forbehold

- **Boka er enheten.** Forekomster i samme bok er ikke uavhengige av hverandre. Wilson-intervallene i
  `stabilitet_obt_andeler.tsv` er regnet per forekomst og er derfor for smale. Usikkerhet med
  bootstrap over dokumenter er ikke gjort.
- **N-gram er for bøker generelt**, mens OBT-andelene er fra et utvalg skjønn- og faglitteratur.
  Sammensetningen kan avvike.
- **N-gram teller formene med små bokstaver.** Former med stor forbokstav (f.eks. først i setningen)
  er ikke med.
- **Aviser er ikke med** (se §2).
- **Decomposer-varianten** bruker reglene, ikke log-regresjonen.

## 6. Konklusjon

- Med det utvidede korpuset kan fordelingen per tiår brukes for de vanlige flertydige formene.
  Noen utviklingstrekk i bøyningsprofilene er robuste, uavhengig av hvordan de flertydige formene
  fordeles (*gå*, *sette*, *krone*, *dør*).
- For sjeldne former (*fisker*) og tiår der én bok dominerer (*døde* på 2000-tallet) er fordelingen per
  tiår fortsatt usikker. Der er én fast andel et bedre valg.
- Bootstrap over dokumenter vil vise hvilke endringer som er større enn variasjonen mellom bøkene.

## 7. Gjenskaping

```bash
python -m sqlite.stabilitet_obt                                   # lag 1 (korpus/obt_frekvenser.db)
python -m sqlite.stabilitet_obt --db <alle lag> --ut resultater/alle_lag
```
