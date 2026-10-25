# Rapport: Kvantitative verbtyper, paradigmeprofiler og sekundære rangeringer

*Delrapport i MONS-prosjektet «Leksikalske bøyningsprofiler: ordboksdata og historiske n-gram» (Revidert med global kryss-POS-filtrering, Sett A / Sett B og dekomponering av «dø/dør»)*

---

## 1. Hovedspørsmål
Når vi klassifiserer norske verb etter hvilken bøyningsform som dominerer i paradigmet (`inf`, `pres` eller `pret`, ev. `perf-part` og `pres-part`):
1. **Hvilke hovedtyper av verbparadigmer finner vi i korpuset?**
2. **Gir 1. plassen automatisk rangeringen av de øvrige formene (`2. plass > 3. plass`), eller finnes det systematisk sekundær variasjon (undertypologier)?**
3. **Hvor stabil er hele rangeringen (`1. > 2. > 3.`) fra år til år (1950–2020) når vi renser bort alle kryss-POS-homografer?**

---

## 2. Metodisk forutsetning: Global POS-isolasjon (To-trinns vask: Sett A og Sett B)

I et uannotert n-gramkorpus må en gullstandard for verbprofiler ta høyde for to feilkilder:
1. **Intern synkretisme i `-et/-a`-verb:** Svake verb med preteritum på `-et/-a` (*kaste – kaster – kastet – kastet*) deler ordform mellom preteritum (`boy_nummer = 4`) og perfektum partisipp (`boy_nummer = 5`). Vi krever derfor at alle fire kjerneformer (`inf`, `pres`, `pret`, `perf-part`) har **internt distinkte ordformer** (`pret != perf-part`).
2. **Kryss-POS-homografi i Norsk Ordbank:** Selv kjente høyfrekvente verb har ofte enkeltformer som kolliderer med ordformer i *andre* ordklasser i `ordform_flertydighet` (på tvers av alle 151 648 lemmaer i Norsk Ordbank):
   - *Substantiv-kollisjon i presens:* `dør` (*å dø* vs. *en/ei dør*), `fisker` (*å fiske* vs. *en fisker / fisker*), `selger` (*å selge* vs. *en selger*), `lever` (*å leve* vs. *ei/en lever*).
   - *Adjektiv-/adverb-kollisjon:* `stille` (*å stille* vs. adj./adv. *stille*), `svarte` (*å svare* vs. bestemt/flertall av adj. *svart*: *den svarte bilen*), `vant` (*å vinne* vs. adj. *vant til*).
   - *Verb-til-verb-kollisjon:* `la` (pret. av *å legge* vs. inf./imp. av *å la*), `satt` (perf-part. av *å sette* vs. pret. av *å sitte*).

Vi gjennomfører derfor en eksplisitt **to-trinns vask**:
- **Sett A — Streng gullstandard (100 % globalt POS-isolerte verb):** Verb ($\ge 100\,000$ treff i `nb_totals`, 4 internt distinkte kjerneformer) der **ingen** av kjerneformene deler ordform med *noe annet lemma i noen ordklasse* i hele Norsk Ordbank (`ordform_flertydighet.antall_lemma_id = 1`).
  - Krav om global POS-isolasjon på de 3 analyserte formene (`inf`, `pres`, `pret`) gir **$N = 606$ verb**.
  - Utvides kravet til også å gjelde 4. form (`perf-part`, slik at også leksikaliserte partisipp-adjektiver som *forlatt, opptatt, forbudt, betjent* lukes ut), gjenstår **$N = 580$ verb** (og **$N = 533$ verb** dersom vi i tillegg krever at hver eneste av de 4 kjerneformene alene ligger inne blant topp 500 000 ordformer i `nb_totals`, noe som fjerner arkaiske riksmålsformer som *tilstede*).
- **Sett B — Praktisk rene kjerneverb (med eksplisitt flagget ordbokskollisjon):** Sentrale norske kjerneverb (*gå, komme, si, gjøre, lese, spise, kjøpe, ha, vite, ligge*) som har en teknisk ordbokskollisjon i én form (f.eks. *går* mot *i går* / imp. *gåre*, eller *ha* mot interjeksjon *ha!* og *hektar*), men der verbformen dominerer i korpuset. Åpenbare støykandidater der kollisjonen forrykker profilen (*dø, stille, fiske, svare, selge, leve, vinne, legge, bygge, sette, tape*) er luket ut av gullstandard-tabellen, og *dø / dør* analyseres i stedet med dekomponeringsmetoden i **seksjon 7.2**.

