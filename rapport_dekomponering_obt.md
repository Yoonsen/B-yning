# Rapport: Decomposer mot et tagget korpus

*Delrapport i MONS-prosjektet. Utfyller `rapport_dekomponering_validering.md`. Tallene gjenskapes med
`python -m sqlite.valider_dekomponering_obt` (med `--db` for hele korpuset). Resultatene per form og
per profil står i `resultater/alle_lag/` (hele korpuset) og `resultater/` (lag 1, kjøringen i §4.2).
Arbeidslogg: `logg.md`, del 40–42 (første kjøring), 52 og 55–56 (forbedringer i decomposer) og
64–66 (hele korpuset).*

---

## 1. Spørsmål

N-gram-dataene teller ordformer. For å lage bøyningsprofiler for ord med flertydige former (*fisker*,
*dør*, *døde*) må formtallene fordeles på leksemene. Decomposer (`sqlite/decomposer.py`) anslår
fordelingen ut fra de øvrige formene i hvert kandidatparadigme.

`rapport_dekomponering_validering.md` tester metoden på kunstige homografer laget av
gullstandardlemmaer. Der er fasiten eksakt, men alle formene i paradigmene er entydige. Denne
rapporten tester decomposer på **ekte** flertydige former, med fasit fra et tagget korpus.

Vi spør:

1. Hvor godt fordeler decomposer ekte flertydige former på leksemer?
2. Hvorfor bommer den når den bommer?
3. Blir bøyningsprofilene bedre med decomposer enn med rå formtall?

## 2. Data og metode

- **Korpus og fasit, tagget i to omganger.** Et bokmålskorpus balansert på 3 teksttyper
  (skjønnlitteratur, faglitteratur, aviser) × 8 tiår (1950–2026), tagget med Oslo-Bergen-taggeren
  (multitagger, CG-3 og OBT-Stat). OBT velger analyse ut fra konteksten, og analysene er koblet til
  lemma_id i Norsk Ordbank (logg del 34). OBT er ikke en perfekt fasit, se §7.

  | | dokumenter tagget | tokens | database |
  |---|---|---|---|
  | **lag 1–5** (hele korpuset, hovedresultatene i §3) | 1 076 av 1 097 | 43,7 mill. | `obt_frekvenser_alle_lag.db`, utenfor repoet (logg del 67) |
  | lag 1 (første korpus, §4–5) | 222 av 224 | 8,8 mill. | `korpus/obt_frekvenser.db` (Git LFS) |

- **Rekkefølgen arbeidet ble gjort i:**
  1. Første kjøring på lag 1 (2026-11-20, §5).
  2. Decomposer forbedret på grunnlag av den: adjektivankre, nedvekting av sjeldne homografer og
     flertydighet regnet per leksem (2026-11-21, §4).
  3. Kjøring på hele korpuset med den forbedrede decomposer (2026-11-23, §3).
- **Decomposer** kjøres på de samme korpustallene: formfrekvensene i korpuset brukes som `nb_totals`.
  - Log-regresjonen lærer på gullstandardprofiler med frekvenser fra korpuset. Gullstandardlemmaene
    velges som i decomposer.py med NBs `nb_totals` (logg del 41).
  - Begge metodene testes: `regler` (de faste forholdstallene) og `logreg` (standard fra 2026-11-20).
- **Sammenligningsenhet** er leksemet (grunnform + ordklasse). Homografe oppføringer i Ordbanken slås
  sammen. OBT-analyser som ikke er koblet til Ordbanken (OCR-feil, ukjente ord), er holdt utenfor
  fordelingen.
- **Mål per form:**
  - *avvik* (pp): hvor mange prosentpoeng som er fordelt på feil leksem (total variasjonsavstand).
    For to kandidater er det det samme som feilen i den ene andelen, altså samme mål som i test 2 i
    `rapport_dekomponering_validering.md`.
  - *riktig flest*: decomposer gir størst andel til samme leksem som OBT.
  - *umodellert*: andelen (ifølge OBT) som går til leksemer decomposer gir 0 %, f.eks. adjektiv,
    andre ordklasser eller «i går». Slike feil kan ikke rettes med bedre forholdstall.
  - *grunnlag*: summen av decomposerens anslag delt på observert frekvens. Nær 0 betyr at decomposer
    har lite å regne ut fra, og at fordelingen i praksis bestemmes av normaliseringen.
