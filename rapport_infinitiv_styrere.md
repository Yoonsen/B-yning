# Notat: Hva står foran infinitivene? (utforskende)

*2026-11-21. `python3 -m sqlite.infinitiv_styrere` (resultater i `resultater/infinitiv_styrere.tsv`, figur `tekst/figurer/infinitiv_styrere.png`). Logg: del 61. Ikke tenkt for foredraget, men som underlag for diskusjon.*

## Spørsmål

Når infinitivandelen endrer seg, skyldes det at bestemte styringsord (*å*, modalverb) blir vanligere eller sjeldnere? Og hvilke?

## Data og metode

- De 60 hyppigste entydige verbene i Sett A, NB N-gram (bøker, bokmål), 1950–2020.
- Bigrammet «styringsord + infinitiv» for 17 styringsord: *å*; *kan, vil, skal, må, bør, får, tør*; *kunne, ville, skulle, måtte, burde, fikk, torde*; *la, lot*.
- Bare naboposisjon telles. *vil ikke gå* og *skal vi gå* havner i «ustyrt», og det gjør også imperativ der den har samme form som infinitiven (*gå!*).

## Funn

**Profil.** 65 % av infinitivforekomstene står rett etter et av styringsordene. Av disse står *å* foran 61 %, *kan* 10 %, *kunne* 6 %, *skal* 6 %, *vil* 4 %, *skulle* 4 %, *ville* 3 %, *må* 3 % og *måtte* 2 %. *bør, burde, får, fikk* utgjør under 1 % hver. *la/lot* og *tør/torde* står nesten aldri rett foran infinitiven, fordi det normalt kommer et pronomen imellom (*la ham gå*).

**Infinitivandelen går opp og så ned:** 33 % (1950-tallet) → 37 % (1990-tallet) → 34 % (2010-tallet) av inf + pres + pret.

Bidrag til infinitivandelen, per 100 verbformer:

| | 1950-t. | 1990-t. | 2010-t. | 1950→1990 | 1990→2010 |
|---|---|---|---|---|---|
| *å* | 11,2 | 14,4 | 14,2 | **+3,3** | −0,3 |
| *kan* | 1,5 | 2,7 | 2,3 | +1,2 | −0,5 |
| *skal* | 0,9 | 1,4 | 1,2 | +0,5 | −0,2 |
| *vil* | 0,8 | 1,2 | 0,8 | +0,4 | −0,4 |
| *kunne* | 1,3 | 1,5 | 1,3 | +0,1 | −0,2 |
| *skulle* | 0,9 | 0,7 | 0,9 | −0,2 | +0,2 |
| *ville* | 0,9 | 0,6 | 0,7 | −0,3 | +0,1 |
| *måtte* | 0,5 | 0,4 | 0,5 | −0,1 | +0,1 |
| ustyrt (ikke rett etter styringsord) | 14,3 | 12,9 | 11,0 | −1,4 | **−1,9** |
| **infinitiv i alt** | 33,2 | 36,9 | 33,9 | +3,7 | −3,0 |

- **Økningen fram til 1990** kommer nesten bare fra *å* (+3,3) og modalene i presens (*kan, skal, vil*: +2,1). Det passer med mer *for å*- og *å*-konstruksjoner (nominal, utredende stil) og mer generisk presens.
- **Nedgangen etter 1990** kommer fra de ustyrte infinitivene (−1,9) og modalene i presens (−1,0). *å* holder seg.
- **Modalene i preteritum** (*skulle, ville, måtte*) går litt ned fram til 1990 og litt opp igjen, i takt med preteritum generelt. De forsvinner ikke.
- Svaret på spørsmålet er altså: ja, delvis. Det er modalene i presens som går ned etter 1990, ikke de i preteritum. Den største enkeltposten er likevel de ustyrte infinitivene.

## Forbehold og ideer

- «Ustyrt» blander tre ting: avstand mellom modal og infinitiv (*vil ikke gå*), imperativ med samme form (*gå!*, *ta!*) og ekte ustyrte infinitiver. Trigrammer (*vil ikke X*, *skal vi X*) og verb med egen imperativform kan skille dem.
- Tallene er for 60 høyfrekvente verb og kan ikke uten videre overføres til hele verbforrådet.
- En mulig neste analyse er å se profilen per verb: hvilke verb står mest etter *å* (formål, *for å*) og hvilke etter modaler. Det kan henge sammen med verbtypene 1A/1B (`rapport_verbtyper.md`).
