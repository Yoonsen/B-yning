# Prosjektlogg — Leksikalske bøyningsprofiler (MONS)

Denne loggen oppdateres av alle AI-agenter (og mennesker ved behov) etter hver arbeidsøkt eller milepæl. Se `AGENTS.md` for retningslinjer.

---

## 2026-10-23 — Oppstart, SQLite-konvertering av Norsk Ordbank og prosjektarkitektur

**Agent:** Antigravity (Gemini 4 Argon)

### Hva ble gjort
1. **Faglig ramme (`abstract.md`):**
   - Lagret MONS-abstractet *«Leksikalske bøyningsprofiler: ordboksdata og historiske n-gram»* i `abstract.md`.
2. **Inspeksjon og konvertering av Norsk Ordbank (`20220201_norsk_ordbank_nob_2005/` -> `sqlite/ordbank.db`):**
   - Inspiserte de 8 TSV-filene i `20220201_norsk_ordbank_nob_2005/` (totalt 1 740 466 linjer, kodet i `ISO-8859-1` / `latin1` med CRLF).
   - Skrev `sqlite/build_db.py` som konverterer alle 8 tabeller til UTF-8 i `sqlite/ordbank.db`, setter opp indekser og bygger to ferdig materialiserte og indekserte analysetabeller (med tilhørende views):
     - `lemma_former` (`v_lemma_former`): Dedupliserer `fullformsliste` (kun `normering = 'normert'`) over alternative paradigmer (f.eks. *-a/-et* for verb og mask/fem-valgfrihet for substantiv).
     - `ordform_flertydighet` (`v_ordform_flertydighet`): Forhåndsberegner for hver ordform (`oppslag`) antall distinkte `lemma_id`, antall leksem+ordklasse-kombinasjoner (`grunnform:pos`), totalt antall analyser og en lesbar oppsummeringsstreng.
3. **Spørringsbibliotek (`sqlite/queries.py`):**
   - Opprettet hjelpefunksjoner klare til bruk i Jupyter Notebooks og skript:
     - `lookup_wordform(oppslag)`
     - `get_paradigm(grunnform=..., lemma_id=..., pos=...)`
     - `get_verb_profile_forms(grunnform=..., lemma_id=...)`
     - `get_noun_profile_forms(grunnform=..., lemma_id=...)`
     - `find_anchor_forms(lemma_id)` (skiller mellom helt entydige former, leksem-entydige former og former som er flertydige mellom ulike lemmaer).
4. **Agent-kontrakt (`AGENTS.md`):**
   - Opprettet `AGENTS.md` med prosjektobligasjoner, mappestruktur, dokumentasjon av datamodellen i `sqlite/ordbank.db` og retningslinjer for bruk av `logg.md`.

### Viktige observasjoner fra databasen (knyttet til abstractets eksempler)
- **Case «fisker»:** I `ordform_flertydighet` har ordformen `fisker` 4 normerte analyser fordelt på 4 `lemma_id`:
  1. `fisk` (subst, `fl ub`, `lemma_id=17301`) — har entydig holdepunkt i bestemt entall **`fisken`** (kun 1 analyse i hele ordbanken).
  2. `fiske` (verb, `pres`, `lemma_id=17307`).
  3. `fiske` (subst nøyt, «et fiske», `fl ub`, `lemma_id=17310`).
  4. `fisker` (subst mask, «en fisker», `ent ub`, `lemma_id=17348`) — har hele tre helt entydige holdepunkter: **`fiskeren`** (`ent be`), **`fiskere`** (`fl ub`) og **`fiskerne`** (`fl be`).
- **Case «gå / går / gikk» (`lemma_id=25369`) og «vite / vet / visste» (`lemma_id=79435`):**
  - `gikk`, `vite` og `vet` er 100 % entydige i ordbanken (1 `lemma_id`, 1 analyse).
  - `gå` tilhører kun `lemma_id=25369`, men har 2 interne analyser (`inf` og `imp`).
  - `visste` tilhører kun `lemma_id=79435`, men står både som `pret` og bøyd perfektum partisipp (`adj <perf-part> be ent` / `fl`).
  - `går` har 3 `lemma_id` i ordbanken: verb `gå` (`pres`), subst `går` (som i *«i går»*, ubøyelig, `lemma_id=25380`) og det sjeldne verbet `gåre` (`imp`, `lemma_id=25431`). Merk at *«i går»* er en reell høyfrekvent konkurrent i n-gramdataene for ordformen `går`!
- **Case «eple» (`lemma_id=15075`) vs. «buss» (`lemma_id=9789`):**
  - `eple`, `eplet`, `epler`, `epla`, `eplene` er alle 100 % entydige i ordbanken (kun `lemma_id=15075`).
  - `buss`, `bussen`, `busser`, `bussene` har i ordbanken formell konkurranse fra verbet `busse` (`lemma_id=9793`) og de lavfrekvente substantivene `busse` (`lemma_id=9794, 9795`, «buse / god venn»). Dette illustrerer en viktig metodisk nyanse: forskjellen mellom *leksikografisk flertydighet* (sjeldne homografer i ordboken) og *empirisk flertydighet i bruk* (slik som *fisker* eller *går*).

### Neste steg
- Sette opp første Jupyter Notebook (f.eks. `notebooks/01_ordbank_og_ngram.ipynb`) som kobler `sqlite/queries.py` med Nasjonalbibliotekets n-gram-API (`dhlab` / `nb_ngram`) for å hente og plotte tidsserier og bøyningsprofiler for verb- og substantiv-eksemplene.

---

## 2026-10-23 (del 2) — N-gram-integrasjon, bøyningsprofiler og stabilitetsanalyse (1950–2020)

**Agent:** Antigravity (Gemini 4 Argon)

### Hva ble gjort
1. **N-gram-klient med lokal SQLite-cache (`sqlite/ngram.py` og `sqlite/ngram_cache.db`):**
   - Implementerte `fetch_ngram_dhlab` (mot `https://api.nb.no/dhlab/ngram_book` og `/ngram_newspapers`) og `fetch_ngram_sp` (mot `sp_tjenester/beta/ngram_1/ngram/query`).
   - Alle tidsserier mellomlagres i `sqlite/ngram_cache.db`, slik at gjentatte kjøringer tar < 1 ms.
   - Implementerte `compute_paradigm_profile` som kobler Norsk Ordbank-paradigmer med historiske n-grammer (1950–2020), håndterer homografe `lemma_id` (velger det lemmaet i ordbanken som har flest fylte bøyningskategorier og høyest korpusfrekvens når `lemma_id` ikke er oppgitt), og beregner:
     - Total og årlig proporsjonsfordeling mellom bøyningskategoriene (`inf`, `pres`, `pret` for verb; `ent ub`, `ent be`, `fl ub`, `fl be` for substantiv).
     - Hvilken kategori som ligger på topp (`dominant_slot`), hvor stor andel av paradigmet den tar (`dominant_share`), hvor mange prosent av årene 1950–2020 samme form ligger på 1. plass (`top_slot_consistency`), standardavvik fra år til år (`std_per_slot`), og tiårsprofiler (`decade_profiles` fra 1950-tallet til 2010-tallet).
2. **Analyse-skript og Jupyter Notebook:**
   - Opprettet `sqlite/analyze_profiles.py` og `notebooks/01_paradigmeprofiler_og_stabilitet.ipynb`.

### Viktige empiriske og metodiske funn (1950–2020)
1. **Hvor stor del av et paradigme kan én form få, og hvilke former ligger på topp?**
   - **Verb (`inf`, `pres`, `pret` i bokkorpuset 1950–2020):**
     - **Infinitiv på topp (typisk 40–63 % av paradigmet):** *stille* (63,3 %), *forklare* (55,8 %), *fiske* (51,7 %), *lese* (50,6 %), *forstå* (47,3 %), *spise* (46,6 %), *ta* (43,8 %), *gjøre* (42,4 %), *finne* (41,3 %), *snakke* (40,9 %).
     - **Presens på topp (typisk 36–57 % av paradigmet):** *ha* (56,9 %), *vite* (55,3 % — merk at presens *«vet»* er mer frekvent i bokkorpuset enn *«vite»* 18,7 % og *«visste»* 26,0 %!), *ligge* (52,9 %), *leve* (40,7 %), *fortelle* (39,5 %).
     - **Preteritum på topp (typisk 38–64 % av paradigmet):** *dø* (*døde* 64,3 %), *svare* (*svarte* 60,0 %), *vinne* (*vant* 58,8 %), *legge* (*la* 58,5 %), *si* (*sa* 51,0 %), *komme* (*kom* 47,9 %), *tape* (*tapte* 41,3 %), *gå* (*gikk* 38,2 % mot *går* 34,2 % og *gå* 27,6 %).
   - **Substantiv (`ent ub`, `ent be`, `fl ub`, `fl be`):**
     - **Bestemt entall på topp:** *sol* (*sola/solen* 67,1 %), *krig* (*krigen* 63,1 %), *konge* (*kongen* 52,7 %), *bok* (*boka/boken* 42,6 %), *buss* (*bussen* 41,9 % mot *buss* 36,9 % og *busser* 15,3 %), *bil* (*bilen* 41,3 %).
     - **Ubestemt entall på topp:** *fisk* (60,2 %), *dag* (59,5 %), *vei* (48,0 %), *kirke* (45,0 %), *mann* (44,2 %), *fisker* (43,1 % — pga. sammenfall i overflateformen *«fisker»*!).
     - **Ubestemt flertall på topp:** *kvinne* (*kvinner* 48,8 %), *eple* (*epler* 45,1 % mot *eple* 30,2 %, *eplene/epla* 13,5 %, *eplet* 11,1 % i bokkorpuset).
2. **Stabilitet over tid (1950–2020):**
   - Bøyningsprofilene er **bemerkelsesverdig stabile** over 70 år:
     - For 19 av 30 undersøkte verb ligger samme bøyningsform på 1. plass i **90–100 % av alle enkeltår** fra 1950 til 2020.
     - Standardavviket fra år til år for toppformens andel ligger for de fleste verb på kun **1,2 til 5,0 prosentpoeng** (f.eks. *spise*: 46,1 % i 1950-årene $\rightarrow$ 48,0 % i 2010-årene, std = 1,5 pp; *gå*: *gikk* 44,4 % i 1950-årene $\rightarrow$ 41,1 % i 2010-årene, std = 3,4 pp).
3. **To viktige metodiske feller oppdaget i Norsk Ordbank:**
   - **Homografe `lemma_id` innenfor samme ordklasse:** Oppslag på grunnform uten disambiguering treffer tilfeldig `lemma_id` (f.eks. *vinne* med svakt preteritum *vinte* i stedet for *vant*, *bok* = treet bøk med flertall *boker* i stedet for *bøker*, *sol* = musikknote uten flertall/bestemt form). Dette er nå løst i `compute_paradigm_profile`.
   - **Paradigme-intern synkretisme (intetkjønn enstavelsesord):** For ord som *år*, *barn*, *hus* er `ent ub` og `fl ub` identiske i form (*år*, *barn*, *hus*). Hvis man summerer per `boy_nummer`, telles samme ordform to ganger. Vi bør derfor merke eller gruppere synkretiske celler eksplisitt i videre analyser.

---

## 2026-10-23 (del 3) — Breddeskanning av «normalen» (< 60 %-regelen) med `nb_totals`

**Agent:** Antigravity (Gemini 4 Argon)

### Hva ble gjort
1. **Lokal totalfrekvenstabell (`nb_totals` i `sqlite/ordbank.db`):**
   - Hentet de 500 000 mest frekvente ordformene fra `https://api.nb.no/dhlab/totals/500000` (ned til frekvens 4 625) og lagret dem i tabellen `nb_totals(oppslag PRIMARY KEY, freq INTEGER)` i `sqlite/ordbank.db`.
   - Dette gjør det mulig å koble hele Norsk Ordbank direkte mot korpusfrekvenser i SQL på noen millisekunder.
2. **Statistisk breddeskanning av høyfrekvente, 100 % lemma-entydige simplex-ord ($\ge 500\,000$ treff i paradigmet, uten synkretisme mellom cellene):**
   - **Simplex-verb med 3 former (`inf`, `pres`, `pret`, $N = 189$):**
     - Median topp-andel: **53,6 %** (gj.snitt **55,6 %**, kvartilbredde **45,3 % – 64,2 %**).
     - Andel med toppform $< 60\text{ \%}$: **66,7 %** ($< 65\text{ \%}$: **76,7 %**).
     - Fordeling av hvilken form som er på topp: **36,5 % `pret`**, **34,4 % `inf`**, **29,1 % `pres`** (nesten helt jevnt tredelt!).
   - **Simplex-verb med 4 former (`inf`, `pres`, `pret`, `perf-part`, $N = 161$):**
     - Median topp-andel: **46,2 %** (gj.snitt **49,1 %**, kvartilbredde **38,4 % – 59,2 %**).
     - Andel med toppform $< 60\text{ \%}$: **75,2 %** ($< 65\text{ \%}$: **85,7 %**).
   - **Tellelige simplex-substantiv med 4 former (`ent ub`, `ent be`, `fl ub`, `fl be`, $N = 571$ der flertall utgjør $\ge 10\text{ \%}$):**
     - Median topp-andel: **51,7 %** (gj.snitt **53,4 %**, kvartilbredde **44,4 % – 61,8 %**).
     - Andel med toppform $< 60\text{ \%}$: **70,2 %** ($< 65\text{ \%}$: **82,0 %**).
     - Fordeling av hvilken form som er på topp: **60,2 % `ent ub`**, **27,5 % `fl ub`**, **9,6 % `ent be`**, **2,6 % `fl be`**.
   - **Substantiv uten flertallskrav ($N = 1\,024$, inkl. utellelige abstrakter/masseord som *sorg*, *ideologi*, *likebehandling*):**
     - Median topp-andel øker til **63,0 %** fordi utellelige ord nesten bare brukes i entall (`ent ub` / `ent be`).
   - **Unntakene som bryter 60–65 %-grensen:** Ord som er låst til bestemte syntaktiske konstruksjoner (f.eks. *angår* 87,7 % i `pres`, *forebygge* 89,1 % i `inf` etter *for å*, *basert* 82,1 % og *datert* 86,3 % i `perf-part`) eller utellelige substantiv.

---

## 2026-10-23 (del 4) — Paradigme-utbrytere («strålende»-effekten) som kvantitativt leksikaliseringsmål

**Agent:** Antigravity (Gemini 4 Argon)

### Hva ble gjort
- Undersøkte hypotesen om at bøyingsformer som «bryter ut av paradigmet» (tar en uforholdsmessig stor andel sammenlignet med normalen for den grammatiske kategorien) fungerer som et kvantitativt signal på at ordformen har fått en egen, leksikalisert betydning (f.eks. blitt et eget adjektiv eller preposisjon).
- Testet dette systematisk på **presens partisipp (`-ende`, `boy_nummer = 10`)** på tvers av 3 239 verb med $\ge 100\,000$ treff i `nb_totals`.

### Viktige funn
1. **Normalen for `-ende` i et verbparadigme (`inf + pres + pret + perf-part + pres-part`):**
   - Median andel for `-ende`-formen på tvers av alle verb er **< 0,1 %** (75 %-kvartilen er **0,22 %**, og 90 %-desilen er **5,5 %**). For **93,5 %** av alle verb utgjør `-ende`-formen under 10 % av paradigmet.
2. **Utbryterne — når `-ende` tar over paradigmet (30 % – 97 %):**
   - I Norsk Ordbank har leksikografene allerede opprettet egne `adj`-lemmaer for en del slike utbrytere, som ***glimrende*** (90,0 % av *glimre*-paradigmet), ***spennende*** (51,7 % i bokkorpuset 1950–2020, økende fra 36,0 % på 1950-tallet til 55,9 % på 2010-tallet), ***avgjørende*** (54,2 %) og ***imponerende*** (49,9 %).
   - Men en lang rekke minst like ekstreme utbrytere står i Norsk Ordbank **kun** som bøyningsformer under verbet (`lem=1`, uten eget `adj`- eller `prep`-lemma):
     - ***resterende*** (96,7 % av *restere*)
     - ***vedrørende*** (89,8 % av *vedrøre* — fungerer som preposisjon)
     - ***tilsvarende*** (81,1 % av *tilsvare* — 5,93 mill. treff)
     - ***oppløftende*** (80,3 % av *oppløfte*)
     - ***formildende*** (80,0 % av *formilde*)
     - ***sjarmerende*** (78,3 % av *sjarmere*)
     - ***sprudlende*** (72,1 % av *sprudle*)
     - ***strålende*** (70,7 % av *stråle* i `nb_totals`; 46,0 % selv når substantivflertall *stråler* ligger i nevneren, og ~75–80 % av selve verbparadigmet!)
     - ***tilfredsstillende*** (64,4 % av *tilfredsstille*)
     - ***administrerende*** (63,2 % av *administrere*)
     - ***overveldende*** (58,6 % av *overvelde*)
3. **Konklusjon / metodisk verdi:**
   - Avvik fra normalprofilen (f.eks. når en partisippform som normalt ligger på $< 1\text{–}5\text{ \%}$ plutselig utgjør $40\text{–}95\text{ \%}$ av paradigmet) gir et direkte, objektivt kriterium for **leksikalisering og semantisk løsrivelse** — og kan til og med brukes leksikografisk til å peke ut hvilke partisipper i Norsk Ordbank som burde vært oppført som egne adjektiv-/preposisjonsleksemer.

---

## 2026-10-23 (del 5) — Dekomponering av flertydig ordform («fisker») ut fra resten av paradigmene

**Agent:** Antigravity (Gemini 4 Argon)

