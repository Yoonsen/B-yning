# Rapport: Decomposer mot et tagget korpus

*Delrapport i MONS-prosjektet, 2026-11-20. Utfyller `rapport_dekomponering_validering.md`. Tallene
gjenskapes med `python -m sqlite.valider_dekomponering_obt`, og resultatene per form og per profil står
i `resultater/dekomponering_obt_former.tsv` og `resultater/dekomponering_obt_profiler.tsv`. Arbeidslogg:
`logg.md`, del 40–42.*

*Oppdatert 2026-11-21 (logg del 52): decomposer har fått adjektivankre, og valideringen er kjørt på nytt. §3–5 er beholdt slik de ble skrevet, med tall fra første kjøring (2026-11-20; TSV-filene fra den kjøringen ligger i commit `390d420`). De nye tallene står i §9, og nedvekting av sjeldne homografer (logg del 55) i §10. TSV-filene i `resultater/` er fra kjøringen i §10.*

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

- **Korpus og fasit.** Det OBT-taggede bokmålskorpuset (`korpus/obt_frekvenser.db`): 222 dokumenter,
  1950–2026, 8,4 mill. ord. Det er tagget med Oslo-Bergen-taggeren (multitagger, CG-3 og OBT-Stat),
  som velger analyse ut fra konteksten. Analysene er koblet til lemma_id i Norsk Ordbank (logg del 34).
  OBT er ikke en perfekt fasit, se §7.
- **Decomposer** kjøres på de samme korpustallene: formfrekvensene i korpuset brukes som `nb_totals`.
  - Log-regresjonen lærer på gullstandardprofiler med frekvenser fra korpuset: 1 916 substantiv og
    459 verb med alle fire kjernekategorier belagt. Gullstandardlemmaene velges som i decomposer.py
    med NBs `nb_totals` (logg del 41).
  - Begge metodene testes: `regler` (de faste forholdstallene) og `logreg` (standard fra 2026-11-20).
    Decomposer er ikke endret.
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
  - *Bred del:* alle 1 775 ordformer med minst 100 forekomster i korpuset der Ordbanken har minst to
    ulike leksemer blant substantiv, verb og adjektiv.
  - *Hovedutvalget* er de 1 721 formene der OBT gir minst 90 % substantiv, verb eller adjektiv. Det
    holder småord som *for*, *men* og *nå* utenfor; decomposer er ikke laget for dem.
  - *Dyp del:* 12 former fra repoet (logg del 40) og profiler for 18 lemmaer.

## 3. Resultater: bred del (første kjøring, uten adjektivankre)

| utvalg | former | tokens | metode | median avvik | vektet avvik | 90-persentil | riktig flest |
|---|---|---|---|---|---|---|---|
| innholdsord, alle | 1 721 | 1 051 451 | regler | 18,7 pp | 29,2 pp | 90,5 pp | 69 % |
| | | | logreg | 18,4 pp | 29,4 pp | 90,4 pp | 69 % |
| alle kandidater modellert (umodellert < 5 %) | 1 206 | 721 154 | regler | **7,8 pp** | 14,3 pp | 63,5 pp | **80 %** |
| | | | logreg | 7,9 pp | 14,6 pp | 63,5 pp | 80 % |
| … med grunnlag ≥ 0,5 | 524 | 240 669 | logreg | 5,7 pp | 12,1 pp | 53,0 pp | 84 % |
| … med grunnlag < 0,5 | 682 | 480 485 | logreg | 9,6 pp | 15,9 pp | 71,0 pp | 76 % |
| umodellert ≥ 5 % | 515 | 330 297 | regler/logreg | **50,0 pp** | 61,7 pp | 99,0 pp | **44 %** |

«Vektet» er vektet med antall forekomster av formen.

**Når alle kandidatene er modellert, virker decomposer omtrent som i den syntetiske testen.**
- Den gir størst andel til riktig leksem for 80 % av formene, og medianavviket er 8 pp. Kollegaens test
  med kunstige homografer fant ca. 80 % riktig og 10–15 pp median.
- Feilfordelingen har en lang hale: hver tiende form bommer med over 60 pp.
- Med mer å regne ut fra (grunnlag ≥ 0,5) blir det bedre: 84 % riktig og 6 pp median.

**Den største feilkilden er kandidater decomposer ikke modellerer.**
- 515 av 1 721 innholdsordformer (31 % av forekomstene) har minst 5 % av forekomstene på et leksem
  decomposer gir 0 %. Der bommer den med 50 pp i median og gir riktig leksem størst andel bare i 44 %
  av tilfellene.
- To tredjedeler av forekomstene i denne gruppen er former der OBTs hovedanalyse er et **adjektiv**:
  - decomposer gir *hele*, *nye* og *litt* 95–100 % til sjeldne verb (*hele*, *nye*, *lite*);
  - *godt* fordeles på substantivet *godt* og verbet *godte*;
  - *få* mister adjektivandelen sin (17 %).