---

## 3. De 6 verbtypene i den strenge gullstandarden (Sett A)

Sammenligningen mellom $N = 606$ (3 former globalt POS-isolerte), **$N = 580$ (Sett A: alle 4 former globalt POS-isolerte)** og **$N = 533$ (Sett A med alle 4 former belagt i `nb_totals`)** viser at fordelingen mellom de 6 undertypene (`1A–3B`) er ekstremt robust (avviket er kun $0{,}1\text{–}0{,}8$ prosentpoeng):

1. **1. plassen bestemmer *ikke* alene rekkefølgen av de andre formene** — alle $3! = 6$ permutasjoner er godt belagt og speiler verbets aksjonsart/aspekt.
2. **Men det er en sterk strukturell asymmetri i favør av infinitiv på 2. plass:**
   - Når **`pret` er på topp**, har **71,2 %** av verbene i Sett A ($N=580$) **`inf` på 2. plass** (`pret > inf > pres`), mens kun **28,8 %** har `pres` på 2. plass (`pret > pres > inf`).
   - Når **`pres` er på topp**, har **62,3 %** av verbene **`inf` på 2. plass** (`pres > inf > pret`), mens **37,7 %** har `pret` på 2. plass (`pres > pret > inf`).
   - Når **`inf` er på topp**, deler verbene seg **58,4 % vs. 41,6 %** mellom `inf > pres > pret` og `inf > pret > pres`.

### Oversiktstabell over de 6 rangeringstypene i Sett A ($N = 580$ globalt POS-isolerte verb, med $N = 606$ og $N = 533$ i parentes)