### Hva ble gjort
- Skrev og kjørte `sqlite/decompose_fisker.py` for å teste hovedhypotesen i abstractet på ordformen **«fisker»** ($1\,435\,424$ treff i `nb_totals`, hvorav $223\,821$ i bøker 1950–2020 og $955\,475$ i aviser 1950–2020).
- Kartla alle fire normerte analyser i Norsk Ordbank (de tre hovedkandidatene + det ubøyelige/kollektive intetkjønnsordet *et fiske*):
  1. **Substantivet *«en fisker»* (`lemma_id=17348`, der *«fisker»* er `ent ub`):**
     - Har tre 100 % entydige holdepunkter i resten av paradigmet: `fiskeren` ($215\,276$), `fiskere` ($1\,644\,273$) og `fiskerne` ($1\,374\,105$), til sammen **$3\,233\,654$**.
     - Sammenlignet med 93 helt entydige flertallsdominerte person-/yrkesord på *-er* (som *politiker, deltaker, innbygger, musiker, medarbeider*) gir profil-vektet regresjon et uavhengig estimat på **$\sim 804\,000$** forekomster av *«en fisker»* (`ent ub`).
  2. **Substantivet *«en fisk»* (`lemma_id=17301`, der *«fisker»* er `fl ub`):**
     - Selv om entall `fisk` ($5{,}78\text{ mill.}$) og `fisken` ($2{,}04\text{ mill.}$) er svært høyfrekvente (fordi *fisk* brukes kollektivt/utellelig i entall: *«mye fisk», «tre kilo fisk»*), avslører det entydige holdepunktet i bestemt flertall **`fiskene`** (kun **$181\,593$** treff, altså $7{,}6\times$ lavere enn *fiskerne*!) at tellelig flertall av *fisk* er langt mer beskjedent.
     - Ut fra normalforholdet $\text{fl ub} / \text{fl be}$ for dyreord (median $3{,}34$) gir `fiskene` et uavhengig estimat på **$\sim 607\,000$** forekomster av *«flere fisker»* (`fl ub`).
  3. **Verbet *«å fiske»* (`lemma_id=17307`, der *«fisker»* er `pres`):**
     - Her deler `fiske` ($3{,}74\text{ mill.}$) og `fisket` ($2{,}84\text{ mill.}$) form med intetkjønnssubstantivet *«et fiske / dette fisket»* (`lemma_id=17310`), mens passiven **`fiskes`** ($155\,338$) og **`fiskende`** ($9\,149$) er 100 % entydige verbformer.
     - Ut fra medianforholdet $\text{pres} / \text{passiv}$ ($2{,}61$) for høstings-/aktivitetsverb (*jakte, høste, dyrke, plukke, fange, slakte*) gir dette et uavhengig estimat på **$\sim 405\,000$** forekomster av presens *«fisker»*.
  4. **(Substantiv nøyt. *«et fiske»*, `lemma_id=17310`):** Har formelt `fl ub = fisker` i ordbanken (*«ulike fisker»*), men i praksis er dette marginalt sammenlignet med de tre hovedkandidatene.

### Viktige resultater
- **Konsistenssjekk:** Summen av de tre **helt uavhengige** paradigme-estimatene ($804\,009 + 607\,049 + 405\,122 = 1\,816\,180$) treffer innenfor $\sim 26\text{ \%}$ av det faktisk observerte totaltallet for ordformen «fisker» ($1\,435\,424$)!
- **Normalisert fordeling i `nb_totals` (samlet NB-korpus):**
  1. **Subst. *«en fisker»* (`ent ub`, yrket): 44,3 %** ($\sim 635\,500$)
  2. **Subst. *«en fisk»* (`fl ub`, dyret): 33,4 %** ($\sim 479\,800$)
  3. **Verb *«å fiske»* (`pres`, handlingen): 22,3 %** ($\sim 320\,200$)
- **Sjanger- og tidsforskjeller (bøker vs. aviser 1950–2020):**
  - I **aviser** er `fiskeren + fiskere + fiskerne` ($2{,}30\text{ mill.}$) nesten 8 ganger større enn i bøker ($295\text{k}$), mens `fiskene` kun er dobbelt så stort ($96\text{k}$ vs. $50\text{k}$). Dermed dominerer yrkesordet *«en fisker»* i aviser ($\sim 50\text{–}55\text{ \%}$), mens flertall av dyret *«flere fisker»* dominerer i bøker ($\sim 50\text{–}60\text{ \%}$) – og i bøker øker andelen *«flere fisker»* fra $49{,}3\text{ \%}$ på 1950-tallet til $64{,}4\text{ \%}$ på 2010-tallet i takt med at yrkesgruppen *fiskere* omtales sjeldnere!

---

## 2026-10-23 (del 6) — Generell paradigme-dekomponerer (`sqlite/decomposer.py`) for ordboksredaktør-bruk

**Agent:** Antigravity (Gemini 4 Argon)

### Hva ble gjort
- Bygget modulen `sqlite/decomposer.py` med funksjonen `estimate_wordform_shares(oppslag)` som tar en hvilken som helst flertydig ordform i Norsk Ordbank og automatisk fordeler frekvensen mellom kandidat-lemmaene (`lemma_id`) ved å bruke de entydige ankerformene i resten av hvert paradigme.
- Testet algoritmen på 8 klassiske verb/substantiv-homografer i `nb_totals`:
  - **`fisker` ($1\,435\,424$):** `en fisker` 45,2 % ($649\text{k}$), `en fisk` 32,4 % ($465\text{k}$), `å fiske` 21,6 % ($311\text{k}$), `et fiske` 0,8 % ($11\text{k}$).
  - **`hatt` ($27\,128\,954$):** `å ha` (`perf-part`) 97,0 % ($26{,}3\text{ mill.}$), `en hatt` (`ent ub`, forankret i *hatten* $919\text{k}$, *hatter* $270\text{k}$, *hattene* $50\text{k}$) 3,0 % ($825\text{k}$).
  - **`møter` ($11\,218\,438$):** `å møte` (`pres`, forankret i *møtte* $5{,}55\text{ mill.}$, *møtt* $4{,}52\text{ mill.}$) 53,8 % ($6{,}04\text{ mill.}$), `et møte` (`fl ub`, forankret i *møtet* $7{,}03\text{ mill.}$, *møtene/møta* $1{,}41\text{ mill.}$) 46,2 % ($5{,}18\text{ mill.}$). Sum uavhengige estimater er $10{,}21\text{ mill.}$ mot observert $11{,}22\text{ mill.}$!
  - **`ønsker` ($25\,837\,609$):** `å ønske` (`pres`) 92,7 % ($23{,}96\text{ mill.}$), `et ønske` (`fl ub`, forankret i *ønskene* $117\text{k}$) 7,3 % ($1{,}88\text{ mill.}$).
  - **`landet` ($25\,566\,467$):** `et land` (`ent be`, forankret i *landene* $1{,}86\text{ mill.}$ + *land*) 89,8 % ($22{,}95\text{ mill.}$), `å lande` (`pret/perf`, forankret i *lande* $936\text{k}$, *lander* $308\text{k}$, *landes* $87\text{k}$) 10,2 % ($2{,}61\text{ mill.}$).
  - **`viser` ($29\,900\,136$):** `å vise` (`pres`) 99,7 %, `en viser` (`ent ub`) 0,3 % ($78\text{k}$), `ei vise` (`fl ub`) $< 0{,}1\text{ \%}$, `å visere` (`imp`) $\approx 0\text{ \%}$.
- Noterte også observasjonen om funksjonsords-bigrammer (*«å fiske»*, *«en fisker»*, *«et fiske»*): Mens `api.nb.no/dhlab/ngram_book` kun støtter unigrammer, støtter `sp_tjenester`-endepunktet bigrammer/trigrammer, som kan kombineres direkte med paradigme-estimatoren når to paradigmer deler *flere* celler (f.eks. verb *å møte* vs. subst. *et møte* i grunnformen *møte*).

---

## 2026-10-23 (del 7) — «Katt/hatt»-effekten: Bøyningsparadigmet som OCR- og støydetektor

**Agent:** Antigravity (Gemini 4 Argon)

### Hva ble gjort
- Sjekket brukerens observasjon om ordformen **«katt»** på 1950-tallet mot hele bøyningsparadigmet (`katt`, `katten`, `katter`, `kattene`) i bok- og aviskorpuset (`1948–1962`).

### Viktige funn
- I **aviskorpuset** (og i bokkorpuset i «normale» år som 1951, 1953 og 1959) ligger ubestemt entall `katt` helt stabilt på **38–43 %** av paradigmet (`katt / (katten + katter + kattene) ≈ 0,68`):
  - **1951 (bøker):** `katt` = 525, `katten+katter+kattene` = 761 $\rightarrow$ **`katt`-andel = 40,8 %** (`katt/rest = 0,69`)
  - **1953 (bøker):** `katt` = 550, `katten+katter+kattene` = 786 $\rightarrow$ **`katt`-andel = 41,2 %** (`katt/rest = 0,70`)
- I **1954–1958 (bøker)** spretter plutselig `katt` mer enn **3 ganger opp** til **1 742–1 962**, mens resten av paradigmet (`katten + katter + kattene`) ligger flatt på **790–1 080**:
  - **1954 (bøker):** `katt` = 1 816, `rest` = 952 $\rightarrow$ **`katt`-andel bykser til 65,6 %** (`katt/rest = 1,91`)!
  - **1958 (bøker):** `katt` = 1 758, `rest` = 790 $\rightarrow$ **`katt`-andel = 69,0 %** (`katt/rest = 2,23`)!
  - **1959 (bøker):** `katt` faller brått tilbake til 559, `rest` = 721 $\rightarrow$ **`katt`-andel = 43,7 %** (`katt/rest = 0,78`)!
- **Metodisk poeng for MONS:**
  - Fordi bøyningsprofilen i et paradigme normalt er tidsstabil, vil enhver brå økning i én enkelt ordform (`katt`) som *ikke* følges av resten av paradigmet (`katten`, `katter`, `kattene`), avsløre at økningen **ikke** handler om leksemet *katt*, men om en ekstern kilde som kun rammer akkurat den overflateformen — her OCR-feillesning av høyfrekvente ***«hatt»*** ($h \rightarrow k$).
  - Og enda bedre: Ut fra `katten + katter + kattene` ($952$ i 1954) kan vi faktisk **rense** kurven for `katt` i 1954 ved å estimere at $\sim 650$ treff ($0{,}68 \times 952$) var ekte katter, mens de resterende $\sim 1\,166$ treffene ($\sim 64\text{ \%}$ av «katt» det året!) var feilleste *hatt*!

---

## 2026-10-23 (del 8) — Paradigme-grafen ($a \stackrel{n}{\text{---}} b$): Global topologi og fler-hopps-dekomponering

**Agent:** Antigravity (Gemini 4 Argon)

### Hva ble gjort
- Opprettet `sqlite/paradigm_graph.py` som bygger den fulle **paradigme-grafen** for Norsk Ordbank ($151\,648$ lemmaer innenfor substantiv, verb og adjektiv), der nodene er paradigmer (`lemma_id`) og en kant $a \stackrel{n}{\text{---}} b$ kobler to paradigmer hvis de deler $n \ge 1$ bøyningsformer (`oppslag`).
- Analyserte både den lokale komponenten rundt «fisker» og den globale fordelingen av komponentstørrelser, kantvekter $n$ og maksimal bredde (BFS-hopp) i hele ordforrådet.

### Viktige funn
1. **«Fisker»-komponenten er en lukket 4-node-graf ($K_4$) uten lekkasje ut:**
   - Komponenten rundt `fisker` består av nøyaktig 4 lemmaer og 6 kanter:
     - `en fisker (17348)` $\stackrel{n=1}{\text{---}}$ `en fisk (17301)` (`['fisker']`)
     - `en fisker (17348)` $\stackrel{n=1}{\text{---}}$ `å fiske (17307)` (`['fisker']`)
     - `en fisker (17348)` $\stackrel{n=1}{\text{---}}$ `et fiske (17310)` (`['fisker']`)
     - `en fisk (17301)` $\stackrel{n=2}{\text{---}}$ `å fiske (17307)` (`['fisk', 'fisker']`)
     - `en fisk (17301)` $\stackrel{n=2}{\text{---}}$ `et fiske (17310)` (`['fiskene', 'fisker']`)
     - `å fiske (17307)` $\stackrel{n=4}{\text{---}}$ `et fiske (17310)` (`['fiska', 'fiske', 'fisker', 'fisket']`)
   - **Analytisk verdi av graf-hoppet (`fisker` $\rightarrow$ `å fiske` $\rightarrow$ `et fiske`):**
     - Noden `et fiske (17310)` har **0 egne entydige former** (alle dens 5 former deles med `å fiske` og `en fisk`).
     - Men fordi nabo-noden `å fiske (17307)` har det entydige ankeret `fiskes` ($155\,338$) og `fiskende` ($9\,149$), vet vi at selve verbet *å fiske* bare står for rundt $600\text{–}800\text{k}$ av `fiske` ($3{,}74\text{ mill.}$) og $450\text{–}600\text{k}$ av `fisket` ($2{,}84\text{ mill.}$). Dermed kan vi via **ett graf-hopp** utlede at brorparten av `fiske` ($\sim 3{,}0\text{ mill.}$) og `fisket` ($\sim 2{,}3\text{ mill.}$) faktisk tilhører substantivet ***«et fiske / dette fisket»***!
2. **Global topologi i Norsk Ordbank ($151\,648$ lemmaer): Ingen «giant component»!**
   - **Størrelse 1 (helt isolerte / 100 % entydige lemmaer):** $132\,564$ lemmaer (**87,4 %**)
   - **Størrelse 2 (par $a \stackrel{n}{\text{---}} b$):** $4\,817$ komponenter = $9\,634$ lemmaer (**6,4 %**)
   - **Størrelse 3 (triangler/3-kjeder):** $1\,181$ komponenter = $3\,543$ lemmaer (**2,3 %**)
   - **Størrelse 4 (f.eks. `fisker`-gruppen):** $452$ komponenter = $1\,808$ lemmaer (**1,2 %**)
   - **Størrelse 5–10:** $544$ komponenter = $3\,316$ lemmaer (**2,2 %**)
   - **Størrelse $> 10$ (maks 54 lemmaer, BFS-dybde 3–7 hopp):** kun $47$ komponenter = $783$ lemmaer (**0,5 %**, sentrert rundt korte lydlige klynger som *li/lide/led/lede* og *ro/roe/ror*).
   - **Hovedkonklusjon:** Hele **97,3 % av det norske ordforrådet** befinner seg i små, lukkede paradigme-komponenter på **1 til 4 lemmaer**. Det betyr at dekomponering via paradigme-grafen er et lokalt, velavgrenset ligningssystem nesten overalt i språket!

---

## 2026-10-23 (del 9) — Git-oppsett og `.gitignore` (inkl. fremtidig PWA-støtte)

**Agent:** Antigravity (Gemini 4 Argon)

### Hva ble gjort
- Opprettet `.gitignore` som ekskluderer store rådata (`20220201_norsk_ordbank_nob_2005/`, >100 MB), genererte SQLite-databaser (`*.db`, `*.db-wal`, `*.db-shm`), Python/Jupyter-artefakter og fremtidige PWA-/frontend-byggefiler (`node_modules/`, `dist/`, `build/`, `.vite/`, `.svelte-kit/`, `.next/`, genererte Workbox/Service Worker-bundles, `.env`-filer og `.DS_Store`).
- Oppdaterte `sqlite/build_db.py` slik at det også laster ned og bygger tabellen `nb_totals` automatisk ved nybygging av `sqlite/ordbank.db`.
- Staget prosjektfilene (`git add`) klare for første commit/push.
- Satt opp **Git LFS** (`git lfs track "sqlite/ordbank.db"`) og un-ignorert `!sqlite/ordbank.db` i `.gitignore`, slik at den ferdigbygde SQLite-databasen (`sqlite/ordbank.db`, inkl. `nb_totals`) også er direkte tilgjengelig i GitHub-repoet.

---

## 2026-10-23 (del 10) — Rapport om verbtyper, sekundære rangeringer (`1. > 2. > 3.`) og aksjonsart (`rapport_verbtyper.md`)

**Agent:** Antigravity (Gemini 4 Argon)