- Resten er bl.a. «i går» (*går*: 15 %) og *sin* i *si*.

**Regler og log-regresjon gir nesten samme resultat på ekte former.**
- Log-regresjonen krever minst to kategorier der alle formene er entydige. I de modellerte formene er
  det oppfylt for bare 566 av 2 962 kandidatanslag (19 %); resten bruker reglene som reserve.
- I ekte flertydigheter er de andre formene i paradigmet ofte også flertydige, slik at forbedringen
  fra den syntetiske testen sjelden slår inn.

**Homografe oppføringer telles dobbelt, men det betyr lite.**
- Decomposer gir hver homografe lemma_id (f.eks. to oppføringer for *la* «la være» og tre for verbet
  *rekke*) sitt eget fulle anslag, slik at leksemet kan få for stor vekt.
- Når hvert leksem bare telles én gang, endres medianavviket fra 7,9 til 8,1 pp. Dette er altså ikke
  en viktig feilkilde.

**Typiske feil blant de modellerte formene:**
- *Lite grunnlag.* For *fall* er summen av anslagene 17 mot 1 738 observert, og verbet *falle*
  (imperativ) får 90 % (OBT: 1 %).
- *Delte ankerformer.* Når et verb bare har ankerformer som deles med substantivet (*arbeidet*,
  *livet*), brukes hele frekvensen, mens substantivets delte former nedvektes. *arbeid* (82 % verb,
  OBT 0 %) og *livet* (63 % verb, OBT 1 %) dras derfor mot verbet.
- *Idiosynkratiske profiler.* *la* tilhører *legge* i 66 % av tilfellene (OBT), men decomposer gir
  *legge* 21 %. Log-regresjonen anslår preteritum av *legge* fra infinitiv og partisipp, men *la* er
  mye hyppigere i fortellende tekst enn gjennomsnittsverbet tilsier.

## 4. Resultater: utvalgte former (første kjøring)

Andeler i prosent, OBT mot decomposer (logreg). Avviket er gitt i prosentpoeng.

| form | n | OBT | decomposer | avvik | årsak |
|---|---|---|---|---|---|
| *ønsker* | 2 044 | verb 93, subst 7 | 94 / 6 | 0,9 | |
| *landet* | 2 099 | *land* 85, *lande* 15 | 88 / 12 | 2,4 | |
| *hatt* | 2 843 | *ha* 95, *hatt* 5 | 92 / 8 | 2,6 | |
| *dager* | 2 570 | *dag* 100 | 96 / *dage* 4 | 4,2 | |
| *viser* | 2 649 | verb 94, subst *vise* 6 | 98 / *viser* 2 | 5,8 | subst *vise* får 0 |
| *møter* | 978 | verb 72, subst 28 | 65 / 35 | 6,9 | |
| *fisker* | 367 | *fiske* 74, *fisker* 19, *fisk* 8 | 59 / 19 / 21 | 14,6 | *fisk* (flertall) overvurdert |
| *går* | 8 486 | *gå* 85, *går* («i går») 15 | 100 / 0 | 14,8 | umodellert |
| *dør* | 628 | *dø* 52, *dør* 48 | 29 / 71 | 22,8 | substantivet overvurdert |
| *kroner* | 2 943 | subst 99, verb 1 | 74 / 26 | 24,9 | verbets ankre (*krone*) er flertydige |
| *døde* | 1 580 | *dø* 72, *død* (adj) 28 | 100 / 0 | 28,4 | adjektiv umodellert |
| *tro* | 1 937 | verb 60, subst 28, *trå* 8, adj 4 | 91 / 0 / 9 / 0 | 31,8 | subst og adj får 0 |

## 5. Resultater: profiler (første kjøring)

Bøyningsprofiler (kjernekategorier) i tre varianter:
- *OBT*: fasit fra det taggede korpuset;
- *decomposer*: hver forms frekvens × decomposerens andel for leksemet;
- *naiv*: rå formfrekvens uten fordeling, slik n-gram gir.

Kategorier som deler form innen samme leksem (f.eks. infinitiv/imperativ, preteritum/perfektum
partisipp i svake verb), er slått sammen, fordi decomposer bare fordeler mellom leksemer. Avviket er
hvor mange prosentpoeng av profilen som er feilplassert.