- **Utvalg:**
  - *Bred del:* alle ordformer med minst 100 forekomster i korpuset der Ordbanken har minst to ulike
    leksemer blant substantiv, verb og adjektiv: 4 245 former i hele korpuset (1 775 i lag 1).
  - *Hovedutvalget* er formene der OBT gir minst 90 % substantiv, verb eller adjektiv: 4 170 (lag 1:
    1 721). Det holder småord som *for*, *men* og *nå* utenfor; decomposer er ikke laget for dem.
  - *Dyp del:* 12 former fra repoet (logg del 40) og profiler for 18 lemmaer.

## 3. Hovedresultater: hele korpuset (lag 1–5)

Kjørt 2026-11-23 med decomposer i versjonen etter §4.

**Fem ganger så mye data endrer nesten ikke hvor godt decomposer treffer.** For å skille effekten
av korpusstørrelsen fra endringene i decomposer er lag 1 kjørt på nytt med samme kode (ikke lagret).
De 1 722 innholdsordformene som finnes i begge kjøringene, er sammenlignet:

| | lag 1 | lag 1–5 |
|---|---|---|
| median avvik, logreg | 13,7 pp | 13,1 pp |
| riktig leksem størst, logreg | 74 % | 75 % |
| median avvik, regler | 18,5 pp | 17,4 pp |
| riktig leksem størst, regler | 70 % | 70 % |

Log-regresjonen er klart bedre enn reglene (13 mot 18 pp). I første kjøring (§5) var de like, fordi
log-regresjonen sjelden kunne brukes. Endringene i §4 gjør at den brukes oftere.

**Bredt utvalg (logreg):**

| utvalg | former | tokens | median avvik | vektet avvik | 90-persentil | riktig flest |
|---|---|---|---|---|---|---|
| innholdsord | 4 170 | 5 711 534 | 16,5 pp | 25,8 pp | 74,1 pp | 73 % |
| alle kandidater modellert (umodellert < 5 %) | 3 282 | 4 298 653 | **10,4 pp** | 14,7 pp | 59,8 pp | **78 %** |
| … grunnlag ≥ 0,5 | 1 755 | 1 486 098 | 9,6 pp | 13,1 pp | 50,0 pp | 80 % |
| … grunnlag < 0,5 | 1 527 | 2 812 555 | 11,4 pp | 15,5 pp | 68,3 pp | 74 % |
| umodellert ≥ 5 % | 888 | 1 412 881 | **50,0 pp** | 59,8 pp | 97,8 pp | **54 %** |

«Vektet» er vektet med antall forekomster av formen.

- **Når alle kandidatene er modellert,** gir decomposer riktig leksem størst andel for 78 % av
  formene, med medianavvik 10 pp. Det er omtrent som i den syntetiske testen (§6). Med mer å regne ut
  fra (grunnlag ≥ 0,5) blir det 80 %.
- **Den største feilkilden er fortsatt kandidater decomposer ikke modellerer:** 888 former, 25 % av
  forekomstene, med 50 pp i median. Det gjelder særlig adjektiv uten entydige ankre og «i går» (§4.1).
- **Mange sjeldnere former kommer med.** Med minst 100 forekomster er formene mange flere og
  sjeldnere enn i lag 1 (4 170 mot 1 721), og medianen for alle innholdsord blir høyere. Med minst
  500 forekomster (1 679 former, omtrent like vanlige som terskelen 100 i lag 1) er medianen 12,5 pp
  og 75 % riktig.

**Utvalgte former.** Andel i prosent for leksemet OBT gir størst andel. «Decomposer lag 1» er
kjøringen på lag 1 med samme kode. Både fasiten og decomposer kan flytte seg med mer data:

