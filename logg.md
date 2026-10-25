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
