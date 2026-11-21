# Leksikalske bøyningsprofiler: ordboksdata og historiske n-gram

*(Abstract til MONS-konferansen, slutten av november. Revidert 2026-11-21 slik at eksemplene stemmer med dataene; den innsendte versjonen står nederst.)*

Hvordan fordeler bruken av et leksem seg mellom bøyningsformene, og hvor stabile er disse proporsjonene over tid? Vi undersøker dette ved å kombinere ordboksdata om bøyningsparadigmer fra Norsk Ordbank med historiske n-gramdata fra Nasjonalbibliotekets bokkorpus (1950–2020). Målet er å kartlegge leksikalske forskjeller i bøyningsformenes relative frekvens og undersøke hvordan slike mønstre kan brukes til å estimere leksemfordelingen bak flertydige ordformer.

For verb ser vi på fordelingen mellom infinitiv, presens og preteritum. Leksemene har tydelig ulike favorittformer: infinitiven «vurdere» står for 70 % av bruken, presensformen «vet» for 55 % og preteritumsformen «forsvant» for 54 %. For substantiv ser vi på bestemthet og tall: ubestemt entall dominerer for «tid», bestemt entall for «sommeren» og ubestemt flertall for «epler». Forskjellene er stabile. Alle disse seks leksemene har samme form på topp i alle 71 årene, og det samme gjelder omtrent halvparten av alle entydige verb og substantiv vi har undersøkt. Dette åpner for å beskrive leksemer gjennom kvantitative bøyningsprofiler og undersøke hvor sterkt fordelingen mellom grammatiske kategorier avhenger av leksikalsk identitet.

Metodisk kobler vi ordbøkenes paradigmer til frekvenskurver for de enkelte ordformene og beregner formenes relative andeler over tid. Her er skillet mellom observert ordform og leksem avgjørende: N-gramdataene teller former, mens én form kan tilhøre flere leksemer og bøyningskategorier. «Fisker» kan være presens av verbet «fiske», ubestemt entall av substantivet «fisker» eller ubestemt flertall av substantivet «fisk». Frekvenskurven for «fisker» summerer disse bidragene uten å skille dem fra hverandre. Entydige former, som kan knyttes til ett leksem og én bøyningskategori, gir derimot direkte observerbare holdepunkter. Vi bruker slike holdepunkter, sammen med bøyningsprofiler lært på entydige leksemer, til å estimere hvordan frekvensen av flertydige former fordeler seg mellom leksemene. I en test med kunstige homografer finner metoden riktig hovedleksem i omtrent fire av fem tilfeller.

Ambisjonen er dermed todelt: å beskrive samspillet mellom leksikon og bøyning i faktisk språkbruk, og å utvikle et empirisk grunnlag for å fordele aggregerte frekvenser mellom mulige leksemer. Slik kan bøyningsprofiler både belyse grammatiske bruksmønstre og gi mer presise tolkninger av historiske frekvenskurver.

---

## Endringer fra den innsendte versjonen (2026-11-21)

| Innsendt | Dataene (bokkorpuset 1950–2020) | Revidert |
| :--- | :--- | :--- |
| «gikk» dominerer over «gå» og «går» | gikk 38 / går 34 / gå 28 %; samme form på topp bare 70 % av årene, og «går» inkluderer *i går* | erstattet med «forsvant» (54 %, topp alle 71 år) |
| infinitiven «vite» dominerer | vet 55 / visste 26 / vite 19 % | presensformen «vet» dominerer |
| infinitiv-eksempel | — | «vurdere» (inf. 70 %, topp alle 71 år) |
| «eple» dominerer over «eplet» og «epler» | epler 45 / eple 30 / eplet 11 % | ubestemt flertall «epler» dominerer |
| «bussen» dominerer | stemmer (42 %), men alle formene kolliderer med *busse* i Ordbanken | erstattet med «sommeren» (69 %, entydig, topp alle 71 år) |
| ubestemt entall-eksempel | — | «tid» (63 %, topp alle 71 år) |
| «stabile over flere år» | samme toppform alle 71 år for 46 % av Sett A-verbene og 53 % av substantivene | konkretisert |

Kilder: `rapport_verbtyper.md` §4, `rapport_substantivtyper.md` §3–5, `rapport_dekomponering_validering.md` §3.

## Innsendt versjon

Hvordan fordeler bruken av et leksem seg mellom bøyningsformene, og hvor stabile er disse proporsjonene over tid? Vi undersøker dette ved å kombinere ordboksdata om bøyningsparadigmer med historiske n-gramdata fra Nasjonalbiblioteket. Målet er å kartlegge leksikalske forskjeller i bøyningsformenes relative frekvens og undersøke hvordan slike mønstre kan brukes til å estimere leksemfordelingen bak flertydige ordformer.

For verb undersøker vi om ulike leksemer har karakteristiske fordelinger mellom infinitiv og tempusformer. Foreløpige observasjoner viser eksempelvis at preteritumsformen «gikk» dominerer over «gå» og «går», mens infinitiven «vite» dominerer over «vet» og «visste». For substantiv undersøker vi tilsvarende forhold mellom bestemthet og tall: Blant formene «eple», «eplet» og «epler» er ubestemt entall mest frekvent, mens bestemt entall dominerer blant «buss», «bussen» og «busser». Observasjonene tyder på at slike forskjeller holder seg stabile over flere år. Dette åpner for å beskrive leksemer gjennom kvantitative bøyningsprofiler og undersøke hvor sterkt fordelingen mellom grammatiske kategorier avhenger av leksikalsk identitet.

Metodisk kobler vi ordbøkenes paradigmer til frekvenskurver for de enkelte ordformene og beregner formenes relative andeler over tid. Her er skillet mellom observert ordform og leksem avgjørende: N-gramdataene teller former, mens én form kan tilhøre flere leksemer og bøyningskategorier. «Fisker» kan være presens av verbet «fiske», ubestemt entall av substantivet «fisker» eller ubestemt flertall av substantivet «fisk». Frekvenskurven for «fisker» summerer disse bidragene uten å skille dem fra hverandre. Entydige former, som kan knyttes til ett leksem og én bøyningskategori, gir derimot direkte observerbare holdepunkter for bøyningsprofilene. Vi undersøker om slike holdepunkter, sammen med stabile proporsjoner i paradigmene, kan brukes til å estimere hvordan frekvensen av flertydige former fordeler seg mellom leksemene.

Ambisjonen er dermed todelt: å beskrive samspillet mellom leksikon og bøyning i faktisk språkbruk, og å utvikle et empirisk grunnlag for å fordele aggregerte frekvenser mellom mulige leksemer. Slik kan bøyningsprofiler både belyse grammatiske bruksmønstre og gi mer presise tolkninger av historiske frekvenskurver.
