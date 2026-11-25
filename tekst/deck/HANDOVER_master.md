# Overlevering: master-presentasjonen for MONS (`tekst/mons_master.pptx`)

*Fra Claude (Opus 5.5), som jobbet sammen med Marie, til agenten som jobber videre med Lars.
Skrevet 2026-11-23. Se også `logg.md` del 68.*

## 1. Hva som gjelder nå

- **`tekst/mons_master.pptx` er den gjeldende presentasjonen.** Marie og Lars jobber videre i den
  fram mot MONS.
- **Kilden er `tekst/deck/build_master.js`.** Alle endringer gjøres i skriptet, og pptx-en bygges på
  nytt. Ikke rediger pptx-en direkte, da blir endringene overskrevet ved neste bygging.
- `build_deck.js` / `mons_presentasjon.pptx` (hoveddecket til 2026-11-21) og `build_tillegg.js` /
  `mons_nytt_siden_fredag.pptx` (arbeidsdecket til møtet 2026-11-23) er **historikk**. De er ikke
  endret og skal ikke oppdateres videre. De ligger igjen som referanse.
- `tekst/mons_presentasjon_plan.md` er **ikke oppdatert**. Lysbildenumrene der viser til det gamle
  hoveddecket, se kartet i §3.

## 2. Hvordan master ble laget

1. `build_master.js` er en kopi av `build_deck.js`. Tema, layouter (`TITTEL`, `INNHOLD`),
   hjelpefunksjoner og stil er uendret.
2. Fire lysbilder er hentet uendret fra `build_tillegg.js`: formelen, «døde», kontekstrater og
   bigramvalideringen. To av dem har fått kortere titler, så de holder seg på én linje.
3. To nye lysbilder om det utvidede OBT-korpuset (lag 1–5, 43,7 mill. tokens).
4. Lysbildene om «dør», «fisker», «Hva er nytt?» og oppsummeringen er oppdatert (se §3).
5. Ny hjelpefunksjon `note()`: en sand-farget «MERK»-boks i samme stil som `missing()`. Den brukes
   for innhold som er motsagt av nye data og må avklares.
6. Overgangsskriptet som gjorde dette, er ikke lagret. `build_master.js` er nå eneste kilde.

**Ikke tatt med fra «Nytt siden fredag»** (ligger fortsatt i `build_tillegg.js` hvis dere vil ha dem):
- tittel og «Til møtet» (bare for møtet);
- «Dekomponereren mot tagget korpus: fire forbedringer» (lag 1; erstattet av det nye lysbilde 19);
- «dør og tro over tid» (finnes allerede i hoveddecket);
- infinitivstyrere, frukt, matbøker og Koselleck (utforskende, ikke en del av foredraget foreløpig).

## 3. Lysbildekart (22 lysbilder)

| # | Tittel | Kilde | Endring |
|---|---|---|---|
| 1 | Leksikalske bøyningsprofiler | deck 1 | – |
| 2 | Hvert leksem har sin favorittform | deck 2 | – |
| 3 | To datakilder, koblet på ordform | deck 3 | – |
| 4 | Én form, flere leksemer | deck 4 | – |
| 5 | Gullstandard: former uten konkurrenter | deck 5 | Sett B i egen boks; ny rad for substantiv (6 007 → 5 799 Sett A), logg del 72 |
| 6 | Seks verbtyper, ikke tre | deck 6 | – |
| 7 | Hvert verb er et punkt i trekanten | deck 6b | – |
| 8 | Rangeringen står stille i 70 år | deck 7 | – |
| 9 | Substantiv velger tall før bestemthet | deck 8 | – |
| 10 | Én bok bruker sjelden hele paradigmet | deck 9 | – |
| 11 | Én formel bak alle anslagene | tillegg 2 | ny i hoveddecket |
| 12 | «dør» er mest et substantiv | deck 10 | MANGLER om «døde» erstattet av **MERK** (se §4) |
| 13 | «døde»: adjektivet er 28 %, og dø er fortsatt 2A | tillegg 3 | stat-teksten nevner 29 % med alle lag |
| 14 | «fisker» fordelt på leksemer over tid | deck 11 | MANGLER erstattet av **MERK** (se §4) |
| 15 | Bare verbet har stabile kontekster | tillegg 5 | kortere tittel |
| 16 | Bigrammer treffer best: 5 pp median | tillegg 6 | kortere tittel |
| 17 | Fra ordboka til kurven: «dør» og «tro» | deck 12b | – |
| 18 | Hvor godt treffer metoden? | deck 12 | – |
| 19 | 44 mill. ord tagget: samme treff, samme svakhet | **ny** | UTKAST |
| 20 | Endringer som tåler valg av fordeling | **ny** | UTKAST |
| 21 | Hva er nytt? | deck 13 | nytt punkt: «Validert mot 44 mill. ord tagget med Oslo-Bergen-taggeren» |
| 22 | Bøyningsprofiler er leksikalske — og stabile | deck 14 | funn 3 og 4 oppdatert |

Seksjoner: Innledning (1–3), Metode (4–5), Verb (6–8), Substantiv (9), Enkeltbøker (10),
Dekomponering (11–20), Avslutning (21–22).

## 4. Åpne spørsmål som må avklares før foredraget