### Hva ble gjort
- Sjekket innkommende endringer fra medforfatter (`notebooks/00_dataoppslag.ipynb` merget via PR #1).
- Analyserte alle 6 mulige rangeringer (permutasjoner av `inf`, `pres`, `pret`) på tvers av $N = 606$ helt lemma-entydige verb med 4 distinkte kjerneformer (`pret != perf-part`, $\ge 100\,000$ treff i `nb_totals`) samt for våre 30 kjerneverb over 71 enkeltår (1950–2020).
- Skrev delrapporten **`rapport_verbtyper.md`** i prosjektroten.

### Viktige funn
1. **Gir 1. plassen automatisk rangen av de andre formene, eller finnes det sekundær variasjon?**
   - **Begge deler:** 1. plassen låser *ikke* 2. og 3. plass automatisk (alle 6 permutasjoner av `inf`, `pres`, `pret` brukes), **men** det er en sterk asymmetri der **`inf` inntar 2. plass for ~65–70 % av verbene** når `pret` eller `pres` er på topp:
     - **1A `inf > pres > pret` (30,0 % av verbene):** Prosessuelle/diskursive aktivitetsverb (*stille, forklare, lese, forstå, spise, gjøre, finne*).
     - **1B `inf > pret > pres` (21,3 %):** Teliske/resultative handlingsverb (*ta, sette, kjøpe, snakke, fiske, skaffe, oppnå*).
     - **2A `pret > inf > pres` (17,5 % — utgjør 70,7 % av verb med `pret` på topp):** Intensjonale hendelsesverb som også styres av modalverb (*vinne, legge, si, tape, bygge, forsøke, vedta, forlate*).
     - **2B `pret > pres > inf` (7,3 % — utgjør 29,3 % av verb med `pret` på topp):** Ikke-intensjonale overgangsverb og narrative regiverb som sjelden planlegges i infinitiv (*dø, svare, komme, gå, smile, rope, forsvinne, ankomme*).
     - **3A `pres > inf > pret` (14,9 % — utgjør 62,1 % av verb med `pres` på topp):** Relasjonelle og ekspositoriske verb (*bety, fungere, innebære, oppleve, leve, fortelle*).
     - **3B `pres > pret > inf` (9,1 % — utgjør 37,9 % av verb med `pres` på topp):** Stative tilstandsverb som beskriver nåtidig eller fortidig tilstand og sjelden står i infinitiv (*ha, vite, ligge, trenge, bestå, foreligge*).
2. **Stabilitet av hele rangeringen (`1. > 2. > 3.`) gjennom 71 år (1950–2020):**
   - For verb som *vinne*, *legge*, *dø*, *svare*, *komme*, *ha* og *vite* er **hele rekkefølgen (`1. > 2. > 3.`) identisk i 100,0 % av årene (71 av 71 år)** fra 1950 til 2020!
3. **Litteraturforankring lagt til i `rapport_verbtyper.md`:**
   - Knyttet funnene til den internasjonale litteraturen om *inflectional profiles / focal forms* (Karlsson 1986, 2000; Arppe 2006), *grammatical profiles* (Janda & Lyashevskaya 2011; Newman 2008) og paradigme-entropi i mentalt leksikon (Milin, Filipović Đurđević & Baayen 2009), og presiserte hva som er genuint nytt i vår metode (70-årig diakron rang-stabilitet, de 6 permutasjonene av `inf/pres/pret`, «baklengs» bruk av profiler til å dekomponere rå n-grammer/OCR-støy/leksikalisering uten POS-tagget korpus, samt den globale paradigme-grafen over Norsk Ordbank).

---

## 2026-10-23 (del 10) — Startnotebook for dataoppslag (`notebooks/00_dataoppslag.ipynb`)

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Opprettet `notebooks/00_dataoppslag.ipynb`: én samlet inngang som importerer de viktigste datafunksjonene fra `sqlite/` og viser ett eksempel på hver:
  - `lookup_wordform`, `get_paradigm`, `get_verb_profile_forms`, `get_noun_profile_forms`, `find_anchor_forms` (`sqlite/queries.py`)
  - korpusfrekvenser fra `nb_totals` (liten hjelper `frekvens()` i notebooken) og fri SQL til DataFrame (`sql()`)
  - `estimate_wordform_shares` (`sqlite/decomposer.py`)
  - `build_paradigm_graph` / `inspect_component` (`sqlite/paradigm_graph.py`)
  - `fetch_ngram_dhlab`, `fetch_ngram_sp`, `compute_paradigm_profile` (`sqlite/ngram.py`, krever nett første gang)
- Alle kodeceller er kjørt gjennom uten feil (grafbygging ~4 s, n-gram-kall ~1–4 s uten cache).

### Tekniske observasjoner
- Nøkkelen `"target_ labels"` i `sqlite/decomposer.py` (linje 71, 75, 207) har et mellomrom i navnet. Den er konsistent brukt og virker, men bør trolig renames til `target_labels`.
- Rå n-gram for `gå`/`går` inkluderer hhv. imperativ og *«i går»*, så andelsplottet i seksjon 8 er en råfordeling av formene, ikke en leksemprofil.

### Neste steg
- Bruke notebooken som mal for nye analysenotebooks (02, 03, …).

---

## 2026-10-23 (del 11) — Paradigmedekning og overlevelse i enkeltbøker (`sqlite/book_dispersion.py`)

**Agent:** Antigravity (Gemini 4 Argon)

### Hva ble gjort
- Opprettet `sqlite/book_dispersion.py` som henter enkeltbok-korpus via `https://api.nb.no/dhlab/build_corpus` og eksakte dokumentfrekvenser per bok via `https://api.nb.no/dhlab/frequencies` (merk teknisk detalj: `/dhlab/frequencies` krever `"cutoff": 1` i JSON-payloaden for å unngå HTTP 500).
- Kjørte en systematisk analyse av 400 digitaliserte bokmålsbøker (1980–2020: 200 *Skjønnlitteratur* + 200 *Faglitteratur*) for 20 representative verb (fordelt på alle de 6 undertypene i `rapport_verbtyper.md`) og 12 substantiv (fordelt på `ent_ub`-, `ent_be`- og `fl_ub`-profiler).

### Viktige funn
1. **Enkeltbøker har sjelden med hele paradigmet — selv når ordet brukes flere ganger i boka:**
   - **Verb (3 former: `inf, pres, pret`, $N=6\,480$ bok–verb-par):**
     - Ved **2 forekomster** av verbet i en bok har **57,4 %** av bøkene kun **1 form** (samme form gjentas!), og 42,6 % har 2 former.
     - Ved **3–5 forekomster** i boka mangler fortsatt minst én form i **86,2 % av bøkene** (kun 1 form: 27,6 %, 2 former: 58,6 %, alle 3 former: **kun 13,8 %**).
     - Ved **6–15 forekomster** i boka mangler fortsatt minst én form i **53,6 % av bøkene** (alle 3 former: 46,4 %).
   - **Substantiv (4 former: `ent_ub, ent_be, fl_ub, fl_be`, $N=2\,548$ bok–substantiv-par):**
     - Ved **3–5 forekomster** i en bok har **kun 0,9 %** av bøkene alle 4 former (31,2 % har 1 form, 53,6 % har 2 former, 14,3 % har 3 former).
     - Selv på tvers av hele bøker har vanlige substantiv som *eple* (58 % kun 1 form, **7 %** alle 4), *buss* (41 % kun 1 form, **7 %** alle 4), *kirke* (46 % kun 1 form, **13 %** alle 4), *sol* (37 % 1 form, 55 % 2 former, **1 %** alle 4) og *forelder* (39 % 1 form, 50 % 2 former, **1 %** alle 4) nesten aldri hele paradigmet realisert i én bok.
2. **Hvilken del av paradigmet blir med? («Overlevelsesskala» styrt av den globale profilen):**
   - Når en bok **kun har 1 form** av et leksem, følger valget av form leksemets globale rangering (`1. > 2. > 3. (> 4.)`):
     - For **verb ($N=1\,145$ enkeltbok-forekomster med kun 1 form)** er den enslige formen verbets globale **#1-form i 57,2 %** av bøkene, **#2-formen i 26,1 %**, og **#3-formen i kun 16,7 %**.
     - Når en bok har **nøyaktig 2 former** av et verb ($N=1\,727$), er global **#1-form med i 81,4 %** av bøkene (52,3 % er paret `{#1, #2}`, 29,1 % er `{#1, #3}`, og bare 18,6 % er `{#2, #3}`).
     - For **substantiv ($N=813$ enkeltbok-forekomster med kun 1 form)** er den enslige formen substantivets globale **#1-form i 56,0 %**, **#2-form i 32,5 %** (til sammen **88,5 %** for topp-2!), **#3-form i 9,7 %**, og **#4-form i kun 1,8 %**.
   - Tydelige eksempler ved kun 1 form i boka: *bety* -> 91 % *betyr*; *gjelde* -> 79 % *gjelder*; *legge* -> 78 % *la*; *vinne* -> 74 % *vant*; *forklare* -> 68 % *forklare*; *dag* -> 83 % *dag*; *politi* -> 80 % *politiet*; *sol* -> 76 % *sola/solen*; *politiker* -> 61 % *politikere*.
3. **Dispersjon vs. «burstiness» (klumping) og sjangereffekter (Skjønnlitteratur vs. Faglitteratur):**
   - Preteritum har høyere lokal tetthet («burstiness») i narrative bøker, mens infinitiv og presens har høyere dokumentdispersjon på tvers av sjangre (f.eks. har *si* flest tokens i `pret` *sa* totalt pga. skjønnlitteratur (70 %), men høyere dokumentfrekvens i `inf` *si* (93 % av bøkene mot 84 % for *sa*) fordi *å si / det vil si* brukes i både sakprosa og skjønnlitteratur).
   - For verb med `inf` på topp (som *spise* og *lese*) holder `inf` 1.-plassen i både skjønnlitteratur og faglitteratur, men **2.- og 3.-plassen bytter plass etter sjanger**: skjønnlitteratur gir `inf > pret > pres` (*spise 49 % > spiste 33 % > spiser 18 %*), mens faglitteratur gir `inf > pres > pret` (*spise 53 % > spiser 33 % > spiste 14 %*).

---

## 2026-10-25 (del 12) — Kryss-POS-filtrering av gullstandard (Sett A / Sett B) og dekomponering av *«dø / dør»* i `rapport_verbtyper.md`

**Agent:** Antigravity (Gemini 4 Argon) — etter handoff/fagfellevurdering fra Gemini-chat

### Hva ble gjort
- Gjennomførte full kryss-POS-revisjon av både makroutvalget ($N=606$) og kjerneverbtabellen i `rapport_verbtyper.md` (seksjon 2, 3, 4 og 7.2):
  1. **Sett A — Streng gullstandard (100 % globalt POS-isolerte i hele Norsk Ordbank):**
     - Verifiserte at de opprinnelige $N=606$ verbene allerede krevde `ordform_flertydighet.antall_lemma_id = 1` på tvers av *alle* ordklasser for `(inf, pres, pret)`.
     - Utvidet kravet til også å gjelde 4. form (`perf-part`, `boy_nummer = 5`), slik at også leksikaliserte partisipp-adjektiver (*forlatt, opptatt, forbudt, betjent*) ekskluderes. Dette gir **$N = 580$ verb** (og **$N = 533$ verb** når alle 4 kjerneformer i tillegg kreves belagt $>0$ i `nb_totals`, som fjerner arkaiske riksmålsformer som *tilstede*).
     - Fordelingen på de 6 undertypene (`1A–3B`) i det 100 % POS-isolerte Sett A ($N=580$) er praktisk talt identisk med $N=606$ (maks $0{,}4$ prosentpoeng forskjell: `1A` 29,8 %, `1B` 21,2 %, `2A` 17,9 %, `2B` 7,2 %, `3A` 14,8 %, `3B` 9,0 %).
  2. **To-trinns vask i seksjon 4 (Sett A vs. Sett B):**
     - Luket ut alle støy-kandidater med reell kryss-POS-homografi fra gullstandard-tabellen (*dø, stille, fiske, svare, selge, leve, vinne, legge, bygge, sette, tape*) og erstattet dem med 100 % globalt kollisjonsfrie **Sett A**-verb (*vurdere, forstå, oppnå, utføre, foreta, bidra, diskutere, forklare, undersøke, innføre, ta, overta, vedta, forlate, gjenta, skjule, forsøke, forsvinne, ankomme, rope, smile, omkomme, bety, fungere, oppleve, innebære, anbefale, trenge, bestå, foregå, foreligge*), hvorav bl.a. *vurdere, undersøke, overta, forsvinne, ankomme, rope, trenge, bestå* har **100,0 % full-rang-stabilitet (71 av 71 år)** i 1950–2020.
     - Flagget de resterende praktisk rene høyfrekvente kjerneverbene eksplisitt som **Sett B** med angivelse av hvilken ordform som har en teknisk ordbokskollisjon.
  3. **Glansnummer i seksjon 7.2 — Dekomponering av `dø` (verb) vs. `dør` (substantiv):**
     - Brukte de entydige substantiv-ankerformene (`døren + døra` = $1{,}65\text{M}$ i bøker / $7{,}02\text{M}$ i `nb_totals`, `dører`, `dørene`) og `estimate_wordform_shares("dør")` i `sqlite/decomposer.py` til å dekomponere strengen `«dør»` i **71,4 % substantiv (`en/ei dør`)** og **28,6 % verb (`han/hun dør`)**.
     - **Hovedfunn:** Når substantivet *en/ei dør* trekkes fra, faller presensandelen til verbet *dø* i bokkorpuset (1950–2020) fra **20,6 %** ned til **6,9 %** ($\approx 192\,900$ mot $492\,694$ for infinitiv *dø*), slik at **`dø` bytter verbtype fra 2B (`pret > pres > inf`) til 2A (`pret > inf > pres`: `75,4 % > 17,7 % > 6,9 %`)**!
- Fikset også skrivefeilen `"target_ labels"` $\rightarrow$ `"target_labels"` i `sqlite/decomposer.py` (påpekt i del 10).

### Neste steg (lagt til i del 13, manglet i del 12)
- Se del 13.

---

## 2026-11-17 (del 13) — Statussjekk, forbehold om «døde» og plan for MONS-presentasjonen

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Sjekket arbeidstreet på `rapport-verbtyper`: alt fra del 12 var allerede committet og pushet (ingen uferdige endringer). Det som manglet var «Neste steg» i loggoppføringen for del 12.
- Kontrollerte tallene for *dø/dør* i `rapport_verbtyper.md` §7.2 mot `estimate_wordform_shares("dør")`: andelene 71,4 % / 28,6 % og `nb_totals`-tallene stemmer.
- **Fant en feil i resonnementet:** `«døde»` har `antall_lemma_id = 3` (pret. av *dø*, adj. *død* be/fl, verbet *døde*). Preteritumstallet for *dø* inneholder altså adjektivbruk (*de døde*). `estimate_wordform_shares("døde")` gir verbet 100 % fordi `sqlite/decomposer.py` ikke har ankerregler for adjektiv (adj.-kandidaten får 0 selv om `dødt` er entydig, 343 621).
- Sensitivitetsoverslag med `-e`/`-t`-forholdet fra entydige adjektiv (*blinde/blindt* 4,7; *syke/sykt* ≈ 10; *gamle/gammelt* 14): adjektivet utgjør 13–38 % av *døde*; *dø* får `pret` 69–76 % > `inf` 18–23 % > `pres` 7–9 %. **2A-konklusjonen holder, men prosenttallene i §7.2 punkt 4 er et øvre anslag for `pret`.** Lagt inn som punkt 5 i §7.2.
- Opprettet `tekst/mons_presentasjon_plan.md`: forslag til lysbilderekke (14 lysbilder) med kilde/status per lysbilde, og prioritert liste over hull.

### Viktige observasjoner
- Sett A-tallene (N = 606 / 580 / 533, fordeling 1A–3B) finnes ikke som kjørbart skript; de ble regnet ad hoc.
- Dekomponereren overestimerer før normalisering: for *dør* summerer de ukappede estimatene til 4,7 M mot 3,4 M observert.
- Referansen Milin, Filipović Đurđević & Baayen (2009), «Paradigms bit by bit», er trolig et bokkapittel i *Analogy in Grammar* (OUP), ikke *Cognitive Linguistics* 20(1). Må verifiseres.

### Neste steg (frem mot MONS, se `tekst/mons_presentasjon_plan.md`)
1. Substantivprofiler: typefordeling og stabilitet tilsvarende verbrapporten (største faglige hull).
2. Figurer: ternærplott for Sett A, tidsserier for stabile verb, *dø* før/etter dekomponering, *fisker* over tid, paradigmedekning i enkeltbøker.
3. Skript som reproduserer Sett A og typefordelingen (`sqlite/verbtyper.py`).
4. Validering av dekomponereren mot kjent fasit, og adjektivankre (løser *døde*).
5. Verifisere referansene i §7.1.

---

## 2026-11-17 (del 14) — Skjelett for MONS-presentasjonen (`tekst/mons_presentasjon.pptx`)

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Bygget et skjelett med 14 lysbilder etter planen i `tekst/mons_presentasjon_plan.md`. Generator: `tekst/deck/build_deck.js` (pptxgenjs 3.12.0, MIT-lisens). Kjøres med `NODE_PATH=<node_modules> node tekst/deck/build_deck.js`.
- Ferdige data er lagt inn som native PowerPoint-diagrammer: de seks verbtypene (lysbilde 6), enkeltbøker med bare én form (9), og *dø* før/etter dekomponering (10). Tallene kommer fra `rapport_verbtyper.md` og logg del 11.
- Innhold som mangler er markert med sandfargede «MANGLER»-felt og statusmerke («UTKAST»/«MANGLER») øverst til høyre. Kilder og forbehold står i talenotatene for hvert lysbilde.
- Filen består `validate.py`. Den er sjekket visuelt via Keynote-eksport, men Keynote viser ikke pptxgenjs-diagrammer, så diagrammene er bare kontrollert på data (python-pptx), ikke visuelt.

### Viktige observasjoner
- **Abstractet stemmer ikke med dataene for *vite*:** abstractet sier at infinitiv *vite* dominerer, men bokkorpuset gir *vet* 55 % > *visste* 26 % > *vite* 19 %. Lysbilde 2 bruker dataene; abstract og foredrag må samkjøres.

### Neste steg
- Åpne decket i PowerPoint og sjekke diagrammene.
- Fylle «MANGLER»-feltene i prioritert rekkefølge (se `tekst/mons_presentasjon_plan.md`). Endringer gjøres i `build_deck.js`, ikke direkte i .pptx, så lenge decket genereres.

---

## 2026-11-17 (del 15) — Substantivprofiler: gullstandard, typer og stabilitet (`rapport_substantivtyper.md`)

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Nytt skript `sqlite/substantivtyper.py` (`python3 -m sqlite.substantivtyper`, `--offline` for bare `nb_totals`). Det bygger gullstandarden, henter n-gram for bokkorpuset 1950–2020 (ca. 26 000 ordformer; lokal cache i `ngram_cache.db`, som ikke er i git — første kjøring på en ny maskin tar noen minutter), og regner hovedtyper, full rangering og årlig rang-stabilitet. Per-lemma-resultater: `resultater/substantivtyper.tsv`.
- Gullstandard (Sett A, substantiv): alle fire kjerneformer entydige i hele Ordbanken, internt distinkte kategorier, ≥ 100 000 treff i `nb_totals`, alle fire belagt i bokkorpuset → **N = 5 799**. Bokstavnavn, forkortelser og 25 håndplukkede falske venner (*nogen, vor, jan, used, forst* …) er filtrert bort (`FALSKE_VENNER`).
- Skrev `rapport_substantivtyper.md`. Oppdaterte lysbilde 2 og 8 i `tekst/mons_presentasjon.pptx` (via `tekst/deck/build_deck.js`) og planen.

### Viktige funn
- Hovedtyper: `ent_ub` 67,1 %, `ent_be` 16,5 %, `fl_ub` 14,5 %, `fl_be` 1,9 %. Alle 24 rekkefølger er belagt; tre dekker 74 %.
- **Tall før bestemthet:** 2. plass er nesten alltid samme tall (`ent_be` på topp → `ent_ub` 91 %; `ent_ub` → `ent_be` 72 %; `fl_be` → `fl_ub` 82 %). Unntak: `fl_ub` på topp → `ent_ub` 71,5 % (*en person / tre personer*).
- Stabilitet (N = 4 355 med nok data): samme topp i alle 71 år for 53,1 %; hele firerangeringen uendret i 71/71 år for 7,9 % (*tid, utvikling, sommer, seng, medlem, utgift*), median 78,9 %.
- **Abstractet stemmer ikke for *eple*:** epler 45 % > eple 30 % > eplet 11 % i bokkorpuset; `nb_totals` samme vei. *buss* stemmer (bussen på topp), men alle formene er formelt flertydige.
- `nb_totals` mangler sjeldne ordformer; krav om alle former der halverer utvalget. Kravet ble derfor lagt på bokkorpuset.

### Neste steg
- Samkjøre abstract og foredrag for *eple* og *vite*.
- Teste semantiske forklaringer (genus, tellbarhet, animathet) og skille simplex fra sammensetninger (`leddanalyse`).
- Figurer: tidsserier for noen stabile substantiv, ev. sammen med verbene på lysbilde 7.

---

## 2026-11-19 (del 16) — Skript som gjenskaper verbtallene (`sqlite/verbtyper.py`)

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Nytt skript `sqlite/verbtyper.py` (`python3 -m sqlite.verbtyper`, `--offline` for bare `nb_totals`). Det bygger Sett A, regner de seks typene, snittprofiler, 2.-plass-fordeling og stabilitet, og skriver `resultater/verbtyper.tsv`.
- **Alle tall i `rapport_verbtyper.md` §2–4 gjenskapes nøyaktig:** N = 606 / 580 / 533, typefordelingen for alle tre utvalg, snittprofilene og hele §4-tabellen (profiler, topp- og full-rang-stabilitet for alle 41 verb).
- Presise kriterier (rapporten var uklar på dette): 100 000-grensen gjelder **inf + pres + pret** i `nb_totals`; «internt distinkt» betyr at ingen form står i to av de fire kategoriene. Skrevet inn i rapporten §2.
- Rapporten §3 og §4 fikk tillegg (se under); lysbilde 5–7 i decket oppdatert; planen oppdatert (hull 3 løst).

### Viktige funn
- **Typefordelingen i §3 er regnet på `nb_totals` (hele NB), ikke på bokkorpuset 1950–2020 som resten av rapporten.** I bokkorpuset: 1A 26,9 / 1B 27,1 / 2A 20,2 / 2B 7,4 / 3A 12,2 / 3B 6,2 %. Inf-på-2.-plass-funnet holder (73,1 % / 66,4 %), men 1A/1B deler seg nesten likt (49,8 / 50,2 %) i stedet for 58,4 / 41,6 %.
- **Stabilitet for hele Sett A:** av 569 verb belagt alle 71 år har 260 (45,7 %) samme topp hvert år og 80 (14,1 %) samme fullstendige rekkefølge. Verbene med 100 % i §4 er utvalgte, ikke typiske.
- Sett A inneholder noen ikke-standard former (*tilstede, sæte, meine*); marginal effekt, men ikke bruk dem som eksempler.
- *forlate* er formelt ikke i Sett A (580) fordi *forlatt* også er adjektiv; rapporten merker den allerede «Sett A\*».

### Neste steg
- Bestemme korpus for foredraget (bokkorpuset 1950–2020 anbefales, siden stabilitet og eksempler bruker det) og oppdatere lysbilde 6 og §3 deretter.
- Figurer (hull 2), validering av dekomponereren (hull 4), referanser (hull 6).

---

## 2026-11-19 (del 17) — Bokkorpuset 1950–2020 som felles korpus for foredraget

**Agent:** Claude Code (Claude Opus 5.5)

### Beslutning
- Det ble besluttet å bruke bokkorpuset 1950–2020 (`dhlab ngram_book`) for alle verb- og substantivtall i foredraget. `nb_totals` brukes fortsatt til å velge ut verb og substantiv (100 000-grensen), men ikke til profilene.

### Hva ble gjort
- `sqlite/verbtyper.py`: henter bokprofiler for alle 606 verb og skriver ut typefordelingen i bokkorpuset for N = 606 / 580 / 533; `nb_totals` vises etterpå til sammenligning (`--offline` gir bare `nb_totals`).
- `rapport_verbtyper.md` §3 skrevet om på bokkorpuset: hovedtyper inf 54,0 / pret 27,6 / pres 18,4 %; 1A 26,9 / 1B 27,1 / 2A 20,2 / 2B 7,4 / 3A 12,2 / 3B 6,2 %; nye snittprofiler og eksempler; sammenligningstabell med `nb_totals`.
- Lysbilde 6 i decket oppdatert (diagram, tittel, 73 % / 66 %, talenotat). Planen oppdatert.

### Merk
- Når `inf` er på topp, deler verbene seg likt mellom 1A og 1B (49,8 / 50,2 %) i bokkorpuset. Påstander om at 1A er klart vanligere enn 1B gjelder bare `nb_totals`.
- Eldre loggoppføringer (del 9, 12) har `nb_totals`-tallene; de er historikk og er ikke endret.
- §5 i rapporten (perf-part og -ende) er ikke regnet om; korpuset der er ikke dokumentert.

---

## 2026-11-20 (del 18) — Figurer til decket

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Nytt skript `sqlite/figurer.py` (`python3 -m sqlite.figurer`, krever matplotlib og numpy) lager tre PNG-er i `tekst/figurer/`, alle på bokkorpuset 1950–2020:
  - `verb_ternaer.png`: de 580 verbene i Sett A som punkter i trekanten inf/pres/pret, farget etter formen på topp, med utvalgte verb merket.
  - `verb_stabilitet.png`: andel per form per år for *vurdere, undersøke, forsvinne, trenge*.
  - `fisker_over_tid.png`: «fisker» fordelt på *en fisker*, *fisk* (flertall) og *å fiske* (presens) per år, med 5 års glidende snitt.
- `sqlite/decompose_fisker.py` returnerer nå forholdstallene sine, slik at figurskriptet kan bruke dem år for år. Utskriften er uendret.
- Decket: nytt lysbilde 7 med trekanten (15 lysbilder totalt); figurer på stabilitetslysbildet (8) og *fisker*-lysbildet (12); søylene på lysbilde 6 bruker samme formfarger. Formfargene er inf `B5482F`, pres `3D5A98`, pret `2A9D8F` (sjekket for fargeblindhet; temaets `4A4E69`/`4F7C7A` var for like).
- Planen er oppdatert (hull 2 stort sett løst, hull 7 delvis).

### Funn
- *fisker* 1950 / 1985 / 2020: en fisker 57 / 55 / 51 %, fisk (fl) 33 / 33 / 42 %, å fiske 11 / 12 / 7 %.
- **Advarsel:** summen av de ukappede anslagene er median 2,0 × observert «fisker» i bokkorpuset (spenn 0,8–3,0). Forholdstallene er anslått på `nb_totals` og overført til bokkorpuset. Andelene er normalisert, men nivået er uvalidert. Dette er markert på lysbildet og styrker behovet for hull 4.
- Stabil rangering betyr ikke stabile andeler: *vurdere* går fra ca. 80 til 63 % infinitiv og *trenger* fra ca. 50 til 70 % presens, mens rekkefølgen er den samme i alle 71 år. Det er et poeng for foredraget.

### Neste steg
- Valider dekomponereren (hull 4, lysbilde 13). Se særlig hvorfor anslagene for *fisker* blir for høye.
- Figur for paradigmegrafen (lysbilde 4), referanser (hull 6).

---

## 2026-11-20 (del 19) — Validering av dekomponereren

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- `sqlite/decomposer.py`: anslagsregelen er skilt ut som den rene funksjonen `estimate_from_slots`. Utskriften fra `python3 -m sqlite.decomposer` er identisk med før.
- Nytt skript `sqlite/valider_dekomponering.py` validerer på gullstandardene i `nb_totals` (2 772 substantiv, 533 verb):
  - Test 1 holder én kategori ute og anslår den fra resten av paradigmet.
  - Test 2 lager 3 000 kunstige homografer per type (fl ub + pres, ent be + pret, ent ub + inf, ent ub + pres).
  - Tre metoder sammenlignes: dagens faste regler, lært medianforhold og log-regresjon, de to siste med 5-delt kryssvalidering.
  - Resultatene skrives til `resultater/dekomponering_validering.tsv`.
- `sqlite/decompose_fisker.py`: ny `book_decomposition()` som lærer forholdstallene i bokkorpuset. `fisker_over_tid.png` viser nå begge variantene.
- Ny rapport `rapport_dekomponering_validering.md`. I decket er lysbilde 13 fylt ut (diagram og tall), lysbilde 12 har ny figur og ny merknad, og talenotatet på lysbilde 10 er oppdatert. Planen er oppdatert (hull 4 løst).

### Funn
- Én form anslått fra resten av paradigmet bommer typisk med en faktor på 1,6–2 med log-regresjon og 1,7–2,7 med reglene.
- Kunstige homografer: med log-regresjon er leksemet i flertall riktig i 78–80 % av tilfellene, med median feil 10–11 pp og 90-persentil rundt 30 pp. Reglene gir 66–76 % og 13–17 pp.
- Reglene er skjeve: `ent be` og `pret` overvurderes med omtrent en faktor 2, mens `ent ub` (×0,6) og `perf-part` (×0,5) undervurderes. For dør-typen (ent ub + pres) blir substantivandelen 13 pp for lav, så 71 % substantiv for «dør» er trolig et lavt anslag.
- *fisker*: forholdstall lært i `nb_totals` passer ikke for bøker, der *fiskene* er relativt nesten dobbelt så vanlig. Med tall lært i bokkorpuset er *en fisker* 14–21 %, mot ca. 50 % med de overførte tallene. Valget av referansegruppe flytter anslaget for *en fisker* mellom 39 000 og 322 000, mens det er observert 224 000 «fisker». Bare økningen for *fisk* (flertall) er robust.

### Neste steg
- Bytte reglene i `decomposer.py` ut med log-regresjon lært i samme korpus, og regne *dør* på nytt (lysbilde 10 og rapport §7.2).
- Adjektivandelen av «døde» (hull 5), referanser (hull 6) og figur for paradigmegrafen.

---

## 2026-11-20 (del 20) — Log-regresjon som standard i dekomponereren; *dør* regnet om

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- `sqlite/decomposer.py`:
  - `estimate_wordform_shares(oppslag, corpus="nb_totals"|"book", method="logreg"|"regler")` bruker nå log-regresjon som standard. Regresjonen er lært på gullstandarden (substantiv; Sett A for verb) i samme korpus som frekvensene.
  - Nye hjelpefunksjoner: `corpus_freqs`, `gold_profiles`, `fit_logreg` og `estimate_logreg`.
  - De gamle reglene brukes som reserve når det finnes færre enn to helt entydige ankerkategorier, eller når mål-kategorien ligger utenfor gullstandarden. Forklaringsteksten sier da «regler (reserve)».
  - `--metode regler` gir nøyaktig samme andeler som før omleggingen (sjekket med diff).
  - Ny kommandolinje: `python3 -m sqlite.decomposer [ord ...] --korpus book --metode logreg`.
- `rapport_verbtyper.md` §7.2 punkt 3–5, lysbilde 10, `rapport_dekomponering_validering.md` (ny §6) og planen er oppdatert.

### Funn
- *dør* i bokkorpuset: **63,5 % substantiv / 36,5 % verb**. Før var det 71,4 / 28,6 %, med faste regler lært på `nb_totals`. Summen av de ukappede anslagene er 1,05 × observert.
- Profilen til *dø* etter dekomponering er nå pret 74,0 / inf 17,4 / pres 8,7 % (2A). Med adjektivkorreksjon på 13–38 % av «døde» blir den 64–71 / 19–24 / 10–12 %. For at pres skal komme over inf, måtte anslaget for verbandelen bomme med 36 pp.
- **Rettelse til del 19:** der står det at 71 % substantiv for «dør» trolig er for lavt, fordi reglene i snitt undervurderer substantivet med 13 pp for denne typen. For «dør» gikk anslaget likevel *ned*. Skjevheten gjelder typen i snitt, ikke hvert enkelt ord.
- Delvis entydige ankre og bare én ankerkategori ga åpenbart gale svar («landet» 63 % verb, «ønsker» 67 % substantiv). Derfor kreves minst to helt entydige kategorier.
- *fisker* i bøker med den nye dekomponereren: *fisk* (fl) 64 / *fiske* (pres) 20 / *en fisker* 15 %. Det stemmer med `book_decomposition()`. Bare *en fisker* bruker log-regresjon; de to andre bruker reserveregler.

### Neste steg
- Adjektivandelen av «døde» (hull 5): bigrammer eller adjektivankre.
- Referanser (hull 6) og figur for paradigmegrafen.

---

## 2026-11-14 (del 21) — Oppstart av OBT-tagging: ny gren, testtekst og miljø på Linux-maskin

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Opprettet feature-branch `multitagger-oppsett` fra `main` for arbeidet med å tagge tekst med Oslo-Bergen-taggeren (OBT).
- Lagt til testtekst `tekster/test-tekst-bokselskap.txt` (åpent publisert NB-tekst om Sigrid Undset fra bokselskap.no, ca. 5 000 tegn, UTF-8). Brukes kun til å sjekke at taggeroppsettet virker.
- Lagt til `paradigmevenv/` i `.gitignore` (prosjektets Python-miljø på Linux-maskinen ligger i repo-roten).

### Tekniske observasjoner
- **OBT består av tre trinn:** (1) multitaggeren `mtag` (tokenisering + oppslag i Norsk Ordbank, gir *alle* mulige analyser), (2) Constraint Grammar-disambiguering (VISL CG-3 + regelfiler i OBT-repoet), (3) statistisk disambiguering OBT-Stat (kun bokmål). For å skille f.eks. *en fisker* / *flere fisker* / *han fisker* trengs hele kjeden, ikke bare `mtag`.
- **Kilder:** https://github.com/noklesta/The-Oslo-Bergen-Tagger (hovedrepo, kjørbare skript `tag-bm.sh`, `tag-nostat-bm.sh`), https://github.com/textlab/mtag, https://github.com/textlab/OBT-Stat. Docker-bilde `textlab/obt:1.0` anbefales i README.
- **Avhengigheter:** shell-skript, VISL CG-3, Ruby (OBT-Stat), Python (`mtag`, testet med Python ≤ 3.6; README advarer om mulige problemer med spesialtegn i ≥ 3.7). Kjøres derfor på Linux; Windows-maskinen mangler WSL/Docker/Ruby og administratorrettigheter.
- **Lisenser:** OBT/OBT-Stat: GPL v3 eller senere (modelldata kun til bruk med OBT+Stat). `mtag`: MIT; Norsk Ordbank-data: CC BY. VISL CG-3 og hunpos: ikke sjekket ennå.
- Linux-maskinen har Python 3.12.3 og Git LFS 3.7.0; repoet er klonet der og `sqlite/ordbank.db` er hentet via LFS.

### Neste steg
- Kartlegge verktøy på Linux-maskinen (Docker, Ruby, `vislcg3`, gcc/cmake) og velge Docker-bildet eller lokal installasjon av OBT.
- Lage et lite Python-skript som kjører en tekstfil gjennom OBT og leser resultatet inn i en tabell (ordform, lemma, ordklasse, morfologiske trekk), og teste det på testteksten.

---

## 2026-11-14 (del 22) — OBT installert på Linux-maskin og Python-modul `sqlite/obt_tagger.py`

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- **OBT installert uten root på Linux-maskinen** (brukeren har ikke Docker-tilgang og ikke `sudo`):
  - VISL CG-3 1.4.6 (GPLv3+) hentet som Ubuntu-pakker uten installasjon: `apt download cg3 libcg3-1` + `dpkg -x` til `~/opt/cg3/root`; `PATH` og `LD_LIBRARY_PATH` satt i `~/.bashrc`.
  - OBT klonet til `~/opt/obt` (https://github.com/noklesta/The-Oslo-Bergen-Tagger), med `mtag` (https://github.com/textlab/mtag) og `OBT-Stat` (https://github.com/textlab/OBT-Stat) klonet *inn i* OBT-mappen (skriptene finner dem via `$(dirname $0)/mtag` og `$(dirname $0)/OBT-Stat`).
  - Systemets Python 3.12, Ruby 3.2 og Perl brukes direkte av skriptene (ikke `paradigmevenv`).
  - Testet `./tag-nostat-bm.sh` (mtag + CG) og `./tag-bm.sh` (mtag + CG + OBT-Stat) på `tekster/test-tekst-bokselskap.txt` – begge virker.
- **Ny modul `sqlite/obt_tagger.py`** (kun standardbiblioteket):
  - `run_obt(fil, obt_dir, stat)` kjører OBT-skriptet (finner installasjonen via `$OBT_DIR`, ellers `~/opt/obt`).
  - `parse_obt_output(tekst)` leser OBT-formatet (`<word>…</word>`, `"<form>"`, innrykkede analyser `"lemma" pos trekk…`) til tokens med liste av analyser (lemma, ordklasse, morfologiske trekk, ekstra OBT-markører som `<*>`, `<+ledd>`, `samset-analyse`).
  - `to_rows`, `summarize`, `write_tsv` og kommandolinje: `python -m sqlite.obt_tagger FIL --out ut.tsv` (`--nostat`, `--parse-only` for å lese en eksisterende OBT-fil).
  - Parseren er testet på utdrag av OBT-utdata (med og uten OBT-Stat); hele kjøringen via `run_obt` er ennå ikke testet på Linux-maskinen.

### Tekniske observasjoner
- OBT-formatet: én blokk per token – originalordet i `<word>`, ordformen med små bokstaver i `"<…>"`, og én innrykket linje per gjenværende analyse.
- **Uten OBT-Stat** står det igjen flertydighet etter CG, f.eks. *betydning* (fem/mask – reell valgfrihet i bokmål) og *for* (konj/prep). **Med OBT-Stat** står det én analyse igjen for begge (*betydning* → fem, *for* → prep).
- `mtag` gir `SyntaxWarning: invalid escape sequence` under Python 3.12 (gamle strengliteraler). Ufarlig: strengene har samme verdi, og advarslene går til stderr.
- OBT-Stat skriver `model loaded` / `tagger compiled` til stderr.
- Ordklasse- og trekknavn følger OBT/Norsk Ordbank-notasjon (`subst appell mask be ent`, `adj ub m/f ent pos`), som ligner, men ikke er identisk med, `boy_tekst` i `ordbank.db`.

### Neste steg
- Kjøre `python -m sqlite.obt_tagger tekster/test-tekst-bokselskap.txt --out …` på Linux-maskinen for å teste hele kjeden fra Python.
- Lage en testtekst med de aktuelle flertydighetene (*fisker*, *møter*, *dør*, *hoppet/hoppa* …) og sjekke hvordan OBT skiller dem.
- Koble OBT-analysene til `lemma_id`/`boy_nummer` i `ordbank.db` (mapping fra OBT-trekk til bøyningskategorier).
- Bestemme hvor taggede filer skal ligge, og om de skal i Git.

---

## 2026-11-14 (del 23) — Hele OBT-kjeden testet fra Python; rettelse av taggsortering i `sqlite/obt_tagger.py`

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Kjørte `python -m sqlite.obt_tagger tekster/test-tekst-bokselskap.txt --out /tmp/test.tsv` på Linux-maskinen: 872 tokens, 0 flertydige etter OBT-Stat, 0 uten analyse. Hele kjeden virker fra Python.
- Rettet hvordan `parse_obt_output` sorterer taggene:
  - Ordklasse er nå første tagg som *ikke* er en markør. Tidligere ble første tagg brukt uansett, så tegnsetting fikk f.eks. `<komma>` som ordklasse.
  - Tegnsetting (OBT-lemma som starter med `$`, f.eks. `"$," <komma>`) får `pos = "tegn"`, med markøren i `ekstra`.
  - `flerord-ledd1/2/3` (flerordsuttrykk som *litteratur- og samfunnshistorie*) flyttes fra `trekk` til `ekstra`, sammen med `samset-…` og `<…>`-markører.
- Testet rettelsen mot faktiske OBT-linjer (komma, parentes, flerord, `ukjent`, egennavn).

### Tekniske observasjoner
- OBT skriver tegnsetting uten ordklasse: `"$," <komma>`, `"$(" <parentes-beg>`. Setningsgrenser står som `clb`.
- Ord som ikke finnes i Norsk Ordbank får ordklassen `ukjent`, f.eks. eldre rettskrivning *aar* (= *år*) i testteksten. Det er relevant for eldre tekster: de vil få flere `ukjent`.

### Neste steg
- Som i del 22: testtekst med de aktuelle flertydighetene, og kobling av OBT-analyser til `lemma_id`/`boy_nummer` i `ordbank.db`.

---

## 2026-11-14 (del 24) — Forslag til analysekode for OBT-tagget korpus: `sqlite/korpus_profiler.py`

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Ny modul `sqlite/korpus_profiler.py` for paradigmeanalyse av et OBT-tagget korpus (f.eks. rettighetsbelagte bøker fra samlingen). **Lagrer kun telletall, aldri tekst**, i en egen database `sqlite/korpus.db` (ignoreres av Git via `*.db`).
  1. **Telling:** `add_obt_files` (rå OBT-utdata) eller `tag_and_add` (tagger tekstfiler direkte via `obt_tagger.run_obt` uten å skrive OBT-utdata til disk). Tabell `obt_typer(doc_id, form, lemma, pos, trekk, partisipp, n)`. Tokens med flere gjenværende analyser deles likt (1/k). Tegnsetting, `clb` og `symb` telles ikke.
  2. **Kobling til Ordbanken** (`map_types`): hver analysetype kobles til `(lemma_id, boy_nummer)` ved å sammenligne OBT-trekkene med `fullformsliste.tag` for samme ordform og grunnform. `fullformsliste.tag` bruker samme notasjon som OBT (f.eks. `subst mask appell ent ub`), så trekkene sammenlignes som mengder (rekkefølge og `<…>`-markører ignoreres, unntatt `<perf-part>`/`<pres-part>`). Status: `eksakt`, `flertydig` (passer like godt på flere celler/lemmaer → vekt deles), `delvis` (beste overlapp i trekk), `ingen` (ikke i Ordbanken: egennavn, sammensetninger, ukjente ord). Tabell `type_kobling`, view `v_celle_frekvens`.
  3. **Profiler:** `paradigm_profile(grunnform=…, pos=…, per_doc=…, slots=…)` gir frekvens og andel for alle cellene i paradigmet (også de med 0), for hele korpuset eller per dokument.
  4. **Flertydige former:** `form_split(form)` gir den OBT-baserte fordelingen av en form på lemma/celle. `compare_with_decomposer(form)` kjører `decomposer.estimate_wordform_shares` på de *samme* korpustallene (en midlertidig `nb_totals`-view i en egen tilkobling skygger for Ordbankens tabell, så `decomposer.py` er uendret) og stiller estimatet ved siden av OBT-fordelingen.
  - Kommandolinje: `python -m sqlite.korpus_profiler [--db …] legg-til | tagg | koble | profil | form | sammenlign | ukoblet`.
- Testet på et lite konstruert OBT-utdrag (to «dokumenter» med *fisker* som subst. *fisker*, subst. *fisk* og verb *fiske*, *hoppet/hoppa*, *år* ent/fl, egennavn, tegnsetting). Ikke testet på ekte tagget tekst.

### Tekniske observasjoner
- OBT skiller synkretiske celler som Ordbanken ikke kan skille på form, f.eks. *år* `ent ub` vs. `fl ub` → riktige profiler for slike ord.
- Variantformer i samme celle (*hoppet/hoppa* i `pret`) slås sammen i profilen. Fordelingen mellom variantene finnes per form i `obt_typer`.
- Verbparadigmene i Ordbanken inneholder også partisipp-adjektivcellene (`boy_nummer` 6–10). Bruk `slots=` for å avgrense, f.eks. `(1, 2, 4)` for inf/pres/pret.
- Usikkert: nøyaktig OBT-notasjon for s-passiv (testdataene brukte `verb inf pass`; Ordbanken har `inf pres pass`) – ga status `delvis`, men riktig celle. Må sjekkes mot ekte OBT-utdata.
- `compare_with_decomposer` krever `numpy` (importeres av `decomposer.py`), som må installeres i `paradigmevenv` på Linux-maskinen. Resten bruker bare standardbiblioteket.
- **Rettigheter:** rå OBT-utdata inneholder hele teksten og må ikke legges i repoet. `tag_and_add` unngår å skrive dem til disk. Hvor OBT-utdata eventuelt lagres, og om noe annet enn `*.db` bør legges i `.gitignore`, er ikke avklart.

### Neste steg
- Teste på ekte OBT-utdata (testteksten og en testtekst med *fisker/møter/dør/hoppet*) og se på `ukoblet` for å forbedre koblingen.
- Avklare lagring av rettighetsbelagte tekster og OBT-utdata (utenfor repoet).
- Kontrollere OBT for hånd på et utvalg flertydige former før OBT-fordelingen brukes som fasit mot `decomposer.py`.

---

## 2026-11-14 (del 25) — `*.log` i `.gitignore` (mtag.py.log)

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- La til `*.log` i `.gitignore`.

### Tekniske observasjoner
- OBT-multitaggeren (`mtag.py`) skriver en loggfil `mtag.py.log` i *arbeidsmappen* ved hver kjøring, så den dukker opp i repo-roten når OBT kjøres derfra (f.eks. via `sqlite/obt_tagger.py`). Fila kan inneholde ord fra den taggede teksten og skal ikke deles, særlig ikke ved tagging av rettighetsbelagte bøker. Den lages på nytt ved hver kjøring og kan slettes.

### Neste steg
- Uendret fra del 24.

---

## 2026-11-17 (del 26) — `main` flettet inn i `multitagger-oppsett`; OBT-oppføringene omnummerert

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Flettet `main` (PR #4: MONS-plan, presentasjonsskjelett, forbehold om *døde*) inn i `multitagger-oppsett`. Eneste konflikt var `logg.md`, fordi begge grenene hadde lagt til oppføringer på slutten.
- **Omnummerering:** OBT-oppføringene som ble skrevet på `multitagger-oppsett` 2026-11-14 som del 13–17, heter nå **del 21–25** og står etter del 13–14 fra `main` (2026-11-17). Oppføringene fra `main` er ikke endret, siden de allerede er delt. Datoene er beholdt, så rekkefølgen i loggen er her ikke kronologisk.
- Oppdaterte henvisninger til delnumre i de omnummererte oppføringene og i `sqlite/obt_tagger.py` (docstring: «del 21–22»).
- Normaliserte linjeskift i `logg.md` til LF (slik fila er lagret i Git).

### Tekniske observasjoner
- Når flere jobber på hver sin gren, kolliderer nummereringen i `logg.md` lett. Et alternativ er å bruke dato + kort tittel som nøkkel i stedet for løpenummer, eller å avtale at nummereringen fastsettes ved fletting til `main`.

### Neste steg
- OBT-arbeidet: se del 24. Grenen kan flettes til `main` via pull request når dere har testet `korpus_profiler.py` på ekte OBT-utdata, eller tidligere hvis dere vil dele oppsettet.

---

## 2026-11-17 (del 27) — Renskrevne notater fra samarbeidsøkt

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Renskrev håndskrevne notater fra samarbeidsøkta 2026-11-17 til `notater/2026-11-17_samarbeidsokt.md` (ny mappe `notater/` for møtenotater). Merknader lagt til ved renskrivingen står i [hakeparentes].
- Lagt på `multitagger-oppsett` (ikke egen gren) for å unngå enda en kollisjon i nummereringen i `logg.md`.
- Notatet ble deretter lest over og justert av Marie (overskrift «Powerpoint», språklige rettelser, «bilder» → «foto» i *gulne*-punktet).

### Hovedpunkter fra økta
- **MONS-presentasjonen:** tydeliggjøre datakildene (Norsk Ordbank + NB n-gram), graf over *fisk* tidlig, referanse til Tromsø-miljøet (profiler i taggede korpus) og vårt bidrag om stabilitet over tid, slide med entydige verb, «substantiv velger tall før bestemthet», enkeltbok-poenget som spørsmål til publikum, fylle inn grafene.
- **Ideer som krever tagging:** forholdet mellom ordfrekvens og antall brukte former; prediksjon av flertydige former ut fra tre entydige former i paradigmet, sjekket mot tagget tekst.
- **Infinitiv + *å*/hjelpeverb:** *å gå* er langt hyppigere enn hjelpeverb + infinitiv; *kan/skal* > *vil/må* > *burde* (både *gå* og *spise*). Kan disambiguere infinitivsformer som er flertydige med andre ordklasser (*å tro* / *en tro*).
- **Enkeltord:** *gulne* (skifte fra *gulner* til *gulnet* som hyppigste form; hypotese om bilder/avispapir; konkordanser viser to bruksgrupper), *jakter* (antatt mest verb; testes med tagging).
- **Varianter:** OR-søk (*hoppet OR hoppa*) i appen; *a*-formene ser ut til å være så infrekvente i moderne bokmål at de kan ses bort fra.

### Neste steg
- Følge opp punktene i notatet og `tekst/mons_presentasjon_plan.md`.

---

## 2026-11-18 (del 28) — Korpusutvalg: balansert bokmålskorpus 1950–2026 (`sqlite/korpusutvalg.py`, `korpus/korpusoversikt.tsv`)

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Ny modul `sqlite/korpusutvalg.py` som trekker et korpus fra NBs samling med `dhlab` (Python-pakke, MIT-lisens, v2.41.0) og lagrer **kun en korpusoversikt** (metadata, URN, antall ord), ikke fulltekster. Fulltekstene hentes separat fra URN-ene og skal ikke i repoet.
- **Design (avtalt med Marie):** 3 teksttyper (skjønnlitteratur og faglitteratur fra `digibok`, aviser fra `digavis`) × 8 tiår (1950–59 … 2020–26), omtrent like mange ord i hver av de 24 cellene, ca. 10 mill. ord totalt. Oversettelser utelates.
- **Filtre:** bøker må ha `langs == "nob"` (utelater oversettelser og bøker med blandet språk) og minst 20 000 ord (utelater hefter og barnebøker). Aviser må ha minst 3 000 ord. Alle dokumenter må ha bokmålsandel ≥ 0,95, målt med markørpar (*ikke/ikkje, jeg/eg, hva/kva, hvordan/korleis, noen/nokon, mye/mykje, hvem/kven*). Maks én bok per forfatter og maks tre numre per avistittel per celle. Ingen dokumenter større enn 35 % av cellemålet.
- Antall ord per dokument regnes ut fra dhlab-frekvens-API-et: frekvens / relativ frekvens for et vanlig ord.
- **Resultat:** `korpus/korpusoversikt.tsv` med 224 dokumenter og 10 724 916 ord: 58 skjønnlitterære bøker (3,6 M), 64 fagbøker (3,7 M) og 102 avisnumre fra 80 titler (3,5 M). Alle celler har 418 000–547 000 ord. Trukket 2026-11-18.

### Tekniske observasjoner
- `Corpus(lang="nob")` filtrerer ikke strengt: første trekning hadde 10 bøker med `langs == "nob"` som var nynorsk eller dialekt (bokmålsandel 0,00–0,93, f.eks. *Om distrikts- og regionalpolitikken*, *Breheimen til framtida*, *Jærsk humor*). Språksjekken gjelder derfor nå også bøker, og korpuset ble trukket på nytt.
- Aviser har ikke språk i metadata (`lang="nob"` gir 0 treff), så språksjekken er eneste filter for dem.
- **Svakheter i metadataene som ikke fanges automatisk** (sett i første trekning): feil `literaryform` (f.eks. *Nye forstads- og tunnelbaner i Oslo* og *Etnopolitikk som skolepolitikk* merket som skjønnlitteratur), oversettelser uten originalspråk i metadata (*Ponson du Terrail*, trolig også flere westernhefter fra 1950–80-tallet) og nyutgivelser av eldre verk som havner i feil tiår (*Amalie Skram*, utgave 1993).
- Utvalget trekkes tilfeldig av dhlab-API-et og kan ikke gjenskapes ved ny kjøring. Den lagrede oversikten er den reproduserbare definisjonen av korpuset.

### Neste steg
- Gå gjennom `korpus/korpusoversikt.tsv` for hånd og merke dokumenter som bør ut (feil sjanger, oversettelser, nyutgivelser). Eventuelt legge inn en ekskluderingsliste som skriptet bruker til å fylle cellene opp igjen.
- Hente fulltekstene fra URN-ene til Linux-maskinen (utenfor repoet), og starte med en pilot på ca. 10 bøker for å måle hvor lang tid OBT bruker.

---

## 2026-11-18 (del 29) — Fulltekster hentet for korpusoversikten (utenfor repoet)

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Hentet fulltekstene for alle 224 dokumentene i `korpus/korpusoversikt.tsv` fra Språkbankens interne teksttjeneste (kun tilgjengelig på NBs nettverk) med et lite skript som ligger **utenfor repoet**. Tekstene er lagret lokalt utenfor repoet og OneDrive, én fil per dokument med navn `<dhlabid>.txt`. De skal overføres til Linux-maskinen for tagging og slettes lokalt etterpå.
- Tekstene er rettighetsbelagte og skal ikke inn i repoet. Adressen til tjenesten står heller ikke i repoet.

### Tekniske observasjoner
- 224/224 hentet uten feil, til sammen ca. 55 MB (UTF-8 ren tekst).
- Antall ord i tekstene (mellomromsdelt) er **identisk** med `n_ord` i korpusoversikten for alle dokumenter (10 724 916 ord). Tjenesten leverer altså samme tekst som dhlab teller på.
- Tekstene er allerede tokenisert (tegnsetting er skilt fra ord med mellomrom, f.eks. `Co . Pty . Ltd .`), og linjeskift følger OCR-linjene. OBT tokeniserer selv. Forkortelser og orddeling ved linjeskift kan gi noen ekstra feil eller `ukjent`; sjekkes i piloten.
- Filnavnet (`dhlabid`) blir `doc_id` i `sqlite/korpus_profiler.py`, så telletallene kan kobles direkte til korpusoversikten.

### Neste steg
- Overføre tekstene til Linux-maskinen (utenfor repoet).
- Pilot: tagge ca. 10 dokumenter (blandet teksttype og tiår), måle tidsbruk, og sjekke `koble` / `ukoblet` i `korpus_profiler.py`.

---

## 2026-11-18 (del 30) — Pilot: 10 korpusdokumenter tagget med OBT; rettelser i koblingen

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Valgte 10 pilotdokumenter fra `korpus/korpusoversikt.tsv` (dokumentet nærmest medianlengden i hver celle): skjønnlitteratur og faglitteratur fra 1950-, 1980- og 2010-tallet, aviser fra 1950-, 1980-, 2010- og 2020-tallet. Til sammen 432 414 ord. dhlabid: 100529224 100354617 100212799 100554427 100113405 100410017 202147427 204377691 201547312 204608626.
- Marie tagget dem på Linux-maskinen med `python -m sqlite.korpus_profiler --db /tmp/pilot.db tagg …` og kjørte `koble` og `ukoblet`.
- Rettelser etter piloten:
  - `clb` (OBTs setningsgrensemarkør) behandles som markør, ikke som trekk: i `obt_tagger._is_marker` og i `korpus_profiler._core_tags`. OBT setter `clb` både på setningsavsluttende tegn (`"$." clb <punkt>` → nå `pos = "tegn"`) og på konjunksjoner (*og*, *men*, *for*), som derfor bare ble `delvis` koblet.
  - `koble --på-nytt` kobler alt på nytt (trengs etter endringer i koblingsreglene, uten å tagge på nytt).
  - `koble` viser i tillegg koblingen per ordklasse for `subst` (uten egennavn), `verb` og `adj` (`mapping_report_by_pos`).

### Viktige funn
- **Tid:** ca. 4 minutter for 432 000 ord (ca. 1 800 ord/s). Hele korpuset (10,7 M ord) anslås til 1½–2 timer.
- **Kobling (før rettelsen, alle ordklasser):** eksakt 75,8 %, `ingen` 18,5 %, delvis 2,9 %, flertydig 2,8 %. Nesten alt i `ingen` er ord uten paradigme: ubøyelige ord der OBT og Ordbanken bruker ulik ordklasse (*ut, opp, inn, ned, her, der, hjem, tilbake, frem* er `prep` hos OBT, adverb i Ordbanken; *å* er `inf-merke`), tall, egennavn (*Truls, Aagot, Gud, Norge*) og høflighets-*De*. Det påvirker ikke paradigmeprofilene.
- **OCR-feil gir falske bøyningsformer:** *seiv* er tagget 524 ganger som preteritum av *sive*. Det er nesten sikkert OCR-feil for *selv* (*l* lest som *i*). Slike feil kan blåse opp enkeltceller i paradigmer (jf. *katt/hatt* i del 7) og må holdes øye med i profilene.

### Neste steg
- Marie: `git pull`, kjøre `koble --på-nytt` på pilotdatabasen og se på koblingen for subst/verb/adj, og kjøre linjeskifttesten (sammenligning av tagging med og uten linjeskift).
- Deretter tagge hele korpuset (i bakgrunnen, f.eks. med `nohup`).

---

## 2026-11-18 (del 31) — Pilotresultater etter rettelsen; klargjøring for tagging av hele korpuset

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Marie kjørte `koble --på-nytt` på pilotdatabasen (10 dokumenter) og linjeskifttesten.
- `korpus_profiler.tag_and_add` / `tagg` hopper nå over dokumenter som allerede finnes i databasen, så en avbrutt kjøring kan startes på nytt med samme kommando. Skriver framdrift med tid per dokument.
- `ukoblet` har fått valgene `--status` (f.eks. `flertydig`), `--pos` og `--antall`, og viser hvilke celler (`lemma_id:boy_nummer`) en analysetype er koblet til. Antall regnes nå med vekt, så flertydige typer ikke telles dobbelt.

### Viktige funn
- **Kobling per ordklasse etter rettelsen** (pilot, 432 000 ord):

  | Ordklasse | eksakt | flertydig | delvis | ingen | tokens |
  |---|---:|---:|---:|---:|---:|
  | verb | 92,5 % | 5,0 % | 1,1 % | 1,4 % | 66 191 |
  | adj | 92,7 % | 0,4 % | 0,3 % | 6,6 % | 30 517 |
  | subst (uten egennavn) | 84,2 % | 1,8 % | 1,6 % | 12,4 % | 65 794 |

  Alle ordklasser samlet: eksakt 78,0 %, `ingen` 18,5 % (tall, egennavn, ubøyelige ord med ulik ordklasse hos OBT og Ordbanken). `ingen` for substantiv er trolig mest sammensetninger som ikke er egne oppslag i Ordbanken, pluss OCR-feil.
- **5 % `flertydig` for verb** må undersøkes (`ukoblet --status flertydig --pos verb`). Det betyr at analysen passer like godt på flere lemmaer med samme grunnform, og vekten deles likt mellom dem, noe som kan svekke profilen til vanlige verb.
- **Linjeskifttest** (Smaalenenes Avis 2012, ca. 30 000 tokens): bare 38 av 29 964 tokens (0,13 %) får ulik analyse når linjene slås sammen. Forskjellene er nesten alle ord i starten av en linje (typisk overskrifter: *Undervisning*, *Fjerner*, *Planlegger*), som blir feiltagget som egennavn når linjene slås sammen. **Linjeskiftene hjelper altså, og tekstene tagges som de er.**

### Neste steg
- Tagge hele korpuset (224 dokumenter, ca. 1½–2 timer) i bakgrunnen til `sqlite/korpus.db`.
- Undersøke de flertydige verbkoblingene.

---

## 2026-11-18 (del 32) — Tagging av hele korpuset startet

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Marie startet taggingen av alle 224 korpusdokumentene på Linux-maskinen i bakgrunnen: `nohup python -m sqlite.korpus_profiler tagg /home/rosok/dhlab_fulltekster/*.txt > ~/tagging.log 2>&1 &`. Telletallene skrives til `sqlite/korpus.db` (ignoreres av Git).

### Tekniske observasjoner
- Tempo for de første dokumentene: ca. 1 000 tokens/s (tregere enn anslaget fra piloten). Hele korpuset anslås til ca. 3 timer.
- Taggingen bruker omtrent 1–2 prosessorkjerner og fortsetter selv om SSH-forbindelsen brytes (`nohup`). Stopper den, kan samme kommando kjøres på nytt, og ferdige dokumenter hoppes over.

### Neste steg
- Når taggingen er ferdig: `koble`, `ukoblet --status flertydig --pos verb`, og deretter de første paradigmeprofilene og sammenligningen med `decomposer.py`.

---

## 2026-11-19 (del 33) — Taggingen hang på dokument 5; tidsgrense per dokument i OBT-kjøringen

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Sjekket den nattlige taggingen: bare 4 av 224 dokumenter var tagget. Prosessen sto fast på dokument 5 (`100029013`) i nesten 14 timer: `mtag.py` brukte 99,9 % CPU, mens `vislcg3`, OBT-Stat (Ruby) og `perl` sto på 0 % og ventet. Multitaggeren gikk altså i evig løkke på noe i denne teksten.
- `sqlite/obt_tagger.run_obt` har fått `timeout`. OBT-kjeden kjøres i egen prosessgruppe (`start_new_session=True`), og ved tidsavbrudd stoppes hele gruppa (`os.killpg`) og `ObtTimeout` kastes. `subprocess.run(timeout=…)` ville bare stoppet skallskriptet og latt `mtag.py` fortsette.
- `sqlite/korpus_profiler.tag_and_add` / `tagg`: dokumenter som feiler eller får tidsavbrudd, noteres i ny tabell `tagging_feil` og hoppes over, så resten av korpuset blir tagget. Nye valg: `--tidsgrense` (standard 900 s) og `--prøv-feilede`. Ny kommando `feilet` lister feilede dokumenter.
- Logikken (notere, hoppe over, prøve igjen) er testet med simulert tidsavbrudd på Windows. Selve avbruddet av prosessgruppa bruker Linux-funksjoner og må testes på Linux-maskinen.

### Tekniske observasjoner
- Tempo før stoppen: ca. 1 000 tokens/s. Det største dokumentet (ca. 143 000 ord) bør da ta 2–3 minutter, så 900 s er god margin.
- Mulig årsak: `mtag`-dokumentasjonen advarer om problemer med ordformer som inneholder spesialtegn for regulære uttrykk under Python ≥ 3.7 (maskinen har 3.12). Ikke bekreftet; `100029013` bør undersøkes for å finne hva som utløser løkka.

### Neste steg
- Stoppe den hengende prosessen (`kill -- -<PID>`), hente rettelsen, teste tidsgrensen på `100029013` og starte taggingen på nytt.
- Finne hva i `100029013` som får `mtag.py` til å henge, og om det kan rettes (f.eks. ved å fjerne eller erstatte tegn før tagging).

---

## 2026-11-19 (del 34) — Hele korpuset tagget; kobling mot Ordbanken

**Dato/agent:** 2026-11-19, Claude (Opus 5.5) sammen med Marie

**Hva ble gjort**
- Taggingen av hele korpuset ble fullført på Linux-maskinen (220 dokumenter i denne kjøringen, 149 min; 4 var tagget fra før). 222 av 224 dokumenter er tagget.
- Kjørte `feilet`, `koble` og `ukoblet --status flertydig --pos verb`.

**Funn**
- To dokumenter feilet med tidsavbrudd (900 s), begge faglitteratur 1950–1959:
  `100029013` (*Menn med øreringer i Norge*, 1957, 37 147 ord) og `100496944` (kommunal inndeling i Sør-Trøndelag, 1958, 46 496 ord). Cellen faglitteratur 1950-tallet mister dermed ca. 84 000 av 447 000 ord (ca. 19 %). Godtas foreløpig.
- Kobling mot `fullformsliste`, vektede tokens:

  | | eksakt | flertydig | delvis | ingen | tokens |
  |---|---|---|---|---|---|
  | alle ordklasser | 72,2 % | 2,3 % | 1,0 % | 24,5 % | |
  | subst (uten prop) | 80,7 % | 1,5 % | 1,4 % | 16,4 % | 1 749 197 |
  | verb | 91,1 % | 5,2 % | 1,9 % | 1,8 % | 1 418 488 |
  | adj | 90,2 % | 0,4 % | 0,3 % | 9,1 % | 701 441 |

  Tallene ligger nær piloten. `ingen` for alle ordklasser skyldes særlig egennavn, tall og ubøyelige ord.
- Verb med status `flertydig` er homografe lemmaer i Ordbanken med samme grunnform og samme celle (f.eks. *være* 80033/80034, *bli* 7528/7530, *la* 81665/82098, *rekke* med tre lemma_id). Formen er ikke flertydig i teksten; vekten deles likt mellom lemma_id-ene.
  - Konsekvens: `paradigm_profile` med `grunnform` velger ett lemma_id. Når homografene har like paradigmer, blir andelene riktige, men tallene halvert. Når paradigmene er ulike (f.eks. svak/sterk bøyning, *henge*), får celler som bare finnes i det ene paradigmet full vekt, mens delte celler får halv vekt, og profilen blir skjev.

**Neste steg**
- Slå sammen homografe lemma_id (samme grunnform og pos) i profilene, f.eks. ved å summere per `boy_nummer` over alle kandidatene.
- Se på `ingen` for substantiv (16 %): sammensetninger, OCR-feil, eldre rettskrivning.
- Undersøke tidsavbruddene i `mtag.py` bare hvis det blir nødvendig.

---

## 2026-11-19 (del 35) — Homografe lemmaer slås sammen i paradigmeprofilene

**Dato/agent:** 2026-11-19, Claude (Opus 5.5) sammen med Marie

**Hva ble gjort**
- `paradigm_profile` i `sqlite/korpus_profiler.py` slår nå sammen alle lemma_id med samme grunnform og ordklasse når profilen hentes med `grunnform` (ny parameter `merge_homographs=True`). Frekvensene summeres per `boy_nummer`, og cellene er unionen av paradigmene.
  - Uten `pos`, og med kandidater i flere ordklasser, velges ordklassen med flest forekomster, fordi `boy_nummer` betyr ulike ting i ulike ordklasser.
  - `--lemma-id` gir fortsatt ett enkelt lemma_id. `--ikke-slå-sammen` (eller `merge_homographs=False`) gir den gamle oppførselen.
  - Utdatafeltet `lemma_id` heter nå `lemma_ids`, f.eks. `7528,7530`.
- Testet på en liten database med konstruerte telletall mot Ordbanken. Ingen andre moduler bruker funksjonen.

**Funn**
- Med konstruerte tall (blir 100, ble 60, blitt 40) ga den gamle profilen for *bli* (lemma_id 7528) presens 38 %, preteritum 46 % og perfektum partisipp 15 %. Riktig fordeling er 50/30/20 %. *ble* finnes bare i 7528-paradigmet og fikk full vekt, mens *blir* og *blitt* ble delt på to lemma_id. Profilene for homografe verb var altså skjeve før rettelsen, ikke bare halverte.

**Hva sammenslåingen IKKE endrer: ingen data går tapt**
- Sammenslåingen skjer bare når profilen regnes ut (i `paradigm_profile`). Ingenting i databasen er endret eller slettet.
- `korpus.db` lagrer fortsatt:
  - `obt_typer`: hver ordform med lemma, ordklasse og trekk fra OBT, og antall per dokument;
  - `type_kobling`: én rad per Ordbank-oppføring (lemma_id) som formen kan høre til, med status `flertydig` og vekten den fikk (f.eks. 0,5 + 0,5).
- Informasjonen om at en form kan høre til flere oppføringer kan derfor alltid hentes ut igjen:
  - `ukoblet --status flertydig [--pos verb]`: alle former som kan høre til flere oppføringer, med lemma_id og celle (kolonnen `celler`);
  - `form <ordform>`: fordelingen av én ordform på lemma_id og celle;
  - `profil <grunnform> --lemma-id N`: profilen for én bestemt oppføring;
  - `profil <grunnform> --ikke-slå-sammen`: den gamle beregningen;
  - `lemma_ids` i profilen viser hvilke oppføringer som er slått sammen.
- Merk: OBT selv skiller ikke mellom homografe oppføringer i Ordbanken. Korpuset har derfor aldri hatt informasjon om *hvilken* oppføring et ord i teksten tilhører, bare om at formen passer med flere. Den likedelte vekten (0,5/0,5) er en teknisk fordeling, ikke en observasjon. Skal homografene skilles (f.eks. *la* «la være» vs. *la* «lade»), trengs betydningsanalyse eller manuell gjennomgang. Da er `type_kobling` utgangspunktet.

**Neste steg**
- Kjøre profiler på det ekte korpuset, f.eks. `python -m sqlite.korpus_profiler profil bli --pos verb`, og sammenligne med n-gram-profilene.

---

## 2026-11-19 (del 36) — Første korpusprofil (*bli*) og profiler per tiår/teksttype

**Dato/agent:** 2026-11-19, Claude (Opus 5.5) sammen med Marie

**Hva ble gjort**
- Marie kjørte `profil bli --pos verb` på det taggede korpuset (lemma_id 7528 og 7530 slått sammen).
- Nye funksjoner i `sqlite/korpus_profiler.py`:
  - `load_metadata`: leser `korpus/korpusoversikt.tsv`; doc_id i `korpus.db` er dhlabid.
  - `profile_by_group(conn, grunnform, pos, by=("tiaar",) …)`: paradigmeprofil per gruppe av dokumenter (kolonner i korpusoversikten, f.eks. `tiaar`, `teksttype`). Bygger på `paradigm_profile(per_doc=True)` og summerer per gruppe.
  - Felter per gruppe og celle: `n`, `andel`, `n_lemma`, `per_mill` (lemmaets forekomster per million tokens) og `n_dok`.
- Kommandolinje:
  - `profil bli --pos verb --etter tiaar [teksttype]` gir en tabell med én linje per gruppe og andel per celle (celler som er tomme overalt, utelates).
  - `--celler 1 2 4 5` begrenser til bestemte bøyningsnumre; andelene regnes da innenfor dem. `--celler` virker også uten `--etter`.
- Testet med konstruerte telletall på ekte dhlabid-er fra oversikten. Dokumenter som mangler i oversikten havner i gruppen `ukjent`.

**Funn**
- *bli* i hele korpuset: 55 282 forekomster.

  | celle | andel |
  |---|---|
  | pret (ble/blei/bleiv/blev) | 48,6 % |
  | pres | 24,2 % |
  | inf | 17,3 % |
  | perf-part | 9,7 % |
  | imp | 0,2 % (128) |

  - S-passiv og partisippformene brukt som adjektiv er tomme.
  - Imperativ kommer trolig fra kontekstdisambigueringen («Bli her!»).

**Neste steg**
- Kjøre `profil bli --pos verb --etter tiaar teksttype` på korpuset og vurdere stabiliteten over tid.
- Sammenligne med n-gram-profilen (`compute_paradigm_profile`) for samme periode.

---

## 2026-11-19 (del 37) — Profilen for *bli* per tiår og teksttype

**Dato/agent:** 2026-11-19, Claude (Opus 5.5) sammen med Marie

**Hva ble gjort**
- Marie kjørte `profil bli --pos verb --etter tiaar`, `--etter teksttype` og `--etter tiaar teksttype --celler 1 2 4 5` på det taggede korpuset (222 dokumenter).

**Funn** (andeler av inf/pres/pret/perf-part)
- **Per tiår er profilen ganske stabil.** inf 0,14–0,19, pret 0,44–0,59, perf-part 0,08–0,12. Presens varierer mest (0,18–0,30). Det er ingen tydelig trend over tid på tvers av teksttypene.
- **Teksttype betyr mer enn tiår:**
  - faglitteratur har mest preteritum (0,56) og minst infinitiv (0,13), trolig *ble*-passiv;
  - skjønnlitteratur har mest infinitiv (0,22) og perf-part (0,13);
  - aviser har mest presens (0,29).
- **Celler med få dokumenter styres av enkeltdokumenter.** Eksempler:
  - faglitteratur 1980-tallet: pret 0,71 og 11 149 forekomster per million, nesten dobbelt så høyt som ellers, trolig én eller to bøker med mye passiv;
  - skjønnlitteratur 2020-tallet: pres 0,32 og pret 0,30, trolig romaner skrevet i presens.
  - I skjønnlitteratur avhenger pres/pret mye av hvilken tid fortellingen står i.
- **Aviser (10–20 dokumenter per tiår) er jevnest og viser en mulig trend:**
  - presens øker fra 0,23 (1950-tallet) til 0,33–0,34 (1980-tallet og senere), og preteritum går ned fra 0,53 til ca. 0,40;
  - samtidig synker forekomster per million fra 8 131 til 4 745.
  - Det kan tyde på mer presens i nyhetsspråket og/eller mindre *bli*-passiv, men er foreløpig ikke testet mot variasjonen mellom dokumenter.

**Neste steg**
- Måle variasjonen mellom dokumenter (dokumentet er utvalgsenheten): spredning per celle, f.eks. bootstrap over dokumenter, så vi ser hvilke forskjeller mellom tiår og teksttyper som er større enn støyen.
- Finne dokumentene som driver avvikene (faglitteratur 1980-tallet, skjønnlitteratur 2020-tallet) med `profil … --per-dok`.
- Sammenligne med n-gram-profilen for *bli*.

---

## 2026-11-19 (del 38) — Telletallene fra OBT-taggingen deles i repoet (Git LFS)

**Dato/agent:** 2026-11-19, Claude (Opus 5.5) sammen med Marie

**Hva ble gjort**
- Marie ønsker at kollegaen skal kunne analysere resultatet av taggingen. Fulltekstene deles ikke. Det som deles, er en kopi av korpusdatabasen med bare telletall (ca. 300 MB): `korpus/obt_frekvenser.db`.
- `.gitattributes`: `korpus/obt_frekvenser.db` spores med Git LFS (som `sqlite/ordbank.db`).
- `.gitignore`: unntak `!korpus/obt_frekvenser.db` fra regelen `*.db`. `sqlite/korpus.db` (den lokale arbeidsdatabasen) er fortsatt ignorert, så lokale databaser ikke kolliderer ved `git pull`.
- Ny kommando `eksporter` (`export_shared`) i `sqlite/korpus_profiler.py`: kopierer databasen, erstatter `kilde` (lokal filsti til fulltekstene) med filnavnet og kjører VACUUM.

**Innholdet i `korpus/obt_frekvenser.db`** (ingen tekst; teksten kan ikke gjenskapes)
- `obt_typer`: (doc_id, form, lemma, pos, trekk, partisipp, n) per dokument, der n er vektet antall.
- `type_kobling`: koblingen av hver analysetype til Ordbank-celler (lemma_id, boy_nummer, vekt, status). Homografe lemmaer ligger som egne rader med status `flertydig` (se del 35).
- `dokumenter`: doc_id (= dhlabid i `korpus/korpusoversikt.tsv`), filnavn og antall tokens.
- `tagging_feil`: de to dokumentene som fikk tidsavbrudd (del 34).

**Bruk**
- Alle kommandoene tar `--db korpus/obt_frekvenser.db`, f.eks.:
  `python -m sqlite.korpus_profiler --db korpus/obt_frekvenser.db profil bli --pos verb --etter tiaar`
- Ordbanken (`sqlite/ordbank.db`) må også være hentet med Git LFS.
- Oppdatering etter ny tagging eller ny kobling: kjør `eksporter` på nytt, og commit og push.

**Funn / merknader**
- Hver ny versjon av fila legges til i LFS-lagringen på GitHub og teller på kvoten til eieren av repoet.

**Neste steg**
- Marie lager fila på Linux-maskinen (`git pull`, `eksporter`, `git add`, commit, push).

---

## 2026-11-19 (del 39) — Ordformer vs. lemmaer: morfologisk variasjon i korpuset

**Dato/agent:** 2026-11-19, Claude (Opus 5.5) sammen med Marie

**Hva ble gjort**
- Marie lastet opp `korpus/obt_frekvenser.db` (LFS, se del 38). Den er hentet lokalt på Windows-maskinen.
- Overordnede oppgaver avklart med Marie:
  1. validere decomposer mot den taggede fordelingen;
  2. undersøke om bøyningsprofilene er stabile over tid, for utvalgte eksempelparadigmer.
- Først besvares et spørsmål fra kollegaen: hvor mye endrer antallet seg når bøyningsformene slås sammen til lemma?
- Ny modul `sqlite/morfologisk_variasjon.py`:
  - tokens, formtyper, lemmatyper (OBT-lemma + ordklasse), former per lemma og andel bøyde tokens (form ≠ lemma);
  - tallene gis per ordklasse, per lemmafrekvens og per tiår og teksttype;
  - typer sammenlignes ved likt antall tokens (eksakt rarefaction).
  - Kjøres med `python -m sqlite.morfologisk_variasjon [--db …] [--utvalg 200000]`.
- Rapport: `rapport_morfologisk_variasjon.md`.

**Funn**
- Ca. 2 % av tokens (9 % av formtypene) har tegn i starten eller slutten fra tokenisering eller OCR, f.eks. «er.», «er|», «_vært», «kl.». Disse renses (`clean_form`) før telling. Uten rensingen blir forholdet former/lemma for høyt.
- Alle ord: 410 711 formtyper og 363 042 lemmaer, altså 1,13 former per lemma. Men 30 % av tokens står i en annen form enn lemmaet (58 % for substantiv, verb og adjektiv; 79 % for verb).
- Det lave forholdet former/lemma skyldes sjeldne lemmaer, egennavn og ukjente ord. Egennavn og ukjente ord er 13 % av tokens, men 49 % av formtypene. Lemmaer med over 1 000 forekomster har over 6 former (substantiv, verb) og 5,2 former (adjektiv).
- Etter teksttype: skjønnlitteratur har mest bøyning (andel bøyd 0,32; subst/verb/adj 0,64) og aviser minst (0,26 / 0,52). Over tid er tallene stabile samlet sett.
- Aviser: andelen bøyde ord faller fra 0,28 til 0,23 fra 1950-tallet til 2020-tallet. Det skyldes dels flere egennavn (14 % → 21 %) og færre verb, men andelen faller også innenfor subst/verb/adj (0,55 → 0,49).

**Neste steg**
- Validere decomposer (oppgave 1) og velge eksempelparadigmer for stabilitetsanalysen (oppgave 2).

---

## 2026-11-19 (del 40) — Første sammenligning av decomposer med OBT-fordelingen

**Dato/agent:** 2026-11-19, Claude (Opus 5.5) sammen med Marie

**Hva ble gjort**
- Marie ønsker å validere decomposer på et utvalg flertydige former med paradigmer som er brukt i repoet, ikke på alle lemmaer.
- Kjørte `compare_with_decomposer` (uendret, korpustallene fra `korpus/obt_frekvenser.db` brukes som `nb_totals`) på 12 former: fisker, dør, døde, går, hatt, kroner, dager, ønsker, møter, viser, landet, tro. Ingen kode er endret.

**Funn** (andel per kandidat i prosent, decomposer / OBT; antall forekomster i korpuset i parentes)
- God overensstemmelse (1–4 prosentpoeng):
  - *hatt* (2 843): ha 95/95, hatt 5/5;
  - *ønsker* (2 044): verb 94/92;
  - *møter* (978): verb 68/72;
  - *landet* (2 099): land 85/83;
  - *dager* (2 570): dag 98/100.
- Middels:
  - *viser* (2 649): vise verb 99/93, subst *vise* 0/6;
  - *fisker* (367): fiske verb 58/68, fisker 20/17, fisk 21/7.
- Dårlig:
  - *dør* (628): subst 67/48, verb 33/51;
  - *kroner* (2 943): verb *krone* 26/1, fordi verbets egne former (inf *krone*) også er flertydige;
  - *døde* (1 580): adj *død* 0/28, den kjente adjektivmangelen (rapport_verbtyper §7.2);
  - *går* (8 486): subst *går* («i går») 0/15;
  - *tro* (1 932): verb 96/59, subst 0/14, adj 0/4.
- Mønster: decomposer svikter når en kandidat mangler regler eller andre former å regne ut fra (adjektiv, *går*, *tro*), og når ankerformene selv er flertydige (*krone*).
- Forbehold:
  - noen former er sjeldne i korpuset;
  - OBT er ikke fasit (*tro* som pret av *trå* 160 ganger virker mistenkelig);
  - 0–7 % av forekomstene er ukoblet;
  - homografe oppføringer (f.eks. subst *tro* 71278/71279) er ikke slått sammen i `compare_with_decomposer`.

**Neste steg** (foreslått, venter på Maries svar)
- Fast ordliste på ca. 20 former: de 12 over pluss «støykandidatene» fra rapport_verbtyper (stille, fiske, svare, selge, leve, vinne, legge, bygge, sette, tape).
- Liten modul som slår sammen homografer på begge sider og gir et avviksmål per form.
- Stikkprøver av OBT-analyser for mistenkelige tilfeller.
- Rapport `rapport_decomposer_validering.md`.

---

## 2026-11-20 (del 41) — `figurer-deck` flettet inn i `multitagger-oppsett`; lognumre ordnet; sammenligningen tilpasset ny decomposer

**Dato/agent:** 2026-11-20, Claude (Opus 5.5) sammen med Marie

**Hva ble gjort**
- Flettet `origin/figurer-deck` (som inneholder `rapport-verbtyper`) inn i `multitagger-oppsett`, fordi kollegaens arbeid med decomposer hører sammen med valideringen mot OBT. Med i flettingen:
  - substantivprofiler, `sqlite/verbtyper.py` og figurer til decket;
  - `sqlite/valider_dekomponering.py` og `rapport_dekomponering_validering.md`;
  - log-regresjon som standard i `sqlite/decomposer.py`.
- **Omnummerering av loggen:** Kollegaens oppføringer (del 15–20, 2026-11-17–20) er ikke endret og står etter del 14. Oppføringene fra `multitagger-oppsett` (tidligere del 15–34) heter nå **del 21–40**. Henvisninger til lognumre i `.gitignore`, `rapport_morfologisk_variasjon.md`, `sqlite/korpus_profiler.py`, `sqlite/morfologisk_variasjon.py` og `sqlite/obt_tagger.py` er oppdatert tilsvarende. Datoene er beholdt, så rekkefølgen er ikke helt kronologisk.
- **`compare_with_decomposer`** i `sqlite/korpus_profiler.py` er tilpasset den nye decomposer:
  - Ny parameter `method` med `logreg` (standard) eller `regler`.
  - Problemet: Log-regresjonen lærer på gullstandarden, som velges med terskelen 100 000 i `nb_totals`. Med korpustallene (8,4 mill. ord) ble gullstandarden tom, og `numpy.linalg.lstsq` feilet.
  - Løsningen: Gullstandardlemmaene velges med Ordbankens ekte `nb_totals`, mens kategorifrekvensene hentes fra korpuset (`_corpus_gold_profiles`). Det gir 1 916 substantiv og 459 verb med alle fire kategorier > 0.
  - Decomposerens modellbuffere byttes ut midlertidig og settes tilbake etterpå. `decomposer.py` er ikke endret.

**Funn**
- Med `method="regler"` blir resultatene identiske med del 40. Med `logreg` endres lite for formene som er testet så langt:
  - *hatt*: ha 92 % (regler 95 %, OBT 95 %);
  - *dør*: subst 71 % (regler 67 %, OBT 47 %);
  - *fisker* og *kroner*: praktisk talt uendret.

**Neste steg**
- Fast ordliste og valideringsmodul (del 40, neste steg), og kjøre begge metodene.

---

## 2026-11-20 (del 42) — Validering av decomposer mot det OBT-taggede korpuset

**Dato/agent:** 2026-11-20, Claude (Opus 5.5) sammen med Marie

**Hva ble gjort**
- Avklart med Marie: validering i to deler.
  1. Bred og automatisk: alle aktuelle flertydige former.
  2. Dyp: utvalgte former og profiler.
- `sqlite/korpus_profiler.py`: ny klasse `DecomposerSession`. Den gjenbruker én tilkobling med en indeksert temp-tabell `nb_totals` (korpusets formtall) og gullstandarden for log-regresjonen, så mange former kan kjøres raskt (under 1 ms per form etter ca. 20 s oppstart). `compare_with_decomposer` bruker den.
- Ny modul `sqlite/valider_dekomponering_obt.py` (`python -m sqlite.valider_dekomponering_obt`, ca. 1,5 min):
  - sammenligner per leksem (grunnform + ordklasse; homografer slått sammen);
  - mål: avvik i pp (total variasjonsavstand), riktig flest, umodellert andel og grunnlag (sum anslag / observert);
  - varianter: `regler`, `logreg` og `logreg_hom` (homografe lemma_id telles én gang);
  - profiler i tre varianter: OBT, decomposer (formfrekvens × andel) og naiv (rå formfrekvens);
  - skriver `resultater/dekomponering_obt_former.tsv` og `resultater/dekomponering_obt_profiler.tsv`.
- Rapport: `rapport_dekomponering_obt.md`.

**Funn**
- Utvalg: 1 775 former med ≥ 100 forekomster og ≥ 2 leksemer blant subst/verb/adj. Av dem gir OBT ≥ 90 % subst/verb/adj for 1 721.
- Når alle kandidatene er modellert (1 206 former), gir decomposer riktig leksem størst andel i 80 % av formene, med medianavvik 7,9 pp (logreg) / 7,8 pp (regler). Med grunnlag ≥ 0,5: 84 % og 5,7 pp. Det stemmer med kollegaens syntetiske test (ca. 80 %, 10–15 pp).
- Største feilkilde er umodellerte kandidater: 515 former (31 % av forekomstene) har ≥ 5 % på et leksem decomposer gir 0 %. Medianavviket er 50 pp, og riktig leksem får størst andel i 44 %. To tredjedeler av forekomstene er adjektiver (*hele*, *nye*, *godt*, *litt*, *døde*, *få*).
- Regler og logreg gir nesten samme resultat, fordi logreg krever to entydige ankerkategorier og bare brukes i 566 av 2 962 kandidatanslag (19 %).
- Homografe lemma_id telles dobbelt i decomposer (*la*, *rekke*), men å telle dem én gang endrer medianavviket bare fra 7,9 til 8,1 pp.
- Andre feiltyper:
  - lite grunnlag (*fall*: sum anslag 17 mot 1 738 observert);
  - delte ankre behandles ulikt for verb og substantiv (*arbeid*, *livet* dras mot verbet);
  - idiosynkratiske profiler (*la*/*legge*).
- Profiler:
  - substantiv blir klart bedre med decomposer: *fisker* 1,4 pp mot naiv 37,6; *fisk* 4,5 mot 23,2;
  - verb blir blandet: bedre for *sette*, *svare*, *bygge*; verre enn naiv for *dø* (11,7 mot 8,1) og *legge* (23,9 mot 11,0); dårlig begge veier for *stille* og *tape*.
  - *dø*: rekkefølgen pret > inf > pres holder, men decomposer undervurderer presens (8 mot 15 %) og overvurderer preteritum (66 mot 54 %).

**Neste steg**
- Dele rapporten med kollegaen.
- Anbefalingene til decomposer (adjektivkandidater, vise grunnlaget, delte ankre) er hans modul, så de må avtales med ham.
- Eventuelt stikkprøver av OBT (*tro*/*trå*, *å*).

---

## 2026-11-20 (del 43) — Testteksten for OBT fjernet

**Dato/agent:** 2026-11-20, Claude (Opus 5.5) sammen med Marie

**Hva ble gjort**
- Slettet mappen `tekster/` med `test-tekst-bokselskap.txt` (del 21). Teksten ble bare brukt til å teste OBT-oppsettet før de ekte fulltekstene var på plass, og mappenavnet var lett å forveksle med `tekst/`.
- Bruksexemplene i `sqlite/obt_tagger.py` bruker nå en generell sti (`/sti/til/tekst.txt`). Ingen kode var avhengig av filen.
- Eldre loggoppføringer som nevner filen (del 21–24), er ikke endret.

**Neste steg**
- Trengs en testtekst igjen, kan en kort, åpen tekst legges til på nytt.

---

## 2026-11-20 (del 44) — Pull request: `multitagger-oppsett` inn i `main`

**Dato/agent:** 2026-11-20, Claude (Opus 5.5) sammen med Marie

**Hva ble gjort**
- Marie opprettet en pull request på GitHub fra `multitagger-oppsett` til `main` (via nettleseren, siden GitHub CLI ikke er installert). Claude skrev tittel og beskrivelse.
- Pull requesten inneholder også `figurer-deck` og `rapport-verbtyper` (flettet inn i del 41).

**Neste steg**
- Marie fletter når kollegaen har gitt klarsignal.
- Etter flettingen bør `main` flettes inn i `figurer-deck` før nye loggoppføringer skrives der, så nummereringen fortsetter fra del 45 og vi unngår konflikt i `logg.md`.

---

## 2026-11-20 (del 45) — Stabilitet over tid: n-gram for bøker med flertydige former fordelt etter OBT per tiår

**Dato/agent:** 2026-11-20, Claude (Opus 5.5) sammen med Marie

**Hva ble gjort**
- PR #5 (`multitagger-oppsett` → `main`) ble flettet av Marie etter klarsignal fra kollegaen. `multitagger-oppsett` og `notebook-dataoppslag` (helt inneholdt i `main`) er slettet. `rapport-verbtyper` og `figurer-deck` er kollegaens og er ikke rørt.
- Ny gren `stabilitet-obt-fordeling`. Navnet viser at dette er én mulig analyse av stabilitet, basert på taggingen.
- Metode, avtalt med Marie:
  - Entydige former hentes rett fra NBs n-gram for bøker (bokmål, 1950–2020).
  - Flertydige former fordeles med andelen leksemet har av formen i det OBT-taggede korpuset, regnet per tiår fra bøkene (skjønn- og faglitteratur).
  - Aviser er holdt utenfor foreløpig: n-gram for aviser har ikke bokmålsfilter (*ikkje* ≈ 10 % av *ikke* + *ikkje* mot under 2 % i bøkene), mens OBT-andelene er fra bokmålsaviser.
- Ny modul `sqlite/stabilitet_obt.py` (`python -m sqlite.stabilitet_obt`):
  - Eksempellemmaer: substantiv *fisk*, *fisker*, *dør*, *krone*; verb *dø*, *gå*, *svare*, *sette*, *bygge*.
  - Andeler per tiår med Wilson-intervall. Under 30 koblede forekomster i tiåret brukes andelen for hele perioden.
  - Fire varianter: `obt_tiaar`, `obt_fast` (én andel for hele perioden), `decomposer` (regler, per tiår på n-gram-tallene) og `naiv` (rå formtall).
  - Stabilitetsmål: gjennomsnittlig endring mellom påfølgende tiår og største avvik fra snittprofilen (pp).
  - Skriver `resultater/stabilitet_obt_andeler.tsv` og `resultater/stabilitet_obt_profiler.tsv`.

**Funn**
- **Former der ett leksem dominerer** (*går* 91–96 % *gå*, *kroner* 96–99 % *krone*, *sett* 0 % *sette*, *svarer* 98–100 %): variantene gir nesten samme profil, og stabilitetsbildet er robust.
  - *gå*: preteritum går ned fra 41 % (1950-tallet) til 33 % (1980–90-tallet) og opp igjen til 39 % (2020).
  - *krone*: flertall ubestemt stiger fra 81 til 89 %.
  - *fisk*: entall ubestemt er stabil rundt 67–70 % med OBT-fordeling, men 52–61 % med naive tall, fordi *fisker* (flertall) er overtelt.
- **Former der flere leksemer har store andeler** (*satt*: *sette*/*sitte*; *dør*: *dø*/*dør*; *døde*: *dø*/*død*; *svart*/*svarte*: *svare*/adjektivet *svart*): OBT-andelene per tiår svinger mye (*satt* 19–43 %, *dør* som verb 33–72 %, *døde* 58–87 %).
  - Svingningene skyldes i stor grad hvilke bøker som er med. Innenfor ett tiår varierer andelen for *satt* fra 6 til 78 % mellom bøkene, og et tiår har bare 6–10 bøker per teksttype.
  - Variant `obt_tiaar` ser derfor *mindre* stabil ut enn de andre for slike lemmaer (*sette* 10,4 pp per tiår mot 5,3 naivt; *dø* 5,1 mot 2,0). Det er i stor grad målestøy, ikke språkendring.
  - Wilson-intervallene er regnet per forekomst og er for smale, fordi forekomster i samme bok ikke er uavhengige.
- **Decomposer** gjentar feilene fra valideringen (del 42): *svart* og *svarte* gis 100 % til *svare* (adjektivet mangler), *kroner* bare 60–64 % til *krone*, og *fisker* 47–61 % til *fisk*.

**Vurdering (Marie og Claude):** Med dagens korpus (6–10 bøker per teksttype og tiår) er fordelingen av flertydige former per tiår for avhengig av enkeltbøker til å gi en god analyse av stabilitet over tid, unntatt for former der ett leksem dominerer. Analysen legges til side inntil videre. Oppsettet kan kjøres på nytt med et større korpus.

**Neste steg** (ikke avtalt)
- Usikkerhet med bootstrap over dokumenter (boka som enhet), for å skille ekte endring fra utvalgsstøy i andeler og profiler.
- Alternativt bredere tidsvinduer (f.eks. 20 år) eller et større tagget korpus for formene der flere leksemer har store andeler.
- Rapport når metoden er avklart.

---

## 2026-11-20 (del 46) — Korpuset utvidet til fem ganger størrelsen, i lag; fulltekster hentet

**Dato/agent:** 2026-11-20, Claude (Opus 5.5) sammen med Marie

*Merk: del 45 ligger på grenen `stabilitet-obt-fordeling`, som ikke er flettet inn i `main` ennå. Denne grenen (`korpus-utvidelse`) er laget fra `main`.*

**Hva ble gjort**
- Marie ønsket et større korpus i reserve. Det skal ikke tagges nå; omfanget avgjøres senere sammen med kollegaen.
- Avtalt: fem ganger så stort, trukket i fire nye lag. Hvert lag er balansert som det opprinnelige (3 teksttyper × 8 tiår, ca. 417 000 ord per celle), slik at man kan tagge bare noen lag.
- `sqlite/korpusutvalg.py`:
  - ny funksjon `utvid_korpus` og valgene `--utvid` / `--nye-lag`, og ny kolonne `lag` (det opprinnelige korpuset = lag 1);
  - ingen dokumenter trekkes to ganger;
  - bøker: maks én bok per forfatter per celle i hele korpuset (alle lag), for å få mange ulike forfattere;
  - aviser: maks 3 numre per tittel per celle i hvert lag;
  - dhlabid sammenlignes som tekst.
  - Eksempelet «liten prøve» i dokumentasjonen er rettet (`--totalt 2400000`). Med 240 000 ord blir maksgrensen per dokument (35 % av cellemålet) lavere enn `MIN_ORD_BOK`, så ingen bøker kan velges.
- Kjørt: `python -m sqlite.korpusutvalg --utvid korpus/korpusoversikt.tsv --nye-lag 4 --ut korpus/korpusoversikt.tsv` (via en midlertidig fil, kontrollert før den erstattet oversikten).
- Fulltekstene er hentet med `hent_fulltekster.py` (utenfor repoet) til samme mappe som før, utenfor repoet og OneDrive.

**Funn**
- `korpus/korpusoversikt.tsv`: 1 097 dokumenter, 53 588 547 ord.

  | lag | dokumenter | ord |
  |---|---|---|
  | 1 | 224 | 10 724 916 |
  | 2 | 219 | 10 655 322 |
  | 3 | 222 | 10 686 218 |
  | 4 | 211 | 10 698 299 |
  | 5 | 221 | 10 823 792 |

- Kontroller:
  - alle 120 celler (lag × teksttype × tiår) har nådd ordmålet (minst 416 686 ord);
  - lag 1 er uendret felt for felt;
  - ingen duplikater (dhlabid, URN);
  - ingen forfatter mer enn én gang per celle;
  - maks 2 numre per avistittel per celle og lag (4 totalt);
  - bokmålsandel ≥ 0,95 for alle med nok markørord (6 bøker uten nok markørord, som i det opprinnelige utvalget).
- Per celle over alle lag: 32–39 skjønnlitterære bøker, 35–47 faglitterære bøker og 40–88 avisnumre.
- Fulltekster: 1 097/1 097 hentet, 267 MB. Antall ord er identisk med `n_ord` for alle.

**Neste steg**
- Marie kopierer de nye tekstene til Linux-maskinen.
- Tagging venter på avklaring med kollegaen: for eksempel lag 2 for et dobbelt så stort korpus, eller alle lag.
  - Med `tagg` hoppes allerede taggede dokumenter over.
  - Databasen blir ca. 1,5 GB ved alle lag, noe som påvirker deling via Git LFS.

---

## 2026-11-20 (del 47) — Adjektivet i «døde» (hull 5)

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Ny `sqlite/adjektiv_gold.py`: gullstandard for adjektiv, dvs. 1 852 lemmaer i `boy_gruppe 'adjektiv'` der m/f, e-form og nøytrum er innbyrdes ulike og helt entydige. 1 840 av dem er belagt i bokkorpuset. Skriptet kryssvaliderer log-regresjonen for e-formen.
- `sqlite/decomposer.py`:
  - `GOLD_SLOTS["adjektiv"] = (1, 2, 4)`; kategori 3 (be ent) slås sammen med 2 (fl) via `SLOT_ALIAS`.
  - Adjektiv kan bruke ett anker (`MIN_ANCHORS_BY_BG`), fordi paradigmet bare har to mulige ankre.
  - Nytt felt `calibration` (sum ukappede anslag / observert). CLI-et gir advarsel utenfor 0,5–2 (`CALIBRATION_OK`).
- `rapport_verbtyper.md` §7.2 punkt 5 er skrevet om med tabell. Ny tekst om adjektiv i `rapport_dekomponering_validering.md` §6. Lysbilde 11 (boks og notat) og plan (hull 5, rad 10) er oppdatert.
- Bigrammer (*den døde* / *han døde*) ble prøvd: bok-API-et gir 0 treff for flerordsuttrykk, og n-gram-viewer-endepunktet (`fetch_ngram_sp`) svarer med 301 / HTML. Tomme bigramrader i den lokale cachen er slettet.

### Funn
- Adjektivmodellen: typisk avvik ×1,67 (m/f + nøyt) og ×1,91 (bare nøyt) i bøker, uten skjevhet.
- «døde» i bøker: 57 % *dø* / 39 % *død* / 4 % *døde*, men sum / obs. er **0,05**. Ankrene i ordfamilien er atypiske: *dødd* er sjelden (adjektivet tar partisippets plass: *er død*), *dødt* er sjelden, og *dødene* har 25 treff. «død» har samme problem (0,19). **Adjektivandelen er ikke bestemt av ordboksankrene.**
- Overslag for adjektivandelen: 2 % (alle adjektiv; frekvente *-t*-former er ofte adverb) til 14–35 % (tilstandsadjektiv *blind, naken, syk, gammel*) og 46 % (grovt overslag fra del 17). *dø* er 2A så lenge adjektivet er under **76,5 %** av «døde». Profil: pret 74–61 / inf 18–26 / pres 9–13 %.
- «dør» er robust for at *dødd* er atypisk. Med bare infinitiv som verbanker blir verbandelen 34,8 % i stedet for 36,5 %.

### Neste steg
- En presis adjektivandel krever kontekstdata (bigrammer eller konkordanser fra DH-lab). Det er ikke nødvendig for foredraget.
- Referanser (hull 6) og figur for paradigmegrafen.

---

## 2026-11-21 (del 48) — Referansene sjekket (hull 6)

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Alle referansene i `rapport_verbtyper.md` §7.1 er sjekket mot forlags- og repositorieoppføringer, og Janda & Lyashevskaya også mot sin egen referanseliste. §7.1 er skrevet om og har nå en full referanseliste.
- Lysbilde 14 «Hva er nytt?» har fått rettet etikett og Milin-referanse og nytt talenotat. Planen er oppdatert (rad 13 og hull 6).

### Funn
- **Feil i rapporten:** «Paradigms bit by bit» er ikke av Milin, Filipović Đurđević & Baayen i *Cognitive Linguistics* 20(1). Det er Milin, Kuperman, Kostić & Baayen 2009 i Blevins & Blevins (red.), *Analogy in Grammar*, OUP, s. 214–252. Funnet om relativ entropi mellom leksemets og klassens profil er Milin, Filipović Đurđević & Moscoso del Prado Martín 2009, *Journal of Memory and Language* 60(1), 50–64 (serbiske substantiv).
- Janda & Lyashevskaya 2011 har sidene 717–762 (ikke 719–763; det var manuskriptversjonen). DOI 10.1515/COGL.2011.027.
- Newman 2008 er «Aiming low in linguistics», et konferansebidrag til IsCLL-11 i Hsinchu. Janda & Lyashevskaya siterer også Newman & Rice 2006 og Rice & Newman 2005.
- Karlsson 1986 er bekreftet: ZPSK 39(1), 19–28. Karlsson 1985 er «Paradigms and word forms», *Studia Gramatyczne* 7. «Karlsson 2000» fant jeg ikke, så den er tatt ut.
- Arppe 2006 er «Frequency considerations in morphology, revisited – Finnish verbs differ, too», i festskriftet for Karlsson, s. 175–189.
- Innholdet i Karlsson- og Arppe-arbeidene er bare kjent gjennom sekundærkilder. Begrepet «fokalformer» er derfor ikke lenger tilskrevet Karlsson.

### Neste steg
- Les Karlsson 1986 og Arppe 2006 i fulltekst om lysbilde 14 skal si noe mer spesifikt om dem.
- Figur for paradigmegrafen og oppsummeringslysbildet. Abstractet må samkjøres med dataene for *vite* og *eple*.

---

## 2026-11-21 (del 49) — Figur av paradigmegrafen

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- `sqlite/figurer.py`: ny `fig_paradigm_graph()` → `tekst/figurer/paradigmegraf_fisker.png`.
  - Figuren tegner komponenten rundt «fisker» rett fra `paradigm_graph.inspect_component`, uten hardkodede former.
  - Noder er lemmaer, med de entydige kjerneformene (ankrene) inne i boksen. Partisippformer på *-ende/-ede/-ete* er utelatt.
  - Kantene er merket med de delte formene, og linjetykkelsen viser antallet.
  - Fontvarslene fra matplotlib er dempet.
- Lysbilde 4 viser figuren i stedet for de håndtegnede boksene, har nytt talenotat og er ikke lenger merket UTKAST. Planen (rad 4, hull 2) er oppdatert.

### Funn
- Komponenten er en komplett graf (K4): alle fire lemmaene deler minst «fisker» med hverandre.
- Ankrene er svært ujevnt fordelt:
  - *fisker* (subst.) har tre: *fiskere, fiskeren, fiskerne*.
  - *fisk* har bare *fisken*.
  - Verbet *fiske* har bare s-passiv *fiskes*; *fisk* (imp.), *fiske*, *fisker*, *fiska* og *fisket* deles.
  - Substantivet *et fiske* har **ingen** entydige former. Det kan derfor ikke anslås med ankre.
- Firergrupper som denne er sjeldne: 452 komponenter, 1,2 % av 151 648 lemmaer.

### Neste steg
- Oppsummeringslysbildet (rad 14).
- Samkjøre abstractet med dataene for *vite* og *eple*.

---

## 2026-11-21 (del 50) — Abstractet samkjørt med dataene

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- `abstract.md`: revidert versjon øverst, med en endringstabell og den innsendte versjonen uendret nederst.
- Lysbilde 2 har nye eksempler: tre verb og tre substantiv med ulik form på topp. Chipsene har lik bredde, og UTKAST-merket er fjernet. Talenotatet forklarer endringene. Planen er oppdatert.

### Funn / beslutninger
- *vite* og *eple* er beholdt med riktig retning: **vet** 55 % og **epler** 45 % er formene på topp, og begge har samme toppform alle 71 år.
- *gå* er erstattet med *forsvinne* (pret 54 %, topp alle 71 år). *gikk* er på topp bare 70 % av årene, og «går» inkluderer *i går*.
- *buss* er erstattet med *sommer* (ent be 69 %). Alle formene til *buss* kolliderer med *busse* i Ordbanken.
- *vurdere* (inf 70 %) og *tid* (ent ub 63 %) er lagt til, slik at hver kategori har et eksempel.
- Abstractet nevner nå valideringen (riktig hovedleksem i om lag fire av fem kunstige homografer).
- Merk: den reviderte teksten er ikke sendt til konferansen. Om den skal brukes i programmet, må det avgjøres av forfatterne.

### Neste steg
- Oppsummeringslysbildet (rad 14).
- Sjekke merge-konflikter og åpne pull requests (brukerens ønske).

---

## 2026-11-21 (del 51) — `main` flettet inn i `figurer-deck`

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- `origin/main` er flettet inn i `figurer-deck`, slik at PR 6 kan flettes uten konflikt. Det inkluderer PR 5 (`multitagger-oppsett`).
- Eneste konflikt var `logg.md`: begge grenene hadde brukt del 21–24. Konflikten er løst ved å bruke `main` sin logg uendret. Oppføringene fra `figurer-deck` (adjektivet i «døde», referanser, paradigmegraf og abstract) er lagt til etter del 44 som **del 47–50**. Del 45 og 46 er holdt av til oppføringene på `stabilitet-obt-fordeling` og `korpus-utvidelse`, som ikke er flettet ennå.
- Etter flettingen er det kontrollert at `python3 -m sqlite.decomposer dør --korpus book` gir de samme tallene som før (63,5 / 36,5 %).

### Åpent spørsmål
- `rapport_dekomponering_obt.md` (del 42) ble kjørt før dekomponereren fikk adjektivankre (del 47). Gruppen «umodellert ≥ 5 %» består mest av former der OBT gir et adjektiv. De tallene vil trolig endre seg ved en ny kjøring av `python3 -m sqlite.valider_dekomponering_obt`. Rapporten er ikke endret; det bør avtales med den som skrev den.

---

## 2026-11-21 (del 52) — OBT-valideringen kjørt på nytt med adjektivankre

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- `sqlite/korpus_profiler.py`: `_corpus_gold_profiles` bygger nå også adjektiv-gullstandarden. Utvalget gjøres med Ordbankens ekte `nb_totals`, som for substantiv og verb, og frekvensene hentes fra korpuset. Uten denne endringen hadde `decomposer.gold_profiles` valgt adjektivene med korpusets frekvenser.
- `python3 -m sqlite.valider_dekomponering_obt` er kjørt på nytt (ca. 30 sek). `resultater/dekomponering_obt_former.tsv` og `_profiler.tsv` er overskrevet; de gamle filene ligger i commit `390d420`.
- `rapport_dekomponering_obt.md`: ny §9 med de nye tallene. §3–5 er beholdt slik de ble skrevet og merket «første kjøring». Anbefaling 1 er merket som gjennomført for vanlige adjektiv.
- OBT-andelen for «døde» er lagt inn i `rapport_verbtyper.md` §7.2 punkt 5, i lysbilde 11 (boks og notat) og i planen (hull 5).

### Funn
- Innholdsord, logreg: medianavviket gikk fra 18,4 til **13,9 pp**, og riktig leksem størst fra 69 til **73 %**.
- 1 321 former har nå alle kandidatene modellert (før 1 206). 129 former ble mer enn 5 pp bedre, 12 mer enn 5 pp verre.
- **«døde»:** OBT gir 72 % *dø* / 28 % *død* (adj.), og decomposer gir nå 71 / 29 (før 100 / 0). Grunnlaget er bare 0,1. OBT-tallet (28 %) er den beste empiriske kontrollen av adjektivandelen og ligger innenfor spennet for tilstandsadjektiv (14–35 %).
- Profilen til *dø* avviker 6,0 pp fra OBT (før 11,7) og er nå bedre enn rå formtall (8,1 pp).
- **Ny feiltype:** sjeldne adjektiv i ordboka tar for mye når grunnlaget er lite: *grunn* (adj 63 %, OBT 2 %), *bein*, *faren*, *maken*, *engelsk*, *sikre*.
- Fortsatt umodellert: ubøyelige adjektiv (*stille*, *få*), uregelrette (*liten/lille/litt*, *mange/flere*) og adjektiv med flertydige ankre (*hel/helt*, *ny/nytt*).

### Neste steg
- Nedvekte sjeldne ordbokshomografer, eller la grunnlaget styre (anbefaling 2–3 i OBT-rapporten).
- Oppsummeringslysbildet.

---

## 2026-11-21 (del 53) — Oppsummeringslysbildet

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- Lysbilde 15 «Bøyningsprofiler er leksikalske — og stabile» er skrevet om fra en plassholder til fire nummererte kort på innholdslayouten. Planen (rad 14) er oppdatert.
  1. *Hvert leksem har sin favorittform:* alle seks rekkefølger blant 580 verb; substantiv skiller seg først på tall.
  2. *Profilene står stille i 70 år:* samme toppform alle 71 år for 46 % av verbene og 53 % av substantivene.
  3. *Profilene kan brukes baklengs:* riktig hovedleksem i om lag 4 av 5 tilfeller; «dør» 64 % substantiv; *dø* blir 2A.
  4. *Andelene er usikre:* ±10–15 pp; metoden svikter uten entydige former eller når sjeldne ordbokshomografer får for stor vekt.
- Talenotatet viser hvor hvert tall kommer fra.

### Neste steg
- Gå gjennom hele decket for UTKAST-merker og «mangler»-bokser som gjenstår.
- Nedvekte sjeldne ordbokshomografer i dekomponereren (OBT-rapporten §9).

---

## 2026-11-21 (del 54) — Maries grener flettet inn i `figurer-deck`

**Agent:** Claude Code (Claude Opus 5.5)

### Hva ble gjort
- `stabilitet-obt-fordeling` (del 45) og `korpus-utvidelse` (del 46) er flettet inn i `figurer-deck`, slik at de følger med PR 6 til `main`.
- Eneste konflikt var `logg.md`. Oppføringene er satt inn i nummerrekkefølge: del 45 og 46 kommer etter del 44 og før del 47. Ingen tekst er endret.
- Nye filer fra grenene: `sqlite/stabilitet_obt.py`, `resultater/stabilitet_obt_profiler.tsv` og utvidet `sqlite/korpusutvalg.py` og `korpus/korpusoversikt.tsv` (1 097 dokumenter i fem lag).

### Observasjoner
- Det utvidede korpuset er ikke tagget (del 46). `korpus/obt_frekvenser.db` er uendret, så OBT-valideringen fra del 52 gjelder fortsatt. Den bør kjøres på nytt hvis flere lag tagges.
- Del 45 legger stabilitetsanalysen per tiår til side: med 6–10 bøker per teksttype og tiår er fordelingen av flertydige former for avhengig av enkeltbøker. Analysen ble kjørt før adjektivankrene, så decomposer-tallene for *svart/svarte* der er utdatert.

### Neste steg
- Møte mandag: gå gjennom PR 6, de tre UTKAST-lysbildene og hvor mye av det utvidede korpuset som skal tagges.