| form | n (alle lag) | OBT lag 1 | OBT alle lag | decomposer lag 1 | decomposer alle lag | avvik alle lag |
|---|---|---|---|---|---|---|
| *hatt* | 13 832 | *ha* 95 | *ha* 95 | 92 | 94 | 1,3 |
| *ønsker* | 10 542 | verb 93 | verb 91 | 94 | 93 | 1,4 |
| *dager* | 11 715 | *dag* 100 | *dag* 100 | 96 | 95 | 4,6 |
| *døde* | 7 940 | verb 72, adj 28 | verb 71, adj 29 | 71 / 29 | 65 / 33 | 5,2 |
| *landet* | 9 649 | *land* 85 | *land* 87 | 90 | 92 | 5,4 |
| *viser* | 12 769 | verb 94 | verb 94 | 98 | 99 | 5,9 |
| *møter* | 4 910 | verb 72 | verb 70 | 65 | 61 | 8,3 |
| *går* | 39 663 | *gå* 85 | *gå* 85 | 100 | 100 | 15,1 |
| *dør* | 2 865 | verb 52 | verb 50 | 29 | 24 | 25,1 |
| *tro* | 9 584 | verb 60 | verb 58 | 89 | 88 | 34,0 |
| *kroner* | 14 730 | subst 99 | subst 99 | 74 | 59 | 39,7 |
| *fisker* | 959 | verb 74, *fisker* 19, *fisk* 8 | verb 57, *fisker* 33, *fisk* 10 | verb 59, *fisk* 21 | *fisk* 50, verb 26 | 41,1 |

- OBT-fordelingen er stabil for de hyppige formene. For *fisker* (367 forekomster i lag 1) var den
  ikke det.
- Decomposer lærer forholdstallene fra korpuset og bruker korpusets frekvenser for ankerformene. Derfor
  kan anslagene for enkeltord endre seg mye selv om gjennomsnittet står stille. For *kroner* og
  *fisker* er de blitt dårligere.
- *dør*: OBT gir om lag 50/50, mens decomposer gir substantivet 76 %.

**Profiler.** Bøyningsprofiler (kjernekategorier) i tre varianter:
- *OBT*: fasit fra det taggede korpuset;
- *decomposer*: hver forms frekvens × decomposerens andel for leksemet;
- *naiv*: rå formfrekvens uten fordeling, slik n-gram gir.

Kategorier som deler form innen samme leksem (f.eks. infinitiv/imperativ, preteritum/perfektum
partisipp i svake verb), er slått sammen, fordi decomposer bare fordeler mellom leksemer. Avviket er
hvor mange prosentpoeng av profilen som er feilplassert:

| lemma | decomposer | naiv | lemma | decomposer | naiv |
|---|---|---|---|---|---|
| *fisker* (subst) | **5,2** | 23,1 | *dø* | **6,5** | 7,4 |
| *fisk* (subst) | **7,9** | 15,9 | *gå* | 3,4 | 3,4 |
| *dør* (subst) | **4,5** | 8,3 | *tro* | **7,2** | 9,7 |
| *krone* (subst) | 2,4 | **1,1** | *svare* | **11,6** | 26,6 |
| *land* (subst) | **0,5** | 2,4 | *sette* | **13,7** | 37,0 |
| *bygge* | **3,0** | 9,9 | *legge* | 25,0 | **10,1** |
| *selge* | **4,4** | 4,6 | *stille* | 41,7 | **37,4** |
| *leve* | 5,0 | **1,6** | *tape* | **28,6** | 30,3 |
| *vinne* | 16,4 | **10,0** | *fiske* | **26,6** | 41,7 |

- **Substantiv:** decomposer forbedrer profilene klart. For *fisker* og *fisk* er forskjellen fra rå
  formtall stor.
