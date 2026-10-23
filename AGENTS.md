# AGENTS.md — Leksikalske bøyningsprofiler (MONS-prosjektet)

Dette dokumentet er hovedkontrakten og koordineringsflaten for AI-agenter og mennesker som jobber sammen på prosjektet **«Leksikalske bøyningsprofiler: ordboksdata og historiske n-gram»** frem mot **MONS-konferansen i slutten av november**.

---

## 1. Obligatorisk arbeidsflyt for AI-agenter (AI-Native Engineering)

Fordi token-budsjettet og kontekstvinduet tømmes over tid og ulike AI-modeller/agenter vil ta over stafettpinnen, gjelder følgende ufravikelige regler:

1. **Les alltid før du starter:**
   - Les `AGENTS.md` (denne filen)
   - Les `abstract.md` (prosjektets faglige ramme og hypoteser)
   - Les de siste oppføringene i `logg.md` for å se hva som nylig er gjort, hvilke beslutninger som er tatt, og hva som er neste steg.
2. **Oppdater alltid `logg.md`:**
   - **Hver gang** en oppgave, et skript, en notebook eller en analyse er utført (og alltid før en økt avsluttes), skal du skrive en kort, datert oppføring i `logg.md`.
   - Oppføringen i `logg.md` skal inneholde:
     - **Dato/tid og agent/modell**
     - **Hva som ble gjort** (endrede/opprettede filer, spørringer, figurer, analyser)
     - **Viktige funn eller tekniske observasjoner** (f.eks. datakvalitet, homografi-utfordringer, resultater)
     - **Neste naturlige steg / åpne spørsmål**
3. **Samarbeid med menneske og Jupyter Notebooks:**
   - Prosjektet kombinerer ren kode (`sqlite/`, Python-moduler) med interaktiv utforskning i **Jupyter Notebooks** (`notebooks/`) og tekstproduksjon (`tekst/` eller artikkel/presentasjonsutkast).
   - Hold tung logikk, SQL-spørringer og hjelpefunksjoner i importerbare Python-filer (f.eks. `sqlite/queries.py`), slik at notebooks blir ryddige, lesbare og lette for både mennesker og AI å redigere videre.
   - Ikke overskriv menneskeskrevne celler eller tekst uten at det er etterspurt.

---

## 2. Faglig kjerne (kort oppsummert fra `abstract.md`)

Vi kombinerer **Norsk Ordbank (bokmål)** med **historiske n-gramdata fra Nasjonalbiblioteket (NB / dhlab)** for å undersøke:
1. **Kvantitative bøyningsprofiler:** Hvordan fordeler bruken av et leksem seg mellom bøyningsformene i paradigmet, og hvor stabile er disse proporsjonene over tid?
   - *Verb (infinitiv vs. presens vs. preteritum):* f.eks. dominerer preteritum *«gikk»* over *«gå»* og *«går»*, mens infinitiv *«vite»* dominerer over *«vet»* og *«visste»*.
   - *Substantiv (ubestemt/bestemt × entall/flertall):* f.eks. dominerer ubestemt entall *«eple»* over *«eplet»* og *«epler»*, mens bestemt entall *«bussen»* dominerer over *«buss»* og *«busser»*.
2. **Flertydige ordformer vs. entydige holdepunkter (dekomponering):**
   - N-gram teller overflateformer (*oppslag*), ikke leksemer. Ordformen *«fisker»* summerer verbet *fiske* (presens), substantivet *fisker* (entall ubestemt), substantivet *fisk* (flertall ubestemt) og substantivet *fiske* (flertall ubestemt).
   - **Entydige former** i paradigmet (som *«fisken»* for *fisk*, eller *«fiskeren»/«fiskere»/«fiskerne»* for *fisker*) gir direkte observerbare holdepunkter.
   - Vi undersøker hvordan stabile proporsjoner i bøyningsprofilene + entydige holdepunkter kan brukes til å estimere leksemfordelingen bak flertydige ordformer over tid.

---

## 3. Prosjektstruktur

