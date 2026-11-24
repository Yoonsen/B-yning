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

**Reproduserbarhet (lagt til 2026-11-19):** Alle tall i §2–4 gjenskapes nøyaktig med `python3 -m sqlite.verbtyper` (per-verb-resultater i `resultater/verbtyper.tsv`). Presise kriterier, slik skriptet bruker dem:
1. Alle fire kjerneformer finnes (`boy_nummer` 1, 2, 4, 5).
2. Internt distinkte: ingen ordform står i to av de fire kategoriene. Det utelukker `-et/-a`-verbene der `pret = perf-part`.
3. **`inf + pres + pret` ≥ 100 000** i `nb_totals` (perf-part teller ikke med i grensen).
4. `inf`, `pres` og `pret` har `antall_lemma_id = 1` → **606**; også `perf-part` → **580** (Sett A); alle fire kategorier har minst én form i `nb_totals` → **533**.

Sett A inneholder noen ikke-standard former som har sneket seg gjennom (*tilstede, sæte, meine*). De påvirker typefordelingen marginalt, men bør ikke brukes som eksempler.

---

## 3. De 6 verbtypene i den strenge gullstandarden (Sett A)

*Revidert 2026-11-19: tallene er nå fra bokkorpuset 1950–2020 (`dhlab ngram_book`), samme korpus som §4 og foredraget. Tidligere versjoner brukte `nb_totals` (hele NB-korpuset); se sammenligningen nederst i seksjonen. Gjenskapes med `python3 -m sqlite.verbtyper`.*

Sammenligningen mellom $N = 606$ (3 former globalt POS-isolerte), **$N = 580$ (Sett A: alle 4 former globalt POS-isolerte)** og $N = 533$ (Sett A med alle 4 former belagt i `nb_totals`) viser at fordelingen mellom de 6 undertypene er robust for utvalget (avvik på høyst 2 prosentpoeng):

1. **1. plassen bestemmer *ikke* alene rekkefølgen av de andre formene.** Alle $3! = 6$ rekkefølger er godt belagt.
2. **Infinitiv vil helst stå på 2. plass når den ikke står på 1.:**
   - Når **`pret` er på topp**, har **73,1 %** av verbene **`inf` på 2. plass** (`pret > inf > pres`), og 26,9 % har `pres` på 2. plass.
   - Når **`pres` er på topp**, har **66,4 %** **`inf` på 2. plass** (`pres > inf > pret`), og 33,6 % har `pret` på 2. plass.
   - Når **`inf` er på topp**, deler verbene seg likt: **49,8 %** `inf > pres > pret` og **50,2 %** `inf > pret > pres`.

### Oversiktstabell over de 6 rangeringstypene i Sett A ($N = 580$, bokkorpuset 1950–2020)