- **Verb:** blandet resultat.
  - Decomposer hjelper mest der en imperativ kolliderer med et substantiv eller et partisipp
    (*sett*, *svar*).
  - *dø* er bedre enn rå tall etter adjektivankrene.
  - Rå tall er bedre for *legge*, *vinne* og *stille* (uvanlig profil, eller konkurrent som ikke
    modelleres).
  - *tape* viser at imperativregelen kan gi en kollisjon med et substantiv (*tap*) altfor stor vekt.

**Konklusjon.**
- Med 43,7 mill. tokens treffer decomposer omtrent like godt i gjennomsnitt som med lag 1 (13 pp
  median, 75 % riktig).
- Feilkildene er de samme: umodellerte kandidater, lite grunnlag og ord med uvanlige profiler.
- Enkeltanslag kan endre seg mye med korpuset, så andeler for enkeltord bør vises med usikkerhet.

## 4. Forbedringer i decomposer underveis (lag 1, 2026-11-21)

*Arbeid gjort av Lars, med utgangspunkt i første kjøring (§5). Tallene er fra lag 1.*

### 4.1 Adjektivankre

**Hva er endret.** Decomposer har nå en gullstandard for adjektiv (`sqlite/adjektiv_gold.py`): vanlige adjektiv der m/f, e-form og nøytrum er entydige. E-formen (*store*) anslås med log-regresjon fra de entydige positivformene. Ett anker er nok for adjektiv. Gullstandarden velges med NBs `nb_totals`, som for substantiv og verb, og frekvensene hentes fra korpuset (`korpus_profiler._corpus_gold_profiles`). Reglene (`regler`) er uendret.

**Bred del, innholdsord (1 721 former), logreg:**

| utvalg | former | median avvik | vektet avvik | 90-persentil | riktig flest |
|---|---|---|---|---|---|
| alle innholdsord, før | 1 721 | 18,4 pp | 29,4 pp | 90,4 pp | 69 % |
| alle innholdsord, nå | 1 721 | **13,9 pp** | **26,1 pp** | **80,7 pp** | **73 %** |
| alle kandidater modellert, nå | 1 321 (før 1 206) | 7,9 pp | 14,9 pp | 62,3 pp | 80 % |
| … med grunnlag ≥ 0,5 | 581 | 6,5 pp | 12,9 pp | 52,3 pp | 83 % |
| … med grunnlag < 0,5 | 740 | 9,1 pp | 15,9 pp | 70,1 pp | 77 % |
| umodellert ≥ 5 %, nå | 400 (før 515) | 50,0 pp | 57,9 pp | 98,9 pp | 51 % |

- 115 flere former har nå alle kandidatene modellert. Andelen forekomster med en umodellert kandidat (≥ 5 %) er 26 %, mot 31 % før.
- Avviket endret seg for 149 av 1 775 former. 129 ble mer enn 5 pp bedre, 12 mer enn 5 pp verre.
- Størst forbedring: *godt* (fra 100 til 0 pp), *gamle*, *syke*, *varm*, *frisk*, *tung*, *trygg*, *internasjonale* og *døde* (fra 28,4 til 1,0 pp).

**Hva som fortsatt ikke modelleres.** 64 % av forekomstene i den umodellerte gruppen har fortsatt et adjektiv som OBTs hovedanalyse. Det gjelder adjektiv uten entydige ankre:
- ubøyelige adjektiv (*stille*, *få*);
- uregelrette adjektiv (*liten/lille/litt*, *mye/mer*, *mange/flere*);
- adjektiv der også m/f og nøytrum er flertydige (*hel/helt*, *ny/nytt*).

Resten er bl.a. «i går» og *sin* i *si*.

**Ny feiltype: sjeldne adjektiv i ordboka får for mye.** Når ordboka har et sjeldent adjektiv med samme form som et vanlig substantiv, kan adjektivet nå ta for stor andel. Det skjer særlig når grunnlaget er lite:

| form | OBT | decomposer nå | grunnlag |
|---|---|---|---|
| *grunn* | subst 98, adj 2 | adj 63 / subst 37 | 0,01 |
| *bein* | subst 97, adj 3 | adj 89 / subst 11 | 0,06 |
| *faren* | *far* 98, adj 2 | adj 39 / *far* 36 / *fare* 24 | 0,01 |
| *engelsk* | subst 55, adj 45 | adj 98 / subst 2 | 0,46 |
| *sikre* | verb 64, adj 36 | adj 83 / verb 17 | 1,26 |

De fleste har svært lite grunnlag. Det støtter anbefaling 2 (vise grunnlaget, eller utelate ord med for lite grunnlag) og anbefaling 3 (nedvekte sjeldne ordbokshomografer).

**Utvalgte former og *dø*.**
- *døde*: OBT gir *dø* 72 / *død* (adj) 28, og decomposer gir nå 71 / 29 (avvik 1,0 pp, før 28,4). Grunnlaget er bare 0,1, så treffet skyldes delvis normaliseringen. I bokkorpuset gir den samme metoden 57 / 39 (`rapport_verbtyper.md` §7.2 punkt 5).
- Profilen til *dø*: avviket fra OBT er 6,0 pp (før 11,7), og den er nå bedre enn rå formtall (8,1 pp).

  | | inf/imp | pres | pret | perf-part |
  |---|---|---|---|---|
  | OBT | 28 | 15 | 54 | 2 |
  | decomposer nå | 31 | 9 | 58 | 2 |
  | naiv | 21 | 22 | 56 | 1 |

  Preteritum ligger fortsatt litt for høyt og presens for lavt, fordi substantivet *dør* overvurderes (71 mot 48 %).
- *stille* og *få* er uendret (ubøyelige adjektiv).
- Ingen av de andre utvalgte formene eller profilene er endret.

**Konklusjon.** Adjektivankrene gir den forbedringen anbefaling 1 ventet for vanlige adjektiv. Men decomposer må få kontroll på sjeldne adjektivhomografer med lite grunnlag, før adjektivandelene kan brukes ukritisk.

### 4.2 Nedvekting av sjeldne homografer

**Problemet.** En form som deles av n lemmaer, ble nedvektet med 1/n² for alle lemmaene når den brukes som grunnlag for et anslag. Et sjeldent ordbokshomograf straffer da det vanlige leksemet like hardt som seg selv. *liv* deler for eksempel *livet* med det sjeldne verbet *live*, og fikk derfor for lite.

**Endringen** (`decomposer.shared_form_weights`, standard `SHARE_MODE = "masse"`):
- En delt form fordeles på lemmaene etter hvor mye entydig bruk hvert av dem har, dvs. summen av formene som bare finnes i dette lemmaet.
- Hvert lemma får et gulv på `SHARE_FLOOR / n`, så leksemer uten entydige former ikke faller helt bort.
- Har ingen av lemmaene entydig bruk, brukes 1/n² som før.

**Valg av gulv** (innholdsord, logreg):

| variant | median avvik | vektet avvik | 90-persentil | riktig flest |
|---|---|---|---|---|
| 1/n² (§4.1) | 13,9 pp | 26,1 pp | 80,7 pp | 72,9 % |
| masse, gulv 0 | 14,4 pp | 26,8 pp | 87,6 pp | 71,6 % |
| masse, gulv 0,1 | 13,8 pp | 26,3 pp | 82,9 pp | 73,0 % |
| masse, gulv 0,3 | 13,7 pp | 26,0 pp | 81,7 pp | 73,2 % |
| **masse, gulv 0,6 (valgt)** | **13,5 pp** | **25,8 pp** | **80,4 pp** | **73,4 %** |

Uten gulv blir flere kandidater satt til 0 (bl.a. substantivet *tro*), og resultatet blir verre.

