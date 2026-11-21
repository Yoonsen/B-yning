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

## 2026-11-20 (del 21) — Adjektivet i «døde» (hull 5)

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

## 2026-11-21 (del 22) — Referansene sjekket (hull 6)

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

## 2026-11-21 (del 23) — Figur av paradigmegrafen

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

## 2026-11-21 (del 24) — Abstractet samkjørt med dataene

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
