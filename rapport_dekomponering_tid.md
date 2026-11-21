# Rapport: Leksemandeler over tid for flertydige former

*Delrapport i MONS-prosjektet, 2026-11-21. Gjenskapes med `python3 -m sqlite.tidsserie dør tro`; figuren `tekst/figurer/dor_tro_over_tid.png` lages av `python3 -m sqlite.figurer`. Logg: del 56.*

## 1. Brukstilfellet

En bruker ser bøyningsparadigmet til et ord i en ordbok, for eksempel *dør* (subst.) eller *tro* (verb), og vil se kurven for *ordet*. N-grammene teller bare overflateformer. «dør» er både *en dør* og presens av *å dø*, og «tro» er både *å tro*, *en tro*, adjektivet *tro* og en sjelden preteritumsform av *å trå*. Kurven for formen må derfor deles på leksemene, år for år. Vi holder oss til «normale» ord og ser bort fra former som har brutt ut av paradigmet (*strålende*).

## 2. Formelen

Formen O har frekvensen f(O) og tilhører cellen cᵢ i paradigmet Pᵢ. Resten av paradigmet (komplementet) har frekvensen Rᵢ.

```
f(O) = Σ xᵢ                     xᵢ = forekomstene av O som tilhører leksem i
πᵢ   = xᵢ / (xᵢ + Rᵢ)           cellens andel av leksemets paradigme
xᵢ   = ρᵢ · Rᵢ                  ρᵢ = πᵢ / (1 − πᵢ), oddsen for cellen
```

- **Anslag for hele perioden:** x̂ᵢ fra `decomposer.estimate_wordform_shares` (log-regresjon på gullstandarden i bokkorpuset; regler som reserve).
- **Over tid:** vi antar stabil profil, altså samme ρᵢ hvert år: xᵢ(t) = (x̂ᵢ / Rᵢ) · Rᵢ(t). Andelen er xᵢ(t) / Σⱼ xⱼ(t).
- **Kalibrering:** Σ x̂ᵢ / f(O) viser om modellen stemmer med det observerte; nær 1 er godt.

## 3. Usikkerhet

Feilen ligger nesten bare i ρᵢ, altså i hvor mye profilen til det enkelte ordet avviker fra den typiske. Den feilen er den samme hvert år.

- Hver kandidat får en faktor exp(σ·z), z ~ N(0, 1), felles for hele perioden. Båndet er 10- og 90-persentilen over 2 000 trekninger.
- σ er kalibrert på de kunstige homografene (`resultater/dekomponering_validering.tsv`): **0,78** for log-regresjon og **0,93** for reglene. Det tilsvarer 90-persentilen på ca. 30 pp i valideringen.
- Fordi feilen er felles for alle år, er **endringen over tid langt sikrere enn nivået.** Begge rapporteres.

## 4. To forbedringer i dekomponereren som trengtes

- **Flertydighet per leksem** (`decomposer.LEXEME_LEVEL`). Homografe oppslag av samme leksem (to oppføringer for subst. *tro*) ble regnet som flertydige, og leksemet ble talt to ganger. Nå telles flertydighet per (grunnform, ordklasse), og oppslagene slås sammen. I OBT-valideringen: riktig flest 73,4 → 74,0 %, 90-persentil 80,4 → 78,8 pp, median 13,5 → 13,7 pp.
- **Delte ankerformer fordelt etter OBT** (`decomposer.set_anchor_split(obt_anchor_split())`). Substantivet *tro* deler alle formene sine (*troen, troa, troer, troene*) med et sjeldent substantiv *troe*, og *grunn* med *ei grunne*. Paradigmet alene kan ikke skille dem. Det taggede korpuset kan: *troen* og *grunnen* er 100 % de vanlige substantivene. Sjeldne former arver fordelingen fra de andre formene med samme sett av lemmaer. En kategori der minst 95 % tilhører leksemet, kan brukes som anker i log-regresjonen. Brukes bare for ankrene, aldri for selve formen, og er ikke med i OBT-valideringen (det ville vært sirkulært).
  - «grunn» i bøker: subst. 91 % (før: adjektiv 75 %).
  - «tro» i bøker: verb 51 / subst. 38 / *trå* 11 % (før: verb 82 / *trå* 17 / subst. 0,4 %).