| Hovedtype (1. plass) | Sekundær rangering (`1. > 2. > 3.`) | Andel av hovedtypen (Sett A) | Andel av alle verb<br>Sett A $N=580$<br>*(jf. $N=606$ / $N=533$)* | Gj.snittsprofil i Sett A (`inf / pres / pret`) | Semantisk / grammatisk karakteristikk | 100 % globalt POS-isolerte eksempler (Sett A) |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **1. Infinitiv på topp**<br>*(51,0 % av verbene)* | **1A: `inf > pres > pret`** | **58,4 %** | **29,8 %**<br>*(30,0 % / 29,8 %)* | `61,7 % / 25,4 % / 12,9 %` | **Prosessuelle / diskursive aktivitetsverb:** Brukes mye etter modalverb/*å* og i pågående nåtid, sjeldnere som avsluttet fortidshendelse. | *forstå, vurdere, oppnå, utføre, foreta, bidra, diskutere, forklare, tilby, unngå, produsere, konstatere* |
| | **1B: `inf > pret > pres`** | **41,6 %** | **21,2 %**<br>*(21,3 % / 22,7 %)* | `56,8 % / 15,9 % / 27,3 %` | **Teliske / resultative handlingsverb:** Brukes enten som mål/formål i infinitiv (*skal ta, for å undersøke*) eller som fullført hendelse i preteritum (*tok, innførte*), sjelden i pågående presens. | *ta, undersøke, innføre, redusere, studere, dømme, henvende, engasjere, etablere* |
| **2. Preteritum på topp**<br>*(25,2 % av verbene)* | **2A: `pret > inf > pres`** | **71,2 %** | **17,9 %**<br>*(17,5 % / 17,3 %)* | `27,7 % / 13,8 % / 58,4 %` | **Intensjonale / punktuelle hendelsesverb:** Domineres av narrativ fortid (*overtok, vedtok, forsøkte*), men brukes også ofte etter modalverb (*vil overta, må gjenta*), mens presens er lav. | *overta, vedta, gjenta, forsøke, skjule, registrere, organisere, protestere, resultere, notere* |
| | **2B: `pret > pres > inf`** | **28,8 %** | **7,2 %**<br>*(7,3 % / 6,8 %)* | `15,1 % / 26,3 % / 58,6 %` | **Ikke-intensjonale overgangsverb og narrative regiverb:** Rapporteres direkte når det skjedde (*forsvant, ankom, smilte, ropte, omkom*) eller skjer (*forsvinner, ankommer*), sjelden som planlagt infinitiv (*\*for å omkomme*). | *forsvinne, ankomme, smile, rope, omkomme, berøre, inntreffe, referere, lansere, debutere* |
| **3. Presens på topp**<br>*(23,8 % av verbene)* | **3A: `pres > inf > pret`** | **62,3 %** | **14,8 %**<br>*(14,9 % / 14,6 %)* | `29,7 % / 54,6 % / 15,7 %` | **Relasjonelle og ekspositoriske verb:** Konstaterer sammenhenger i nåtid (*betyr, fungerer, innebærer*) eller drøftes modalt (*kan bety, skal fungere*), sjelden i preteritum. | *bety, fungere, innebære, oppleve, anbefale, arrangere, representere, motta, meddele* |
| | **3B: `pres > pret > inf`** | **37,7 %** | **9,0 %**<br>*(9,1 % / 8,8 %)* | `15,6 % / 58,2 % / 26,2 %` | **Stative tilstandsverb:** Beskriver en tilstand som gjelder nå (*trenger, består, foregår, foreligger*) eller gjaldt i fortid (*trengte, bestod, foregikk*), men sjelden som viljestyrt infinitiv (*å foreligge*). | *trenge, bestå, foregå, foreligge, foreslå, oppstå, befinne, behøve, invitere* |

*(Merk: `oppnå`, `foreta` og `overta` skifter mellom `nb_totals` (1810–2020) og `ngram_book` (1950–2020) avhengig av om hele NB-korpuset eller kun etterkrigsbøker legges til grunn; i seksjon 4 vises tallene for bokkorpuset 1950–2020.)*

---

## 4. Detaljerte profiler og rang-stabilitet (1950–2020) for rensede kjerneverb (Sett A og Sett B)

Tabellen under viser profilene i bokkorpuset (1950–2020, 71 enkeltår) etter at støy-homografer (*dø, stille, fiske, svare, selge, leve, vinne, legge, bygge, sette, tape*) er luket ut og erstattet med **100 % globalt POS-isolerte verb (Sett A)**. For sentrale høyfrekvente kjerneverb i **Sett B** er den tekniske ordbokskollisjonen eksplisitt angitt.

| Undertype (`1. > 2. > 3.`) | Verb | Sett | `inf` | `pres` | `pret` | Topp-stabilitet (1. plass) | Full-rang-stabilitet (`1. > 2. > 3.`) | Ev. teknisk kollisjon i Ordbanken (for Sett B) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1A: `inf > pres > pret`** | **vurdere** | **Sett A** | **69,6 %** | 21,1 % | 9,3 % | **100,0 %** | **100,0 %** *(71 av 71 år!)* | *Ingen (100 % globalt POS-isolert)* |
| | **forstå** | **Sett A** | **47,3 %** | 28,8 % | 23,9 % | **100,0 %** | **97,2 %** | *Ingen (100 % globalt POS-isolert)* |
| | **oppnå** | **Sett A** | **71,4 %** | 17,4 % | 11,2 % | **100,0 %** | **91,5 %** | *Ingen (100 % globalt POS-isolert)* |
| | **utføre** | **Sett A** | **55,1 %** | 28,0 % | 16,9 % | **100,0 %** | **90,1 %** | *Ingen (100 % globalt POS-isolert)* |
| | **foreta** | **Sett A** | **63,7 %** | 21,1 % | 15,2 % | **100,0 %** | 78,9 % | *Ingen (100 % globalt POS-isolert)* |
| | **bidra** | **Sett A** | **52,8 %** | 31,4 % | 15,8 % | 91,5 % | 76,1 % | *Ingen (100 % globalt POS-isolert)* |
| | **diskutere** | **Sett A** | **56,3 %** | 24,2 % | 19,5 % | **100,0 %** | 64,8 % | *Ingen (100 % globalt POS-isolert)* |
| | **forklare** | **Sett A** | **55,8 %** | 22,2 % | 22,0 % | **100,0 %** | 52,1 % *(pres ≈ pret)* | *Ingen (100 % globalt POS-isolert)* |
| | *gjøre* | *Sett B* | **42,4 %** | 32,8 % | 24,8 % | **100,0 %** | 74,6 % | `gjør` = verb *å gjø*; `gjorde` = verb *å gjorde* |
| | *lese* | *Sett B* | **50,6 %** | 27,1 % | 22,3 % | **100,0 %** | 71,8 % | `leser` = subst. *en leser*; `leste` = sj. verb *å leste* |
| | *spise* | *Sett B* | **46,6 %** | 27,8 % | 25,6 % | **100,0 %** | 59,2 % | `spise/spiser` = arkaisk subst. *en spise / en spis* |
| **1B: `inf > pret > pres`** | **undersøke** | **Sett A** | **65,9 %** | 12,8 % | 21,3 % | **100,0 %** | **100,0 %** *(71 av 71 år!)* | *Ingen (100 % globalt POS-isolert)* |
| | **innføre** | **Sett A** | **55,8 %** | 14,4 % | 29,8 % | 95,8 % | **95,8 %** | *Ingen (100 % globalt POS-isolert)* |
| | **ta** | **Sett A** | **43,8 %** | 24,7 % | 31,5 % | 90,1 % | **87,3 %** | *Ingen (`ta, tar, tok, tatt` er 100 % POS-isolerte i Ordbanken!)* |
| | *kjøpe* | *Sett B* | **39,3 %** | 23,4 % | 37,2 % | 52,1 % | 50,7 % | `kjøper` = subst. *en kjøper* |
| **2A: `pret > inf > pres`** | **overta** | **Sett A** | 31,5 % | 15,2 % | **53,4 %** | **100,0 %** | **100,0 %** *(71 av 71 år!)* | *Ingen (100 % globalt POS-isolert)* |
| | **vedta** | **Sett A** | 24,0 % | 14,2 % | **61,8 %** | **100,0 %** | **98,6 %** *(70 av 71 år)* | *Ingen (100 % globalt POS-isolert)* |
| | **forlate** | **Sett A\***| 35,8 % | 20,8 % | **43,3 %** | 98,6 % | **98,6 %** *(70 av 71 år)* | `inf/pres/pret` 100 % rene (`perf-part` *forlatt* er også adj.) |
| | **gjenta** | **Sett A** | 31,4 % | 25,4 % | **43,2 %** | **100,0 %** | **93,0 %** | *Ingen (100 % globalt POS-isolert)* |
| | **skjule** | **Sett A** | 41,4 % | 16,7 % | **42,0 %** | 63,4 % | 63,4 % | *Ingen (100 % globalt POS-isolert)* |
| | **forsøke** | **Sett A** | 30,5 % | 27,3 % | **42,2 %** | 88,7 % | 62,0 % | *Ingen (100 % globalt POS-isolert)* |
| | *si* | *Sett B* | 25,7 % | 23,2 % | **51,0 %** | **100,0 %** | **84,5 %** | `si` = determinativ *si* (hunnkjønn) / subst. *ei si* |
| **2B: `pret > pres > inf`** | **forsvinne** | **Sett A** | 17,7 % | 28,6 % | **53,7 %** | **100,0 %** | **100,0 %** *(71 av 71 år!)* | *Ingen (100 % globalt POS-isolert)* |
| | **ankomme** | **Sett A** | 6,7 % | 27,0 % | **66,3 %** | **100,0 %** | **100,0 %** *(71 av 71 år!)* | *Ingen (100 % globalt POS-isolert)* |
| | **rope** | **Sett A** | 11,7 % | 21,6 % | **66,7 %** | **100,0 %** | **100,0 %** *(71 av 71 år!)* | *Ingen (100 % globalt POS-isolert)* |
| | **smile** | **Sett A** | 10,1 % | 19,5 % | **70,4 %** | **100,0 %** | **98,6 %** *(70 av 71 år)* | *Ingen (100 % globalt POS-isolert)* |
| | **omkomme** | **Sett A** | 9,3 % | 10,4 % | **80,4 %** | **100,0 %** | 43,7 % *(pres ≈ inf)* | *Ingen (100 % globalt POS-isolert)* |
| | *komme* | *Sett B* | 21,1 % | 31,0 % | **47,9 %** | **100,0 %** | **100,0 %** *(71 av 71 år!)* | `komme/kommer` = sjeldent subst. *en komme* |
| | *gå* | *Sett B* | 27,6 % | 34,2 % | **38,2 %** | 70,4 % | 70,4 % | `går` = subst. *i går* / imp. av *å gåre* |
| **3A: `pres > inf > pret`** | **bety** | **Sett A** | 14,6 % | **73,9 %** | 11,4 % | **100,0 %** | **90,1 %** | *Ingen (100 % globalt POS-isolert)* |
| | **fungere** | **Sett A** | 34,5 % | **48,0 %** | 17,6 % | 78,9 % | **76,1 %** | *Ingen (100 % globalt POS-isolert)* |
| | **oppleve** | **Sett A** | 29,6 % | **43,8 %** | 26,5 % | 64,8 % | 56,3 % | *Ingen (100 % globalt POS-isolert)* |
| | **innebære** | **Sett A** | 13,4 % | **73,9 %** | 12,7 % | **100,0 %** | 54,9 % *(inf ≈ pret)* | *Ingen (100 % globalt POS-isolert)* |
| | **anbefale** | **Sett A** | 31,2 % | **41,8 %** | 27,0 % | 49,3 % | 28,2 % | *Ingen (100 % globalt POS-isolert)* |
| **3B: `pres > pret > inf`** | **trenge** | **Sett A** | 8,7 % | **66,8 %** | 24,5 % | **100,0 %** | **100,0 %** *(71 av 71 år!)* | *Ingen (100 % globalt POS-isolert)* |
| | **bestå** | **Sett A** | 11,2 % | **67,1 %** | 21,7 % | **100,0 %** | **100,0 %** *(71 av 71 år!)* | *Ingen (100 % globalt POS-isolert)* |
| | **foregå** | **Sett A** | 19,0 % | **53,5 %** | 27,5 % | **100,0 %** | **95,8 %** | *Ingen (100 % globalt POS-isolert)* |
| | **foreligge** | **Sett A** | 14,5 % | **69,2 %** | 16,3 % | **100,0 %** | 76,1 % | *Ingen (100 % globalt POS-isolert)* |
| | *ha* | *Sett B* | 12,0 % | **56,9 %** | 31,1 % | **100,0 %** | **100,0 %** *(71 av 71 år!)* | `ha` = interj. *ha!* / symb. *ha* (`har` og `hadde` er 100 % rene) |
| | *vite* | *Sett B* | 18,7 % | **55,3 %** | 26,0 % | **100,0 %** | **100,0 %** *(71 av 71 år!)* | Sideform `veit` = subst. *ei veit*; `vite/vet/visste` er 100 % rene |
| | *ligge* | *Sett B* | 10,7 % | **52,9 %** | 36,4 % | 91,5 % | **91,5 %** | `ligger` = sjeldent subst. *en ligger* |

---

## 5. Utvidelse til 4- og 5-formsparadigmer (`perf-part` og `-ende`)

Når vi tar med **perfektum partisipp (`perf-part`, `boy_nummer = 5`)** og **presens partisipp (`-ende`, `boy_nummer = 10`)**, kommer to ekstra verbtyper tydelig frem:

1. **Partisipp-/passivdominerte verb (`perf-part` på topp):**
   - Blant de 161 høyfrekvente simplex-verbene ($\ge 500\text{k}$ treff, `pret != perf-part`) har **42,2 %** faktisk `perf-part` som sin største enkeltform (fordi `perf-part` i bokmål dekker både perfektum *har X*, passiv *blir/er X* og ubestemt partisipp-adjektiv *et X forslag*!).
   - Også her ser vi en tydelig sekundær struktur:
     - **`perf-part > pret > inf > pres` (13,7 %):** Resultative hendelsesverb som ofte står i passiv/perfektum eller fortid (*registrere, skjule, organisere, arrestere, notere*).
     - **`perf-part > inf > pret > pres` (11,2 %)** og **`perf-part > inf > pres > pret` (6,8 %):** Normative/administrative verb (*redusere, dømme, plassere, produsere, definere, regulere*).
2. **Leksikaliserte `-ende`-utbrytere (`pres-part` på topp):**
   - Mens `-ende` normalt ligger på **sisteplass ($< 0{,}22\text{ \%}$ for 75 % av verbene)**, hopper `-ende` opp på **1. plass ($50\text{–}97\text{ \%}$ av paradigmet)** når partisippet er leksikalisert til adjektiv eller preposisjon (*resterende* 96,7 %, *glimrende* 90,0 %, *vedrørende* 89,8 %, *tilsvarende* 81,1 %, *sjarmerende* 78,3 %, *strålende* 70,7 %, *spennende* 68,7 %).

---

## 6. Konklusjon for MONS-foredraget
- **Ja, det finnes klare sekundære variasjoner — også i det 100 % globalt POS-isolerte Sett A ($N=580$):** Toppformen alene låser ikke 2. og 3. plass, men **plasseringen av infinitiv (2. plass vs. 3. plass)** fungerer som en skarp semantisk skillelinje:
  - Verb som kan planlegges/styres modalt beholder **`inf` på 2. plass** (`pret > inf > pres` som *overta, vedta, forlate, gjenta* og `pres > inf > pret` som *bety, fungere, innebære*).
  - Verb som betegner **ikke-viljestyrte overganger/regi** (`pret > pres > inf` som *forsvinne, ankomme, rope, smile, omkomme*) eller **rene tilstander** (`pres > pret > inf` som *trenge, bestå, foregå, foreligge, ha, vite*) skyver derimot **`inf` ned på 3. plass**!
- Og denne fulle rangeringen (`1. > 2. > 3.`) er for 100 % kollisjonsfrie Sett A-verb som *vurdere*, *undersøke*, *overta*, *forsvinne*, *ankomme*, *rope*, *trenge* og *bestå* **uendret i 71 av 71 enkeltår (100 %)** fra 1950 til 2020.

---

## 7. Forskningslitteratur og hva som er nytt i vår tilnærming

Det finnes en sentral internasjonal tradisjon vi kan knytte an til (som gir oss et sterkt teoretisk anker), samtidig som metoden og funnene våre går et langt skritt videre:

### 7.1 Sentrale referanser i litteraturen
1. **Fred Karlsson (1985, 1986, 2000) & Antti Arppe (2006) — *Inflectional profiles / Focal forms*:**
   - Karlsson (1986, *«Frequency considerations in morphology»*, *Zeitschrift für Phonetik, Sprachwissenschaft und Kommunikationsforschung*) påpekte at kasusbøyde substantiv i finsk har bestemte «fokalformer» i paradigmet styrt av semantikk. Karlsson antok imidlertid opprinnelig at verb oppførte seg mer ensartet, noe Arppe (2006) nyanserte for finske verb.
2. **Laura A. Janda & Olga Lyashevskaya (2011) — *Grammatical profiles*:**
   - I *«Grammatical profiles and the interaction of the lexicon with aspect, tense, and mood in Russian»* (*Cognitive Linguistics* 22(4), 719–763; jf. også **Newman 2008** om engelske verb) defineres en *grammatical profile* som den relative frekvensfordelingen av et leksems bøyningsformer i et korpus. De viser at bøyningsprofilen speiler verbets aksjonsart/aspekt, og at statistiske uteliggere («outliers») peker på særskilte konstruksjoner.
3. **Petar Milin, Dušica Filipović Đurđević & R. Harald Baayen (2009) — *Paradigms bit by bit*:**
   - I *«Paradigms bit by bit: An information theoretic approach to the processing of paradigmatic structure in inflectional morphology»* (*Cognitive Linguistics* 20(1), 215–228) viser de psykolingvistisk (med relativ entropi / Kullback-Leibler-divergens) at språkbrukere mentalt lagrer *både* det enkelte leksemets spesifikke bøyningsprofil *og* ordklassens generelle normalprofil.

### 7.2 Vi snur pilen «baklengs» — Glansnummer: Dekomponering av *«dø»* (verb) vs. *«dør»* (substantiv)

Alle tidligere studier av grammatiske profiler har forutsatt et **ferdig lemmatisert og POS-tagget korpus** for å regne ut profilen. Vi snur problemet på hodet: Ved å kombinere Norsk Ordbank med de entydige ankerformene i hvert paradigme bruker vi bøyningsprofilene til å **dekomponere flertydige overflateformer** direkte i rå historiske frekvensdata.

Et perfekt demonstrasjonseksempel er verbet **`dø`** (`lemma_id = 13385`) vs. substantivet **`en/ei dør`** (`lemma_id = 13525`):
1. **Den naive fellen i rå n-gramdata:**
   - Hvis man slår opp bøyningsformene til verbet *dø* direkte i bokkorpuset (1950–2020), får man:
     - `pret` **døde**: $2\,100\,037$ (**64,3 %**)
     - `pres` **dør**: $674\,558$ (**20,6 %**)
     - `inf` **dø**: $492\,694$ (**15,1 %**)
   - I råtall ser det dermed ut som om *dø* tilhører undertype **2B (`pret > pres > inf`)**, på linje med *forsvinne*, *ankomme* og *omkomme*.
2. **Kryss-POS-diagnose via Norsk Ordbank:**
   - Oppslag i `ordform_flertydighet` viser at mens infinitiv **`dø`** ($492\,694$ i bøker; $2\,590\,524$ i `nb_totals`) og perfektum partisipp **`dødd`** ($50\,265$ i bøker; $234\,835$ i `nb_totals`) er **100 % globalt entydige** (`antall_lemma_id = 1`), kolliderer strengen **`«dør»`** ($674\,558$ i bøker; $3\,381\,873$ i `nb_totals`) mellom:
     1. Presens av verbet **`å dø`** (`id = 13385`: *han/hun dør*)
     2. Ubestemt entall av substantivet **`en/ei dør`** (`id = 13525`: *åpne en dør, fra dør til dør*)
3. **Ankerbasert dekomponering av strengen `«dør»`:**
   - Substantivet *dør* (`id = 13525`) har **tre 100 % globalt entydige ankerformer** i paradigmet sitt (`antall_lemma_id = 1`):
     - `ent_be` (**døren + døra**): $1\,650\,679$ i bøker 1950–2020 ($7\,021\,510$ i `nb_totals`)
     - `fl_ub` (**dører**): $192\,902$ i bøker ($1\,838\,925$ i `nb_totals`)
     - `fl_be` (**dørene**): $133\,837$ i bøker ($1\,255\,788$ i `nb_totals`)
     - Sum entydige substantiv-ankere: **$1\,977\,418$** i bøker ($10\,116\,223$ i `nb_totals`).
   - Når vi kjører dekomponeringsmodellen vår (`estimate_wordform_shares("dør")` i `sqlite/decomposer.py`, eller bruker forholdstallet `ent_ub / ent_be` fra sammenlignbare rom-/bygnings-substantiv som *seng, port, trapp, vegg, vindu*), estimeres fordelingen av råfrekvensen for **`«dør»`** til:
     - **Substantivet `en/ei dør` (`ent_ub`):** **71,4 %** ($\approx 481\,600$ i bøker 1950–2020; $2\,413\,878$ i `nb_totals`)
     - **Verbet `å dø` (`pres`):** **28,6 %** ($\approx 192\,900$ i bøker 1950–2020; $967\,995$ i `nb_totals`)
4. **Resultat — `dø` bytter verbtype fra 2B til 2A!**
   - Så snart vi trekker fra substantivet *en/ei dør* fra strengen *«dør»*, faller presensandelen til verbet *dø* fra kunstig oppblåste **20,6 %** ned til **6,9 %** ($\approx 192\,900$ treff mot $492\,694$ for infinitiv *dø*):
     - **Før dekomponering (råtall):** `pret` (64,3 %) > `pres` (20,6 %) > `inf` (15,1 %) $\rightarrow$ feilaktig klassifisert som **2B (`pret > pres > inf`)**.
     - **Etter dekomponering (renset):** `pret` (**75,4 %**) > `inf` (**17,7 %**) > `pres` (**6,9 %**) $\rightarrow$ flytter seg klart over i **2A (`pret > inf > pres`)**!
   - Og dette gir umiddelbart dyp språklig mening: Mens *forsvinne*, *ankomme* og *omkomme* (som er 100 % kollisjonsfrie i Sett A og blir stående i **2B**) sjelden brukes etter modalverb eller *å*, snakker vi på norsk svært ofte om *«å dø»* i infinitiv (*frykten for å dø, i ferd med å dø, skal dø, må dø, heller dø enn...*), mens pågående nåtid (*«han dør nå»*) er langt sjeldnere enn både fortid (*døde*) og infinitiv (*å dø*)!

### 7.3 Den globale paradigme-grafen ($a \stackrel{n}{\text{---}} b$) for et helt nasjonalleksikon
- Vi har kartlagt hele nettverket av delte ordformer på tvers av 151 648 lemmaer i Norsk Ordbank og vist at **87,4 % av ordforrådet er helt isolert (grad 0)** og **97,3 % ligger i lukkede komponenter på $\le 4$ lemmaer**. Det er nettopp denne topologiske glissenheten som gjør at ankerbasert dekomponering (som for *«fisker»* og *«dør»*) nesten alltid har entydige holdepunkter i nabolaget.