```text
/Users/larsj/Github/Bøyning/
├── AGENTS.md                           # Instruksjoner og arkitektur for AI-agenter (denne filen)
├── logg.md                             # Løpende arbeids- og overleveringslogg mellom agenter/økter
├── abstract.md                         # MONS-abstractet (faglig referanse)
├── 20220201_norsk_ordbank_nob_2005/    # Rådata fra Norsk Ordbank (ISO-8859-1 TSV-filer, CRLF)
│   ├── boying.txt                      # 62 rader: bøyningskategorier (boy_nummer, boy_gruppe, boy_tekst)
│   ├── boying_grupper.txt              # 24 rader: ordklasse/bøyningsgrupper
│   ├── fullformsliste.txt              # 1 143 887 rader: alle bøyningsformer knyttet til lemma_id og paradigme_id
│   ├── leddanalyse.txt                 # 180 366 rader: sammensetnings-/leddanalyse (simplex vs. sammensatt)
│   ├── lemma.txt                       # 154 824 rader: lemma_id og grunnform
│   ├── lemma_paradigme.txt             # 255 079 rader: kobling mellom lemma_id og paradigme_id
│   ├── paradigme.txt                   # 803 rader: paradigmedefinisjoner og ordklasse
│   └── paradigme_boying.txt            # 5 413 rader: suffikser/uttrykk per paradigme og boy_nummer
└── sqlite/                             # SQLite-database, byggeskript, n-gram-klient og spørringsbibliotek
    ├── build_db.py                     # Konverterer TSV (latin1) -> sqlite/ordbank.db (UTF-8) med indekser/tabeller
    ├── ordbank.db                      # Ferdigbygd SQLite-database (regenereres på ~13 sek ved behov)
    ├── queries.py                      # Python-API for oppslag av paradigmer, bøyningsprofiler og flertydighet
    ├── ngram.py                        # Henter og cacher NB n-grammer (api.nb.no/dhlab og sp_tjenester) i ngram_cache.db
    ├── ngram_cache.db                  # Lokal SQLite-cache for hentede n-gram-tidsserier
    └── analyze_profiles.py             # Skript for å beregne bøyningsprofiler og tidsstabilitet (1950–2020)
├── notebooks/                          # Jupyter Notebooks for interaktiv utforskning og visualisering
    └── 01_paradigmeprofiler_og_stabilitet.ipynb
```

---

## 4. Viktig domenekunnskap om Norsk Ordbank (`sqlite/ordbank.db`)

Når du skriver SQL-spørringer eller analyserer data fra `sqlite/ordbank.db`, **må** du kjenne til følgende egenskaper ved Norsk Ordbank:

1. **Paradigme-multiplisitet i `fullformsliste`:**
   - Ett og samme `lemma_id` har ofte flere rader i `fullformsliste` for nøyaktig samme ordform (`oppslag`) og bøyningskategori (`boy_nummer`).
   - *Eksempel:* Verbet *fiske* (`lemma_id = 17307`) har tre paradigmer (`001`, `010`, `011` for hhv. *-a* og *-et* i preteritum/partisipp). Alle tre paradigmene har presensformen *«fisker»* (`boy_nummer = 2`). Hunnkjønnssubstantiv har også egne paradigmer for maskulin og feminin bøyning, som deler *ent ub* og *fl*.
   - **Løsning:** Bruk **alltid** den materialiserte og dedupliserte tabellen `lemma_former` (eller viewet `v_lemma_former`) i stedet for rå `fullformsliste` når du teller analyser eller henter bøyningsprofiler! I `lemma_former` er alternative paradigmer og mask/fem-varianter slått sammen per `(lemma_id, grunnform, pos, boy_gruppe, boy_nummer, oppslag)` for alle rader der `normering = 'normert'`.

2. **Homografe lemmaer (flere `lemma_id` med samme `grunnform`):**
   - Norsk Ordbank skiller mellom homografe leksemer med ulike `lemma_id`, selv innenfor samme ordklasse.
   - *Eksempel:* `grunnform = 'buss'` (substantiv, kjøretøy, `lemma_id = 9789`), men det finnes også substantivet `grunnform = 'busse'` (`lemma_id = 9794` og `9795`, som i bestemt entall også heter *«bussen»* og i ubestemt flertall *«busser»*!) samt verbet `busse` (`lemma_id = 9793`, presens *«busser»*, imperativ *«buss»*).
   - Når vi sjekker om en form er «entydig» i praksis, må vi være bevisste på at sjeldne ordbokshomografer (som subst. *busse* eller verb *gåre* i imperativ *«går»*) gir formell flertydighet i ordbanken, selv om ett leksem står for >99 % av bruken i korpuset.

3. **Sentrale bøyningsnumre (`boy_nummer`):**
   - **Substantiv (`boy_gruppe = 'substantiv'`):**
     - `1`: `ent ub` (entall ubestemt) — f.eks. *eple*, *buss*, *fisk*
     - `2`: `ent be` (entall bestemt) — f.eks. *eplet*, *bussen*, *fisken*
     - `3`: `fl ub` (flertall ubestemt) — f.eks. *epler*, *busser*, *fisker*
     - `4`: `fl be` (flertall bestemt) — f.eks. *epla/eplene*, *bussene*, *fiskene*
   - **Verb (`boy_gruppe = 'verb, normal'`):**
     - `1`: `inf` (infinitiv) — f.eks. *gå*, *vite*, *fiske*
     - `2`: `pres` (presens) — f.eks. *går*, *vet/veit*, *fisker*
     - `3`: `inf pres pass` (s-passiv) — f.eks. *gås/gåes*, *vites*, *fiskes*
     - `4`: `pret` (preteritum) — f.eks. *gikk*, *visste*, *fiska/fisket*
     - `5`: `perf-part` (supinum) — f.eks. *gått*, *visst*, *fiska/fisket*
     - `11`: `imp` (imperativ) — f.eks. *gå*, *vit*, *fisk*

4. **Lynraske oppslag (< 1 ms):**
   - Tabellene `lemma_former` og `ordform_flertydighet` er ferdig materialisert og indeksert i `sqlite/ordbank.db`. Bruk disse direkte eller via funksjonene i `sqlite/queries.py`.