## 5. Resultat (bokkorpuset 1950–2020, 5-årig glidende snitt)

| Form | Leksem | 1950 | 1985 | 2020 | Endring 1950–2020 |
|---|---|---|---|---|---|
| «dør» | *en dør* | 63 % (31–88) | 61 % (28–87) | 66 % (33–89) | +3 pp (+1 til +3) |
| | *å dø* | 37 % (12–69) | 39 % (13–72) | 34 % (11–67) | −3 pp (−3 til −1) |
| «tro» | *å tro* | 45 % (17–73) | 47 % (18–74) | 55 % (23–79) | +10 pp (+3 til +11) |
| | *en tro* | 47 % (18–75) | 43 % (16–71) | 33 % (11–62) | −14 pp (−15 til −7) |
| | *å trå* (pret.) | 8 % (2–23) | 10 % (3–29) | 12 % (3–32) | +4 pp (+1 til +9) |

Parentes: 80 %-intervall. Kalibrering for hele perioden: «dør» 1,05, «tro» 0,51.

- **«dør»** er stabil: substantivet står for omtrent to tredjedeler gjennom hele perioden, med en svak økning etter 2000.
- **«tro»** endrer seg: substantivet *en tro* går tilbake og verbet *å tro* fram, særlig fra 1980-tallet. Endringen er klart større enn usikkerheten i endringen. Det passer med en sekularisering av bokspråket, men det er en tolkning, ikke noe vi har testet.
- **Nivåene** er usikre (±25–30 pp). Kontroll mot det OBT-taggede korpuset (8,4 mill. ord, andre tekster): «dør» er 52 % verb der (her 34–39 %), og «tro» er 28 % substantiv (her 33–47 %). Begge ligger innenfor båndene.

## 6. Begrensninger

- Antakelsen om stabil profil er ikke testet år for år. Endrer leksemets egen profil seg (f.eks. mer *troen* og mindre *tro* i substantivet), tolkes det som en endring i leksemandelen.
- Adjektivet *tro* har ingen ankre (ubøyelig) og får 0 %. OBT gir det 4 % av «tro».
- *å trå* bruker reglene; preteritumsformen «tro» er en sjelden variant ved siden av *trådte*, og andelen er trolig overvurdert (OBT: 8 %).
- Kalibreringen for «tro» er 0,51: anslagene dekker bare halvparten av det observerte, så normaliseringen betyr mye.

## 7. Bigrammer som uavhengig kontroll (lagt til samme dag)

NB N-gram har bigrammer (`api.nb.no/dhlab/nb_ngram`, endepunktet bak app.nb.no/ngram; `ngram.fetch_nb_ngram`). Noen kontekster peker nesten bare på én celle. Vi lærer **kontekstraten** r = andelen av en form som står etter kontekstordene, på de 120 hyppigste entydige ordene per celle, og deler bigramtallene på den: x̂ = B / r (`sqlite/bigram_kontekst.py`).

| Celle | Kontekst (ordet foran) | median r | 10.–90. persentil | sd log r |
|---|---|---|---|---|
| subst. ent ub | ubestemt artikkel og eiendomsord etter kjønn (*en/ei/et, min/mi/mitt, sin/si/sitt, din/di/ditt, vår/vårt*) + *hans, hennes, deres* | 9,9 % | 0,2–31,7 % | 1,22 |
| verb inf | *å, kan, vil, skal, må* | 56,4 % | 38,1–70,5 % | 0,21 |
| verb pres | *jeg, han, hun, vi, de, som* | 23,7 % | 13,5–33,7 % | 0,30 |

**Substantivkonteksten er ubrukelig som rate**: abstrakte ord, masseord og månedsnavn får nesten aldri *en* (0 %), konkrete tellbare ord ofte (*serie* 48 %, *følelse* 42 %). Kjønnstilpassede kontekster endrer lite (sd log 1,26 med bare hankjønns eiendomsord, 1,22 kjønnstilpasset); for intetkjønnsord blir raten riktigere (median 14 → 20 %, men bare 6 ord). Substantivets egen flertallsandel korrelerer med raten (0,72), men forklarer for lite (sd log 1,22 → 1,05). For «dør» overskyter substantivanslaget med faktor 2,6. **Verbkontekstene er stabile.** Vi anslår derfor verbet fra bigrammene og lar resten være substantivet («restmetoden»). Bigrammene gir også sikre grenser: verbet er minst B_V og høyst f(O) − B_subst.

