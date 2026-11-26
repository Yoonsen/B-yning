# Forskningsplan 2027: Paradigmatisk tagging av aggregerte data

*Etter MONS-foredraget 26.11.2026. Mål: en artikkel eller et foredrag i 2027 (Nordisk eller en annen konferanse). Dette er en skisse og ikke en ferdig plan. Den skal drodles videre.*

---

## 1. Kjerneidé

Vi tagger ikke teksten. Vi sier noe om fordelingen bak de aggregerte tallene vi ser.

N-gram teller overflateformer, ikke leksemer. «fisker» er summen av *å fiske* (presens), *en fisker*, *fisk* (flertall) og *et fiske* (flertall). Vi skiller to kilder til informasjon om hvilket leksem en form tilhører:

| | Paradigmatisk | Syntagmatisk |
|---|---|---|
| Kilde | resten av paradigmet (*fiskeren*, *fiskene*, *fisket*) | konteksten rundt forekomsten (*å fiske*, *en fisker*) |
| Verktøy | dekomponering med ankre (`sqlite/decomposer.py`, `sqlite/tidsserie.py`) | tagger (OBT), bigrammer (`sqlite/bigram_kontekst.py`) |
| Trenger | mye data og stabile proporsjoner | tilgang til konteksten (tekst eller n-gram med kontekst) |
| Gir | fordelinger over tid | avgjørelse per forekomst |

Ramme: Jakobson (paradigme mot syntagme; poesien projiserer paradigmet ned på syntagmet). Ordet «paradigme» er selv synkretisk her: bøyningsparadigme og den paradigmatiske aksen.

**Hvorfor det er interessant:** Mye tekst er utilgjengelig av rettighetshensyn, men aggregatene (n-gram, frekvenslister) er tilgjengelige. En metode som analyserer fordelingen i aggregatene uten å se teksten, er en ny måte å arbeide med store tekstmengder på.

## 2. Bøyningsparadigmet som «gratis w2v»

- Word2vec *lærer* paradigmatiske klasser (ord som kan bytte plass) fra syntagmatisk kontekst.
- Bøyningsparadigmet *gir* en paradigmatisk gruppering gratis, fra morfologien og ordboka. Konteksten er morfemene.
- Vanlig tokenisering skjuler dette: *fisken* og *fiskene* er like ulike tokener som *fisken* og *bil*. fastText (w2v med bokstav-n-gram) er et nyttig referansepunkt.
- Metoden vår går motsatt vei av w2v: fra paradigmatisk relasjon til syntagmatisk fordeling.

## 3. Hovedspørsmål

> **Hvilke paradigmatiske grupperinger har stabile indre proporsjoner over tid, og kan derfor brukes som ankre til å fordele flertydige former i aggregerte data?**

Bøyningsparadigmet er bare en delmengde av det paradigmatiske. Kravet for at en gruppe skal fungere som anker, er at forholdet mellom medlemmene (ρ) er stabilt.

| Gruppering | Eksempel | Stabile proporsjoner? | Status |
|---|---|---|---|
| Bøyning | *fisk – fisken – fisker* | ja, for de fleste lemmaer | vist (MONS) |
| Stavevarianter | *moderen – moren*, *hoved – hode* | nei, de skifter med reformene | kan brukes som tidsmarkører |
| Avledning | *lærer – lærerinne – lærerik* | ukjent | ikke testet |
| Sammensetning | *krise – klimakrise – finanskrise* | trolig ustabilt | ikke testet |
| Semantiske felt (Ordvev) | *mor – far – søster* | ukjent | ikke testet |

**Ustabilitet er også et signal.** Når proporsjonene *ikke* holder, er det ofte fordi noe har skjedd i syntagmet. Eksempel: *armen min* mot *min arm* gikk fra 7 % til 77 % mellom 1900–19 og 1940–59, og kroppsordene økte i bestemthet. Slektsordene fulgte 60 år senere (*faren min* 50 % i 2000–20).

## 4. Brukstilfelle: ordboka