| lemma | n (OBT) | avvik decomposer | avvik naiv | merknad |
|---|---|---|---|---|
| *fisker* (subst) | 333 | **1,4** | 37,6 | *fisker* ent ub 19 % (naiv 57 %) |
| *fisk* (subst) | 1 052 | **4,5** | 23,2 | *fisker* fl ub 7 % (OBT 2 %, naiv 26 %) |
| *dør* (subst) | 2 978 | **4,2** | 8,8 | |
| *land* (subst) | 4 184 | **0,4** | 3,5 | |
| *krone* (subst) | 3 129 | 1,3 | 0,7 | |
| *sette* (verb) | 6 621 | **13,4** | 36,9 | imperativ *sett* = partisipp av *se* (naiv 30 %) |
| *svare* (verb) | 4 378 | **11,3** | 26,0 | imperativ *svar* = substantiv (naiv 18 %) |
| *bygge* (verb) | 2 073 | **4,5** | 10,6 | |
| *fiske* (verb) | 504 | 27,7 | 38,9 | infinitiv overvurdert (46 mot 23 %), presens undervurdert |
| *tro* (verb) | 6 317 | 7,0 | 8,9 | |
| *gå* (verb) | 24 799 | 3,4 | 3,4 | «i går» umodellert, presens 32 mot 29 % |
| *tape* (verb) | 693 | 27,6 | 27,8 | imperativ *tap* = substantiv, får 28 % (OBT 0 %) |
| *leve* (verb) | 2 450 | 3,1 | 1,8 | |
| *selge* (verb) | 1 019 | 4,1 | 3,0 | |
| *vinne* (verb) | 1 597 | 9,8 | 7,4 | |
| *dø* (verb) | 2 078 | 11,7 | **8,1** | se under |
| *legge* (verb) | 8 937 | 23,9 | **11,0** | *la* (preteritum) 21 mot 45 % |
| *stille* (verb) | 1 885 | 40,3 | 38,5 | adjektiv/adverb *stille* umodellert, infinitiv 62 mot 23 % |

- **Substantiv:** decomposer forbedrer profilene klart og treffer innen 1–5 pp. For *fisker* og
  *fisk* er forskjellen fra rå formtall stor.
- **Verb:** blandet resultat.
  - Decomposer hjelper mest der en imperativ kolliderer med et substantiv eller et partisipp
    (*sett*, *svar*).
  - Den gjør profilen verre enn rå formtall når konkurrenten er et adjektiv eller adverb
    (*dø*, *stille*) eller når verbet har en uvanlig profil (*legge*).
  - *tape* viser at imperativregelen kan gi en kollisjon med et substantiv (*tap*) altfor stor vekt.
- ***dø*:**

  | | inf/imp | pres | pret | perf-part |
  |---|---|---|---|---|
  | OBT | 28 | 15 | 54 | 2 |
  | decomposer | 25 | 8 | 66 | 2 |
  | naiv | 21 | 22 | 56 | 1 |

  - Rekkefølgen pret > inf > pres stemmer i alle tre variantene.
  - Decomposer undervurderer presens (fordi *dør* gis for mye til substantivet) og overvurderer
    preteritum (fordi adjektivet *døde* ikke trekkes fra). Feilene går samme vei som forbeholdet i
    `rapport_verbtyper.md` §7.2.
  - I det taggede korpuset ligger presens på 15 %, mot 7–9 % i dekomponeringen av n-gram-tallene der.
    Korpusene er forskjellige, så tallene kan ikke sammenlignes direkte.

## 6. Sammenligning med den syntetiske valideringen

| | Kunstige homografer (`rapport_dekomponering_validering.md`) | Ekte homografer, tagget korpus (denne rapporten) |
|---|---|---|
| Fasit | eksakt | OBT (kontekstbasert, ikke feilfri) |
| Kandidater | ett substantiv + ett verb, kjernekategorier | alle leksemer i Ordbanken, alle ordklasser |
| Riktig leksem størst | ca. 80 % (logreg) | 80 % når alle kandidatene er modellert, 69 % for alle innholdsord |
| Typisk avvik | 10–15 pp | 8 pp (modellert), 18 pp (alle innholdsord) |
| Regler mot logreg | logreg klart bedre | ingen forskjell; logreg brukes i 19 % av anslagene |

Testene bekrefter hverandre for de tilfellene decomposer er bygd for. Den ekte testen viser i tillegg
to begrensninger den syntetiske ikke kan se:
- leksemer som ikke modelleres (særlig adjektiv);
- at ekte flertydigheter sjelden har nok entydige ankre til log-regresjonen.

## 7. Forbehold

- **OBT er ikke feilfri.** Eksempler: *tro* som preteritum av *trå* (8 %) virker mistenkelig, og
  infinitivsmerket *å* er koblet til interjeksjonen *å*. Bare 0–7 % av forekomstene er ukoblet for de
  utvalgte formene, men systematiske taggerfeil gir systematisk feil fasit.
- **Korpuset er lite.** Med minst 100 forekomster per form er tallene usikre for de sjeldne formene,
  og forholdstallene i log-regresjonen er lært på færre lemmaer enn i `nb_totals`.