| Form | Verbandel: paradigmet (§5) | Verbandel: bigram, restmetode | Sikre grenser (bigram) | OBT-korpuset |
|---|---|---|---|---|
| «dør» | 34–39 % (11–72) | **54 %** (37–78) | 13–81 % | 52 % |
| «tro» | 45–55 % (17–79) | **54 %** (41–70) | 30–95 % | 60 % |

- Over tid gir restmetoden «tro»: verb 39 % (1950) → 58 % (2020), samme retning som paradigmemetoden. «dør»: verb 51 → 55 %, stabilt.
- For «dør» ligger bigrammetoden nærmere det taggede korpuset enn paradigmemetoden.
- De to metodene har uavhengige feilkilder (profilen til ordet mot kontekstraten til ordet). Et vektet snitt i logit-skala (invers varians) gir for «dør» ca. 49 % verb (80 %: ca. 32–67), mot OBT 52 %. Dette er bare regnet for hånd og ikke lagt inn i koden.

**Forbehold.** Bigramtallene er fra NB N-gram, et annet bokkorpus enn `ngram_book`; uni- og bigrammer hentes derfor begge derfra. «en tro» inkluderer adjektivet (*en tro venn*), og *ei tro* kan være nektelse i eldre tekst. Kontekstraten varierer også mellom verb (sd 0,2–0,3 i log-skala), og den er antatt konstant over tid.

## 8. Paradigme, bigram eller begge? Validering mot OBT (logg del 59)

`python3 -m sqlite.kombinert` sammenligner tre anslag for verbandelen på de 150 hyppigste substantiv/verb-homografene i OBT-korpuset. Utvalget er former der ett substantiv og ett verb til sammen står for minst 90 %, og verbet er i infinitiv eller presens. Fasiten er OBTs verbandel av de to. Paradigmeanslaget kjøres her uten OBT-ankre, så valideringen ikke blir sirkulær. Resultatene per form står i `resultater/kombinert_validering.tsv`.

| metode | median avvik | 80-persentil | 90-persentil | riktig flertallsleksem |
|---|---|---|---|---|
| paradigme (bokkorpuset) | 9,7 pp | 37,4 pp | 50,9 pp | 79 % |
| bigram, restmetode (NB N-gram) | **5,0 pp** | **14,5 pp** | **24,5 pp** | **95 %** |
| kombinert (invers varians, kalibrert) | 5,4 pp | 15,4 pp | 31,5 pp | 93 % |

- *det/den* er lagt til som presenskontekst. Uten dem bommet bigrammene på *det dreier seg*, *det koster* og *den virker*. Medianen for bigrammene gikk fra 6,0 til 5,0 pp, og riktig flertallsleksem fra 93 til 95 %.
- **Usikkerheten var for smal.** Med de opprinnelige standardavvikene lå OBT-fasiten innenfor 80 %-intervallet for bare 42–46 % av formene. Det krever faktor 2,3 (paradigme) og 4,3 (bigram) på standardavviket for å nå 80 %. Noe av dette er forskjell mellom korpusene, ikke feil i metoden.
- **Kombinasjonen hjelper ikke** når usikkerheten er kalibrert. Paradigmeanslaget har tunge haler og trekker anslaget feil oftere enn det retter det.
- **Anbefaling** (`kombinert.best_estimate`): bruk bigrammene når verbet har infinitiv- eller presenskontekster, og paradigmet ellers. Usikkerheten oppgis empirisk: ±15 pp generelt og **±29 pp** for jevnt fordelte former (OBT-verbandel 20–80 %, N = 47, median avvik 12,8 pp).
- «dør»: 51 % verb (22–80). «tro»: 54 % verb (25–83). OBT gir 52 og 68 % (60 av 88; adjektiv og *trå* holdes utenfor).

Figur `tekst/figurer/dor_tro_metoder.png` viser verbandelen per år med begge metodene. For «tro» er paradigmeanslaget der kjørt med OBT-ankre (§4), og da går de to metodene sammen: verbet øker fra ca. 40–50 % til ca. 60 %. For «dør» ligger bigrammene på 45–54 %, på nivå med OBT, mens paradigmet ligger på 32–41 %.