| Hovedtype (1. plass) | Sekundær rangering (`1. > 2. > 3.`) | Andel av hovedtypen | Andel av alle verb<br>$N=580$<br>*(jf. $N=606$ / $N=533$)* | Snittprofil (`inf / pres / pret`) | Semantisk / grammatisk karakteristikk | Eksempler (Sett A) |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **1. Infinitiv på topp**<br>*(54,0 % av verbene)* | **1A: `inf > pres > pret`** | **49,8 %** | **26,9 %**<br>*(27,2 % / 26,8 %)* | `61,6 % / 25,3 % / 13,1 %` | **Prosessuelle / diskursive aktivitetsverb:** Brukes mye etter modalverb/*å* og i pågående nåtid, sjeldnere som avsluttet fortidshendelse. | *forstå, bidra, vurdere, forklare, oppnå, foreta, utføre, unngå, produsere* |
| | **1B: `inf > pret > pres`** | **50,2 %** | **27,1 %**<br>*(27,1 % / 29,1 %)* | `55,4 % / 16,5 % / 28,1 %` | **Teliske / resultative handlingsverb:** Brukes som mål/formål i infinitiv (*skal ta, for å undersøke*) eller som fullført hendelse i preteritum (*tok, innførte*), sjelden i pågående presens. | *ta, studere, undersøke, organisere, innføre, observere, dømme, engasjere* |
| **2. Preteritum på topp**<br>*(27,6 % av verbene)* | **2A: `pret > inf > pres`** | **73,1 %** | **20,2 %**<br>*(19,8 % / 19,9 %)* | `29,9 % / 15,5 % / 54,6 %` | **Intensjonale / punktuelle hendelsesverb:** Domineres av narrativ fortid (*overtok, vedtok, forsøkte*), men brukes også etter modalverb (*vil overta, må gjenta*), mens presens er lav. | *forsøke, overta, registrere, skjule, gjenta, vedta, forlange, resultere* |
| | **2B: `pret > pres > inf`** | **26,9 %** | **7,4 %**<br>*(7,6 % / 6,4 %)* | `14,9 % / 25,3 % / 59,8 %` | **Ikke-intensjonale overgangsverb og narrative regiverb:** Rapporteres når det skjedde (*forsvant, ankom, smilte, ropte, omkom*) eller skjer (*forsvinner, ankommer*), sjelden som planlagt infinitiv (*\*for å omkomme*). | *smile, rope, forsvinne, berøre, påstå, ankomme, omkomme, mistenke* |
| **3. Presens på topp**<br>*(18,4 % av verbene)* | **3A: `pres > inf > pret`** | **66,4 %** | **12,2 %**<br>*(12,2 % / 11,8 %)* | `28,8 % / 54,7 % / 16,5 %` | **Relasjonelle og ekspositoriske verb:** Konstaterer sammenhenger i nåtid (*betyr, fungerer, innebærer*) eller drøftes modalt (*kan bety, skal fungere*), sjelden i preteritum. | *bety, innebære, oppleve, oppstå, fungere, medføre, variere, beskrive* |
| | **3B: `pres > pret > inf`** | **33,6 %** | **6,2 %**<br>*(6,1 % / 6,0 %)* | `14,7 % / 59,0 % / 26,3 %` | **Stative tilstandsverb:** Beskriver en tilstand som gjelder nå (*trenger, består, foregår, foreligger*) eller gjaldt (*trengte, bestod*), men sjelden som viljestyrt infinitiv (*å foreligge*). | *trenge, bestå, foregå, foreligge, representere, befinne, eksistere, behøve* |

### Sammenligning med hele NB-korpuset (`nb_totals`)

Samme 580 verb, regnet på `nb_totals` (hele NB-korpuset), som var grunnlaget i tidligere versjoner av denne seksjonen:

| Type | Bokkorpuset 1950–2020 | `nb_totals` |
| :--- | ---: | ---: |
| 1A `inf > pres > pret` | 26,9 % | 29,8 % |
| 1B `inf > pret > pres` | 27,1 % | 21,2 % |
| 2A `pret > inf > pres` | 20,2 % | 17,9 % |
| 2B `pret > pres > inf` | 7,4 % | 7,2 % |
| 3A `pres > inf > pret` | 12,2 % | 14,8 % |
| 3B `pres > pret > inf` | 6,2 % | 9,0 % |

Inf-på-2.-plass-funnet holder i begge korpusene (`nb_totals`: 71,2 % og 62,3 %). Forskjellen ligger i at etterkrigsbøkene har relativt mer preteritum og mindre presens enn hele NB-korpuset. Derfor deler `inf`-på-topp-verbene seg likt mellom 1A og 1B i bokkorpuset (49,8 / 50,2 %), mot 58,4 / 41,6 % i `nb_totals`. Enkeltverb kan også bytte type mellom korpusene (f.eks. *forklare*: 3A i `nb_totals`, 1A i bokkorpuset; *oppnå* og *foreta*: 1B → 1A; *overta*: 1B → 2A).

---

## 4. Detaljerte profiler og rang-stabilitet (1950–2020) for rensede kjerneverb (Sett A og Sett B)

Tabellen under viser profilene i bokkorpuset (1950–2020, 71 enkeltår) etter at støy-homografer (*dø, stille, fiske, svare, selge, leve, vinne, legge, bygge, sette, tape*) er luket ut og erstattet med **100 % globalt POS-isolerte verb (Sett A)**. For sentrale høyfrekvente kjerneverb i **Sett B** er den tekniske ordbokskollisjonen eksplisitt angitt.

**Hele Sett A (lagt til 2026-11-19):** Av de 569 Sett A-verbene som er belagt alle 71 år i bokkorpuset, har **260 (45,7 %)** samme form på 1. plass hvert år, og **80 (14,1 %)** har nøyaktig samme rekkefølge av alle tre formene hvert år. Verbene i tabellen under er altså utvalgte eksempler, ikke typiske. Det typiske verbet har stabil topp, mens 2. og 3. plass kan bytte i enkelte år.

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

*Referansene er sjekket mot forlags- og repositorieoppføringer 2026-11-21 (hull 6). Innholdet i Karlsson 1985/1986 og Arppe 2006 er gjengitt etter sitering i sekundærkilder; fulltekst er ikke lest.*

1. **Fred Karlsson (1985, 1986) og Antti Arppe (2006): frekvens i paradigmet.**
   - Karlsson viste med finske data at de fleste formene i et paradigme med rik bøyning er sjeldne eller ikke belagt i korpus, og at formfrekvensene er svært skjevt fordelt.
   - Arppe (2006) tar opp tråden i et festskrift for Karlsson. Tittelen sier poenget: også finske verb skiller seg fra hverandre i hvordan bruken fordeler seg på formene.
2. **Laura A. Janda og Olga Lyashevskaya (2011): grammatiske profiler.**
   - En *grammatisk profil* er den relative frekvensfordelingen av et leksems bøyningsformer i et korpus. For russiske verb speiler profilen aspekt, og verb med uvanlige profiler peker på særskilte bruksmønstre.
   - De bygger på Newman og Rice, som studerte bøyningsformene til engelske verb (Rice & Newman 2005; Newman & Rice 2006; Newman 2008).
3. **Petar Milin og medarbeidere (2009): paradigmer i det mentale leksikonet.**
   - Milin, Filipović Đurđević & Moscoso del Prado Martín (2009) viser for serbiske substantiv at jo mer et leksems fordeling over formene avviker fra fordelingen i bøyningsklassen (relativ entropi), desto langsommere gjenkjennes ordet. Språkbrukere er altså følsomme for både leksemets egen profil og klassens profil.
   - Milin, Kuperman, Kostić & Baayen (2009, «Words and paradigms bit by bit») gir den informasjonsteoretiske rammen.

**Referanser**

- Arppe, Antti. 2006. Frequency considerations in morphology, revisited – Finnish verbs differ, too. I *A Man of Measure: Festschrift in Honour of Fred Karlsson on his 60th Birthday*, 175–189. Turku: Linguistic Association of Finland (SKY Journal of Linguistics 19, spesialsupplement).
- Janda, Laura A. & Olga Lyashevskaya. 2011. Grammatical profiles and the interaction of the lexicon with aspect, tense, and mood in Russian. *Cognitive Linguistics* 22(4). 717–762. https://doi.org/10.1515/COGL.2011.027
- Karlsson, Fred. 1985. Paradigms and word forms. *Studia Gramatyczne* 7. 135–154.
- Karlsson, Fred. 1986. Frequency considerations in morphology. *Zeitschrift für Phonetik, Sprachwissenschaft und Kommunikationsforschung* 39(1). 19–28. https://doi.org/10.1524/stuf.1986.39.14.19
- Milin, Petar, Dušica Filipović Đurđević & Fermín Moscoso del Prado Martín. 2009. The simultaneous effects of inflectional paradigms and classes on lexical recognition: Evidence from Serbian. *Journal of Memory and Language* 60(1). 50–64. https://doi.org/10.1016/j.jml.2008.08.007
- Milin, Petar, Victor Kuperman, Aleksandar Kostić & R. Harald Baayen. 2009. Words and paradigms bit by bit: An information-theoretic approach to the processing of inflection and derivation. I James P. Blevins & Juliette Blevins (red.), *Analogy in Grammar: Form and Acquisition*, 214–252. Oxford: Oxford University Press.
- Newman, John. 2008. Aiming low in linguistics: Low-level generalizations in corpus-based research. *Proceedings of the 11th International Symposium on Chinese Languages and Linguistics (IsCLL-11)*, National Chiao Tung University, Hsinchu, Taiwan.
- Newman, John & Sally Rice. 2006. Transitivity schemas of English EAT and DRINK in the BNC. I Stefan Th. Gries & Anatol Stefanowitsch (red.), *Corpora in Cognitive Linguistics: Corpus-Based Approaches to Syntax and Lexis*. Berlin: Mouton de Gruyter.
- Rice, Sally & John Newman. 2005. Inflectional islands. Foredrag, 9th International Cognitive Linguistics Conference, Seoul.

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
   - **Oppdatert 2026-11-20:** Dekomponereren bruker nå log-regresjon på de entydige ankerkategoriene, lært på gullstandarden i samme korpus som den brukes på (se `rapport_dekomponering_validering.md`). De tidligere faste reglene var skjeve. I bokkorpuset kjøres den med `estimate_wordform_shares("dør", corpus="book")`. Substantivet anslås fra `ent_be + fl_ub + fl_be`, verbet fra `inf` (*dø*) og `perf-part` (*dødd*). Strengen **`«dør»`** fordeles da slik:
     - **Substantivet `en/ei dør` (`ent_ub`):** **63,5 %** ($\approx 428\,300$ i bøker 1950–2020)
     - **Verbet `å dø` (`pres`):** **36,5 %** ($\approx 246\,300$ i bøker 1950–2020)
     - Summen av de ukappede anslagene er 1,05 × observert, så anslagene er godt kalibrert i bokkorpuset.
     - Til sammenligning gir `nb_totals` 69,8 / 30,2 %. Den tidligere versjonen (faste regler fra `nb_totals` brukt på bøker) ga 71,4 / 28,6 %. Valideringen gir en usikkerhet på ±10–15 pp for andeler av denne typen.
4. **Resultat — `dø` bytter verbtype fra 2B til 2A:**
   - Når substantivet *en/ei dør* trekkes fra strengen *«dør»*, faller presensandelen til verbet *dø* fra **20,6 %** til **8,7 %** ($\approx 246\,300$ treff mot $492\,694$ for infinitiv *dø*):
     - **Før dekomponering (råtall):** `pret` (64,3 %) > `pres` (20,6 %) > `inf` (15,1 %), som gir **2B (`pret > pres > inf`)**.
     - **Etter dekomponering:** `pret` (**74,0 %**) > `inf` (**17,4 %**) > `pres` (**8,7 %**), som gir **2A (`pret > inf > pres`)**.
   - **Hvor robust er det?** For at `pres` skal komme over `inf`, måtte verbet stå for over 73 % av «dør», altså 36 pp mer enn anslaget. Det er større enn 90-persentilen for feilen i valideringen (ca. 30 pp). Adjektivet i «døde» er ikke trukket fra her; se punkt 5.
5. **Forbehold: også `«døde»` er flertydig (oppdatert 2026-11-20).**
   - `ordform_flertydighet` gir `døde` **`antall_lemma_id = 3`**: preteritum av *å dø* (13385), bestemt/flertall av adjektivet **`død`** (13386: *de døde, den døde mannen*) og det sjeldne verbet *å døde* (13402). Preteritumstallet over ($2\,100\,037$ i bøker) inneholder altså også adjektivbruk.
   - **Adjektivankre i dekomponereren:** `sqlite/adjektiv_gold.py` velger 1 840 adjektiv (belagt i bokkorpuset) der m/f, e-form og nøytrum er entydige. Med kryssvalidering anslås e-formen med typisk avvik ×1,67 fra m/f + nøytrum og ×1,91 fra nøytrum alene. For *død* er nøytrum (*dødt*, $69\,425$) eneste anker, fordi «død» også er et substantiv.
   - **Ankrene bestemmer ikke adjektivandelen.** `estimate_wordform_shares("døde", corpus="book")` gir 57 % *dø* / 39 % *død* / 4 % *døde*, men summen av de ukappede anslagene er bare **0,05 × observert**. Hele ordfamilien har atypiske ankre: *dødd* er sjelden fordi adjektivet overtar partisippets rolle (*han er død*, ikke *han har dødd*), *dødt* er sjelden, og substantivet *død* har nesten ikke flertall (*dødene*: 25 treff). Dekomponeringen av «død» har samme problem (0,19). Dekomponereren skriver nå ut en advarsel når summen / observert ligger utenfor 0,5–2.
   - **Spennet:** modellen for alle adjektiv gir adjektivet bare ca. 2 % av «døde» (90-persentil 7 %), fordi frekvente *-t*-former ofte er adverb (*godt, sterkt*). Forholdet e-form / *-t*-form for tilstandsadjektiv i bøker (*blind* 4,1, *naken* 6,5, *syk* 9,8, *gammel* 10,5) gir 14–35 %. Det grove overslaget fra 2026-11-17 gikk opp til 46 %.
   - **Kontroll i et tagget korpus (lagt til 2026-11-21):** i det OBT-taggede korpuset (8,4 mill. ord, `rapport_dekomponering_obt.md` §4.1) er 28 % av «døde» adjektivet *død*. Det ligger innenfor spennet for tilstandsadjektiv. Med 28 % blir profilen til *dø* i bokkorpuset pret 67 / inf 22 / pres 11 %.
   - **Profilen til *dø* i bokkorpuset** (med `pres` = $246\,300$ fra dør-dekomponeringen):

     | Adjektivandel av «døde» | pret | inf | pres |
     | :--- | ---: | ---: | ---: |
     | 0 % (ingen korreksjon) | 74,0 % | 17,4 % | 8,7 % |
     | 2 % (alle adjektiv) | 73,6 % | 17,6 % | 8,8 % |
     | 14–35 % (tilstandsadjektiv) | 71–65 % | 19–23 % | 10–12 % |
     | 28 % (OBT-tagget korpus) | 67,2 % | 21,9 % | 10,9 % |
     | 46 % (høyeste overslag) | 60,5 % | 26,3 % | 13,1 % |

   - **Konklusjon:** rangeringen `pret > inf > pres` (2A) holder så lenge adjektivet står for under **77 %** av «døde». Det er langt over alle overslagene. Prosenttallene er usikre, rangeringen er det ikke. En presis adjektivandel krever kontekst (*de/den/det døde* mot *han/hun/som døde*), og bigrammer var ikke tilgjengelige fra API-ene vi bruker.
   - **Sjekk av «dør»:** *dødd* er også anker for verbet i dør-dekomponeringen. Med bare infinitiv som anker blir verbandelen av «dør» 34,8 % i stedet for 36,5 %, så dør-resultatet påvirkes knapt.
6. **Språklig tolkning:**
   - Og dette gir umiddelbart dyp språklig mening: Mens *forsvinne*, *ankomme* og *omkomme* (som er 100 % kollisjonsfrie i Sett A og blir stående i **2B**) sjelden brukes etter modalverb eller *å*, snakker vi på norsk svært ofte om *«å dø»* i infinitiv (*frykten for å dø, i ferd med å dø, skal dø, må dø, heller dø enn...*), mens pågående nåtid (*«han dør nå»*) er langt sjeldnere enn både fortid (*døde*) og infinitiv (*å dø*)!

### 7.3 Den globale paradigme-grafen ($a \stackrel{n}{\text{---}} b$) for et helt nasjonalleksikon
- Vi har kartlagt hele nettverket av delte ordformer på tvers av 151 648 lemmaer i Norsk Ordbank og vist at **87,4 % av ordforrådet er helt isolert (grad 0)** og **97,3 % ligger i lukkede komponenter på $\le 4$ lemmaer**. Det er nettopp denne topologiske glissenheten som gjør at ankerbasert dekomponering (som for *«fisker»* og *«dør»*) nesten alltid har entydige holdepunkter i nabolaget.