- **Samme korpus for anslag og fasit.** Decomposer er kjørt på korpusets egne formtall. Hvordan den
  virker på `nb_totals` eller bokkorpuset, er ikke testet her. Kollegaens §4 viser at forholdstallene
  må læres i samme korpus som de brukes på.
- **Profilene** omfatter bare kjernekategoriene, og kategorier som deler form innen leksemet, er slått
  sammen.

## 8. Anbefalinger

1. **Modellere adjektivkandidater i decomposer.** *Gjennomført for vanlige adjektiv 2026-11-21, se §9.* Det er den største enkeltforbedringen. Det gjelder
   to tredjedeler av forekomstene der decomposer i dag gir en kandidat 0 %, bl.a. *døde*, *hele*,
   *nye* og *stille*.
2. **Vise grunnlaget.** Summen av anslag mot observert frekvens skiller gode og dårlige anslag (84 mot
   76 % riktig) og bør vises sammen med andelene, eller brukes til å utelate ord med for lite grunnlag.
3. **Behandle delte ankerformer likt for substantiv og verb,** og vurdere å nedvekte sjeldne
   ordbokshomografer (*live*, *falle* i imperativ, *dage*), som i dag får urimelig store andeler.
4. **For foredraget:**
   - dekomponerte andeler bør vises med en usikkerhet på minst ±10–15 pp;
   - substantivprofiler (*fisk*, *fisker*, *dør*) er pålitelige etter dekomponering;
   - verbprofiler der konkurrenten er et adjektiv eller adverb (*dø*, *stille*), er det ikke. For
     *dø* holder rekkefølgen, men prosentene gjør det ikke.

## 9. Ny kjøring med adjektivankre (2026-11-21)

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

## 10. Nedvekting av sjeldne homografer (2026-11-21)

**Problemet.** En form som deles av n lemmaer, ble nedvektet med 1/n² for alle lemmaene når den brukes som grunnlag for et anslag. Et sjeldent ordbokshomograf straffer da det vanlige leksemet like hardt som seg selv. *liv* deler for eksempel *livet* med det sjeldne verbet *live*, og fikk derfor for lite.

**Endringen** (`decomposer.shared_form_weights`, standard `SHARE_MODE = "masse"`):
- En delt form fordeles på lemmaene etter hvor mye entydig bruk hvert av dem har, dvs. summen av formene som bare finnes i dette lemmaet.
- Hvert lemma får et gulv på `SHARE_FLOOR / n`, så leksemer uten entydige former ikke faller helt bort.
- Har ingen av lemmaene entydig bruk, brukes 1/n² som før.

**Valg av gulv** (innholdsord, logreg):

| variant | median avvik | vektet avvik | 90-persentil | riktig flest |
|---|---|---|---|---|
| 1/n² (§9) | 13,9 pp | 26,1 pp | 80,7 pp | 72,9 % |
| masse, gulv 0 | 14,4 pp | 26,8 pp | 87,6 pp | 71,6 % |
| masse, gulv 0,1 | 13,8 pp | 26,3 pp | 82,9 pp | 73,0 % |
| masse, gulv 0,3 | 13,7 pp | 26,0 pp | 81,7 pp | 73,2 % |
| **masse, gulv 0,6 (valgt)** | **13,5 pp** | **25,8 pp** | **80,4 pp** | **73,4 %** |

Uten gulv blir flere kandidater satt til 0 (bl.a. substantivet *tro*), og resultatet blir verre.

**Resultat med gulv 0,6:**
- 74 former ble mer enn 5 pp bedre og 28 mer enn 5 pp verre.
- Bedre: *sola*, *livet*, *ben*, *leken*, *lufta*, *telt*.
- Verre: *hendene*, *skien*, *hoppe*, *leke*, *steg*. Her har det sjeldne lemmaet flere entydige former enn det vanlige (f.eks. *hånd* mot *hende*), så massen peker feil vei.
- Formene der alle kandidatene er modellert: median 7,4 pp og 80 % riktig (§9: 7,9 pp og 80 %).
- Uendret: *dør*, *døde*, *fisker*, *kroner*, alle profilene i §5/§9, og dekomponeringen av «dør» og «fisker» i bokkorpuset (63,5 / 36,5 % og 64 / 20 / 15 %).

**Det som ikke løses:** *grunn* (adj. 62 %, OBT 2 %) og *bein* er uendret. Substantivet *grunn* deler hele paradigmet med det sjeldne *ei grunne*, og har ingen entydige former. Da kan ingen metode basert på paradigmet alene avgjøre hvilket av dem som er vanligst. Det krever ekstern kunnskap, f.eks. en frekvens per lemma fra et tagget korpus, eller en liste over sjeldne ordbokshomografer.

**Vurdering.** Forbedringen er reell, men liten (0,4 pp i median). Den største gjenværende feilkilden er fortsatt kandidater uten modell (§9).