En ordbokforfatter ser lemmaet og vil ha kurven for *lemmaet*, ikke for strengen. For «fisker» kan vi gi egne kurver for verbet *fiske*, substantivet *fisker*, *fisk* i flertall og så videre.

Prototypen finnes allerede (`sqlite/tidsserie.py`, `tekst/figurer/fisker_over_tid.png`). For at den skal kunne brukes, trengs:

- **oppslag på `lemma_id`:** kurven settes sammen av alle formene i paradigmet, der de entydige formene telles og de flertydige fordeles;
- **usikkerhetsbånd**, og et flagg når lemmaet mangler gode ankre (*et fiske*);
- **avgrensning:** metoden fungerer best for hyppige ord og lange perioder, altså der det er mye data.

## 5. Det vi har (per 26.11.2026)

Se `logg.md`, særlig del 82–88.

- **Stabile profiler:** Sett A, 580 verb og 5 799 substantiv (`rapport_verbtyper.md`, `rapport_substantivtyper.md`).
- **Dekomponering:**
  - Paradigmeankre gir riktig hovedleksem i 3–4 av 5 tilfeller, bigrammer i 95 % (`rapport_dekomponering_tid.md` §8).
  - *lærer*: paradigmet gir 47 / 43 / 10 %, taggeren 51 / 42 / 7 %.
- **Syntagmet kan lure:**
  - Bigrammet gir «lærer» 78 % verb i 2020 mot 51 % i taggeren.
  - Årsaken er at *som lærer* (45 % av presenskontekstene) oftest er nominalt.
- **Profilen følger semantikken:** Ordvev-klassene viser at kroppsdeler og steder har mye bestemt form, mens egenskaper, tid og hendelser har mye ubestemt entall (`sqlite/ordvev.py`).
- **Løse tråder** (bare skrevet ned, ikke analysert ferdig):
  - *klimakrisen* låser seg på ca. 74 % bestemt entall fra 2005 (Koselleck, kollektivsingular).
  - Nøkkelbegreper har 49–65 % ent be.
  - Situasjonstypene for verb i Ordvev: tilstand 58 % presens, avgrenset 23 %.
- **Paradigmegrafen:** 87 % av lemmaene står alene i ordboka, men bare 29 % av bruken (`sqlite/paradigme_avstand.py`).

## 6. Mulige neste steg

1. **Litteratur:** quantification (Forman 2005 og senere), learning from label proportions, Google Books Ngram med POS (Lin mfl. 2012), fastText. Sjekk om paradigmeankre i n-gram er gjort før.
2. **Test stabilitet utover bøyning:** mål ρ over tid for avledninger, sammensetninger og Ordvev-felt, med samme metode som for bøyning (`rapport_stabilitet_obt.md`).
3. **Kombinere paradigme og syntagme:** bigram der kontekstene er pålitelige, ellers paradigme. Lag en regel for når konteksten lurer (*som*).
4. **Ordbokprototype:** lemma inn, kurver per leksem ut, med usikkerhet. Eventuelt i samarbeid med ordbokmiljøene.
5. **Diffusjon som case:** postnominal possessiv (kroppsord 1920–1950, slektsord etter 1980) som eksempel på at profilendring er et spor av syntaktisk endring. Aviser bør sjekkes når et avisendepunkt er tilgjengelig.
6. **Vekting og datagrunnlag:** `nb_totals` vekter høyfrekvente homografer (*nå*, *når*) fullt hos alle kandidater. Bruk OBT-andeler eller dekomponering til å fordele.

## 7. Åpne spørsmål

- Hvor mye data trengs før paradigmeanslaget er bedre enn en grov regel? Kan det uttrykkes som en terskel?
- Hva gjør vi med lemmaer uten entydige former, som *et fiske*, der alle formene er flertydige?
- Bør paradigmene ta hensyn til tellbarhet og masse? *et fiske* som massebegrep har kanskje ikke flertall i praksis.
- Er det en sammenheng mellom hvor «diskursivt» et ord er (substantiv, nøkkelbegrep) og hvor stabil profilen er?