**Resultat med gulv 0,6:**
- 74 former ble mer enn 5 pp bedre og 28 mer enn 5 pp verre.
- Bedre: *sola*, *livet*, *ben*, *leken*, *lufta*, *telt*.
- Verre: *hendene*, *skien*, *hoppe*, *leke*, *steg*. Her har det sjeldne lemmaet flere entydige former enn det vanlige (f.eks. *hånd* mot *hende*), så massen peker feil vei.
- Formene der alle kandidatene er modellert: median 7,4 pp og 80 % riktig (§4.1: 7,9 pp og 80 %).
- Uendret: *dør*, *døde*, *fisker*, *kroner*, alle profilene i §4.1/§5, og dekomponeringen av «dør» og «fisker» i bokkorpuset (63,5 / 36,5 % og 64 / 20 / 15 %).

**Det som ikke løses:** *grunn* (adj. 62 %, OBT 2 %) og *bein* er uendret. Substantivet *grunn* deler hele paradigmet med det sjeldne *ei grunne*, og har ingen entydige former. Da kan ingen metode basert på paradigmet alene avgjøre hvilket av dem som er vanligst. Det krever ekstern kunnskap, f.eks. en frekvens per lemma fra et tagget korpus, eller en liste over sjeldne ordbokshomografer.

**Vurdering.** Forbedringen er reell, men liten (0,4 pp i median). Den største gjenværende feilkilden er fortsatt kandidater uten modell (§4.1).

### 4.3 Flertydighet per leksem

Homografe oppslag av samme leksem i Ordbanken (f.eks. to oppføringer for substantivet *tro*) regnes nå sammen, slik at leksemet ikke mister ankrene sine (logg del 56). Innholdsord, logreg: median 13,7 pp og 74 % riktig. Det er versjonen som er brukt i §3.

## 5. Første kjøring på lag 1 (2026-11-20)

*Uten adjektivankre og med de opprinnelige vektene for delte former. Kortversjon; de fullstendige
tallene står i logg del 42, og TSV-filene ligger i commit `390d420`.*

| utvalg | former | tokens | metode | median avvik | 90-persentil | riktig flest |
|---|---|---|---|---|---|---|
| innholdsord, alle | 1 721 | 1 051 451 | regler / logreg | 18,7 / 18,4 pp | 90,5 / 90,4 pp | 69 / 69 % |
| alle kandidater modellert | 1 206 | 721 154 | regler / logreg | 7,8 / 7,9 pp | 63,5 / 63,5 pp | 80 / 80 % |
| … med grunnlag ≥ 0,5 | 524 | 240 669 | logreg | 5,7 pp | 53,0 pp | 84 % |
| umodellert ≥ 5 % | 515 | 330 297 | regler / logreg | 50,0 pp | 99,0 pp | 44 % |

Det viktigste fra første kjøring, som ledet til forbedringene i §4:
- **Umodellerte kandidater var den største feilkilden.** 515 former (31 % av forekomstene) hadde minst
  5 % på et leksem decomposer ga 0 %. To tredjedeler av dem var adjektiv: decomposer ga *hele*, *nye*
  og *litt* 95–100 % til sjeldne verb, og *døde* 100 % til verbet (OBT: 72 %).
- **Regler og log-regresjon ga nesten samme resultat.** Log-regresjonen krever minst to kategorier der
  alle formene er entydige, og det var oppfylt for bare 566 av 2 962 kandidatanslag (19 %).
- **Homografe oppføringer ble telt dobbelt** (*la*, *rekke*), men det betydde lite: medianen endret
  seg fra 7,9 til 8,1 pp når hvert leksem bare ble telt én gang.
- **Typiske feil blant de modellerte formene:**
  - *Lite grunnlag.* For *fall* var summen av anslagene 17 mot 1 738 observert, og verbet *falle*
    (imperativ) fikk 90 % (OBT: 1 %).
  - *Delte ankerformer.* *arbeid* (82 % verb, OBT 0 %) og *livet* (63 % verb, OBT 1 %) ble dratt mot
    verbet, fordi verbets delte former ble talt fullt og substantivets nedvektet.
  - *Idiosynkratiske profiler.* *la* tilhører *legge* i 66 % av tilfellene (OBT), men decomposer ga
    *legge* 21 %.