1. **«dør» (lysbilde 12).** Tittelen og 64 % substantiv (paradigmeanslaget i bokkorpuset) er motsagt
   av to uavhengige kilder:
   - OBT-korpuset med alle lag: 50 % substantiv / 50 % verb (`rapport_dekomponering_obt.md` §3);
   - bigrammene: 51 % verb (`rapport_dekomponering_tid.md` §8).

   OBT-korpuset er et annet utvalg enn bokkorpuset, men forskjellen er stor. Tittel, stat og
   konklusjonen «dø blir 2A» bør vurderes på nytt. Sjekk om 2A holder med ca. 50 % verb i «dør».
2. **«fisker» (lysbilde 14).** Figuren viser fisk (flertall) 57–74 % (paradigmeanslaget lært i
   bokkorpuset). I OBT-korpuset er bare 6–20 % av «fisker» flertall av fisk i bøkene, per tiår
   (`rapport_stabilitet_obt.md` §4.1). Med alle lag er fordelingen 57 % å fiske, 33 % en fisker og
   10 % fisk. Nivået i figuren er sannsynligvis feil. Bare retningen kan eventuelt beholdes.
3. **Lysbilde 19–20 er UTKAST.** Tallene er fra Maries analyser 2026-11-23:
   - 19: `rapport_dekomponering_obt.md` §3, `resultater/alle_lag/dekomponering_obt_former.tsv`;
   - 20: `rapport_stabilitet_obt.md` §4, `resultater/alle_lag/stabilitet_obt_profiler.tsv`, variant
     `obt_tiaar`.

   Lysbilde 20 viser bare robuste kurver. Usikkerhet med bootstrap over dokumenter er ikke regnet ut.
4. **Lysbilde 16** bruker OBT-tall fra lag 1 (150 homografer). Den kombinerte valideringen
   (`sqlite/kombinert.py`) er ikke kjørt på nytt med alle lag.
5. **Fortsatt UTKAST fra før:** 12, 14, 17 og 21. Navn på foredragsholdere mangler på lysbilde 1.
6. **Lengde:** 22 lysbilder er mye for et vanlig konferanseinnlegg (ca. 1,5–2 min per lysbilde). Vurder
   å flytte noe av dekomponeringsdelen (11–20) til et reservelysbilde.

## 5. Data og kilder for de nye tallene

- **Det OBT-taggede korpuset:**
  - 1 076 av 1 097 dokumenter tagget (21 tidsavbrudd i `mtag.py`);
  - 43,7 mill. tokens; 3 teksttyper × 8 tiår 1950–2026, i fem balanserte lag (logg del 46 og 64);
  - oversikt: `korpus/korpusoversikt.tsv` (kolonnen `lag`).
- **Databasen med alle lag** (1,37 GB, bare telletall) er **ikke i repoet**. På Linux-maskinen ligger
  den i `/mnt/md0/paradigmeanalyse_tagget_korpus/obt_frekvenser_alle_lag.db` (lesbar for alle; logg
  del 67). `korpus/obt_frekvenser.db` i repoet (Git LFS) har bare lag 1.
- **Gjenskaping:** analysene kjøres med `--db <databasen>`:
  - `python -m sqlite.valider_dekomponering_obt --db … --ut resultater/alle_lag`
  - `python -m sqlite.stabilitet_obt --db … --ut resultater/alle_lag`
  - `python -m sqlite.morfologisk_variasjon --db … --utvalg 200000`

## 6. Bygging og kontroll

```bash
# pptxgenjs 3.12.0 (MIT) må være installert et sted utenfor repoet
NODE_PATH=<sti>/node_modules APPLY_THEME_JS=<pptx-skill>/scripts/apply_theme.js \
  node tekst/deck/build_master.js
python <pptx-skill>/scripts/office/validate.py tekst/mons_master.pptx
```

- `APPLY_THEME_JS` skriver temafargene inn i pptx-en. Uten den brukes Offices standardpalett for
  scheme-farger.
- På Maries Windows-maskin: bærbar Node i `C:\Users\marier\opt\node-v20.18.0-win-x64` og pptxgenjs i
  `C:\Users\marier\opt\node_pakker\node_modules`. Visuell kontroll er gjort ved å eksportere
  lysbildene til PNG med PowerPoint (COM).
- Kontrollert 2026-11-23:
  - `validate.py` er bestått;
  - lysbilde 12, 14, 19, 20, 21 og 22 er sjekket visuelt, uten overflyt eller overlapp;
  - lysbilde 15 og 16 ble sjekket med de gamle, lange titlene (de brøt over to linjer); de kortere
    titlene er ikke sett på som bilde;
  - lysbilde 11 og 13 er ikke sett på, men har samme oppsett som i `build_tillegg.js`;
  - de øvrige lysbildene er uendret fra hoveddecket.

## 7. Arbeidsflyt

- Følg `AGENTS.md`: egen gren og pull request, og en oppføring i `logg.md` for hver endring.
- Logg del 68 beskriver opprettelsen av master. Neste ledige del er 69. Sjekk `main` før du skriver,
  i tilfelle flere oppføringer har kommet til.
- Endringer i master: rediger `build_master.js`, bygg på nytt, kjør `validate.py`, se på de endrede
  lysbildene og commit både skriptet og pptx-en.