- **Profiler:** substantivprofilene ble klart bedre enn rå formtall (*fisker* 1,4 mot 37,6 pp, *fisk*
  4,5 mot 23,2). Verbene var blandet; *dø* var verre enn rå tall (11,7 mot 8,1 pp), fordi adjektivet i
  *døde* ikke ble trukket fra.

## 6. Sammenligning med den syntetiske valideringen

| | Kunstige homografer (`rapport_dekomponering_validering.md`) | Ekte homografer, hele det taggede korpuset (§3) |
|---|---|---|
| Fasit | eksakt | OBT (kontekstbasert, ikke feilfri) |
| Kandidater | ett substantiv + ett verb, kjernekategorier | alle leksemer i Ordbanken, alle ordklasser |
| Riktig leksem størst | ca. 80 % (logreg) | 78 % når alle kandidatene er modellert, 73 % for alle innholdsord |
| Typisk avvik | 10–15 pp | 10 pp (modellert), 17 pp (alle innholdsord) |
| Regler mot logreg | logreg klart bedre | logreg klart bedre (13 mot 18 pp); i første kjøring på lag 1 ingen forskjell |

Testene bekrefter hverandre for de tilfellene decomposer er bygd for. Den ekte testen viser i tillegg
to begrensninger den syntetiske ikke kan se:
- leksemer som ikke modelleres (særlig adjektiv uten entydige ankre);
- at ekte flertydigheter ofte har få entydige ankre, slik at anslagene for enkeltord blir ustabile.

## 7. Forbehold

- **OBT er ikke feilfri.** Eksempler: *tro* som preteritum av *trå* (8 %) virker mistenkelig, og
  infinitivsmerket *å* er koblet til interjeksjonen *å*. Bare 0–7 % av forekomstene er ukoblet for de
  utvalgte formene, men systematiske taggerfeil gir systematisk feil fasit.
- **Korpusstørrelse.** Lag 1 (8,8 mill. tokens) ga usikre tall for sjeldne former. Med hele korpuset
  (43,7 mill.) er de hyppige formene stabile, men former med noen hundre forekomster (*fisker*) er
  fortsatt usikre.
- **Samme korpus for anslag og fasit.** Decomposer er kjørt på korpusets egne formtall. Hvordan den
  virker på `nb_totals` eller bokkorpuset, er ikke testet her. `rapport_dekomponering_validering.md` §4
  viser at forholdstallene må læres i samme korpus som de brukes på.
- **Profilene** omfatter bare kjernekategoriene, og kategorier som deler form innen leksemet, er slått
  sammen.

## 8. Anbefalinger

1. **Modellere adjektivkandidater i decomposer.** *Gjennomført for vanlige adjektiv 2026-11-21, se §4.1.* Det var den største enkeltforbedringen. Adjektiv uten entydige ankre (*stille*, *få*, *hel*, *ny*) er fortsatt ikke modellert.
2. **Vise grunnlaget.** Summen av anslag mot observert frekvens skiller gode og dårlige anslag (80 mot
   74 % riktig i hele korpuset) og bør vises sammen med andelene, eller brukes til å utelate ord med
   for lite grunnlag.
3. **Behandle delte ankerformer likt for substantiv og verb,** og nedvekte sjeldne ordbokshomografer.
   *Delvis gjennomført 2026-11-21, se §4.2.* Sjeldne adjektivhomografer med lite grunnlag (*grunn*,
   *bein*) er ikke løst.
4. **For foredraget:**
   - dekomponerte andeler bør vises med en usikkerhet på minst ±10–15 pp;
   - substantivprofiler (*fisk*, *fisker*, *dør*) er pålitelige etter dekomponering;
   - for verbprofiler må konkurrenten modelleres. *dø* er nå bedre enn rå tall, mens *stille* (adjektiv
     og adverb) fortsatt ikke er det;
   - andeler for enkeltformer (*dør*, *fisker*, *kroner*) bør sjekkes mot OBT før de vises.
