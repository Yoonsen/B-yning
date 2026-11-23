// Arbeidsdeck til møtet 23.11.2026: det som er nytt siden fredag (logg del 47–62).
// Bygges ved siden av hoveddecket; tema, layouter og hjelpefunksjoner er kopiert fra build_deck.js.
//   NODE_PATH=<sti til node_modules> node tekst/deck/build_tillegg.js
// Krever pptxgenjs (MIT-lisens).

const path = require("path");
const pptxgen = require("pptxgenjs");

const OUT = path.join(__dirname, "..", "mons_nytt_siden_fredag.pptx");
const APPLY_THEME = process.env.APPLY_THEME_JS; // valgfri: sti til apply_theme.js fra pptx-skillen

const THEME = {
  name: "MONS Bøyning",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "22223B", // blekk
    lt1: "FFFFFF",
    dk2: "4A4E69", // grå-indigo for brødtekst
    lt2: "EEF0F3", // lys flate for kort
    accent1: "B5482F", // rust (bokrygg)
    accent2: "4F7C7A", // grønngrå
    accent3: "E9C46A", // sand: kun for «mangler»-markering
    accent4: "9A8C98",
    accent5: "C9ADA7",
    accent6: "2A9D8F",
    hlink: "B5482F",
    folHlink: "4A4E69",
  },
};
const HEX = THEME.colors;
// Formfarger i figurene (sqlite/figurer.py); validert som kategorisk palett.
const FORM = { inf: "B5482F", pres: "3D5A98", pret: "2A9D8F" };
const FIG = (f) => path.join(__dirname, "..", "figurer", f);

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.title = "Nytt siden fredag";
pres.author = "MONS-prosjektet, Nasjonalbiblioteket";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

const W = 13.333;
const MX = 0.6; // marg

// ---------- Layouts ----------
pres.defineSlideMaster({
  title: "TITTEL",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 2.2, w: W - 2 * MX, h: 1.6, fontSize: 44, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: MX, y: 4.0, w: W - 2 * MX, h: 1.4, fontSize: 20, color: C.background2, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});

pres.defineSlideMaster({
  title: "INNHOLD",
  background: { color: C.background1 },
  margin: [0.5, MX, 0.6, MX],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.4, w: W - 2 * MX - 1.8, h: 0.9, fontSize: 32, bold: true, color: C.text1, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "MONS 2026 · Leksikalske bøyningsprofiler", options: { x: MX, y: 7.0, w: 6, h: 0.3, fontSize: 10, color: C.text2, margin: 0 } } },
  ],
  slideNumber: { x: W - MX - 0.6, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: C.text2, align: "right" },
});

// ---------- Hjelpere ----------
// Motiv: ordformer i «brikker» (avrundede rektangler).
function chip(slide, text, x, y, opts = {}) {
  const w = opts.w || Math.max(0.9, 0.13 * text.length + 0.45);
  const h = opts.h || 0.55;
  slide.addText(text, {
    shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.12,
    x, y, w, h, fontSize: opts.fontSize || 18, bold: !!opts.bold, italic: opts.italic !== false,
    align: "center", valign: "middle", margin: 0,
    color: opts.color || C.text1, fill: { color: opts.fill || C.background2 },
    line: opts.line ? { color: opts.line, width: 1.25 } : undefined,
    objectName: opts.name || `chip ${text}`,
  });
  return w;
}

function chipRow(slide, forms, x, y, opts = {}) {
  let cx = x;
  forms.forEach((f, i) => {
    const first = i === 0;
    cx += chip(slide, f, cx, y, { fill: first ? C.accent1 : C.background2, color: first ? C.background1 : C.text1, bold: first, ...opts }) + 0.12;
    if (i < forms.length - 1) {
      slide.addText(">", { x: cx, y, w: 0.3, h: 0.55, fontSize: 18, color: C.text2, align: "center", valign: "middle", margin: 0, isTextBox: true });
      cx += 0.42;
    }
  });
}

// Sand-farget markering for innhold som ikke finnes ennå.
function missing(slide, label, x, y, w, h) {
  slide.addText(
    [
      { text: "MANGLER", options: { bold: true, fontSize: 14, breakLine: true, color: C.text1 } },
      { text: label, options: { fontSize: 14, color: C.text1 } },
    ],
    { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.1, x, y, w, h, fill: { color: C.accent3, transparency: 55 }, line: { color: C.accent3, width: 1.5, dashType: "dash" }, align: "center", valign: "middle", margin: 0.2, objectName: "mangler-markering" }
  );
}

function status(slide, label) {
  const draft = label === "UTKAST";
  slide.addText(label, {
    shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.1,
    x: W - MX - 1.6, y: 0.6, w: 1.6, h: 0.45, fontSize: 12, bold: true, align: "center", valign: "middle", margin: 0,
    color: C.text1, fill: { color: draft ? C.background2 : C.accent3 }, objectName: "status",
  });
}

function stat(slide, big, small, x, y, w, color) {
  slide.addText(big, { x, y, w, h: 1.0, fontSize: 54, bold: true, fontFace: THEME.headFontFace, color: color || C.accent1, margin: 0, valign: "bottom", isTextBox: true, objectName: `stat ${big}` });
  slide.addText(small, { x, y: y + 1.05, w, h: 0.8, fontSize: 14, color: C.text2, margin: 0, valign: "top", isTextBox: true });
}

function body(slide, runs, x, y, w, h, fontSize = 16) {
  slide.addText(runs, { x, y, w, h, fontSize, color: C.text2, valign: "top", margin: 0, paraSpaceAfter: 6, isTextBox: true });
}

function bullets(items) {
  return items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } }));
}

const chartText = {
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", titleFontFace: "+mn-lt", legendFontFace: "+mn-lt",
  catAxisLabelColor: HEX.dk2, valAxisLabelColor: HEX.dk2, dataLabelColor: HEX.dk1, titleColor: HEX.dk1,
  catAxisLabelFontSize: 12, valAxisLabelFontSize: 11, dataLabelFontSize: 12, titleFontSize: 14, legendFontSize: 12,
};
function chartOpts(extra) {
  return {
    ...chartText,
    valGridLine: { color: HEX.lt2, size: 1 }, catGridLine: { style: "none" },
    valAxisLabelFormatCode: "0\"%\"", dataLabelFormatCode: "0.0\"%\"",
    showValue: true, dataLabelPosition: "outEnd",
    ...extra,
  };
}

// ---------- Seksjoner og lysbilder ----------


const FOOT = (s, t) => s.addNotes(t);

// 1 Tittel
pres.addSection({ title: "Innledning" });
let s = pres.addSlide({ masterName: "TITTEL", sectionTitle: "Innledning" });
s.addText("Nytt siden fredag", { placeholder: "title" });
s.addText("Dekomponering med kontekst, over tid og i subspråk · arbeidsnotat til møtet 23.11.", { placeholder: "body" });
FOOT(s, "Arbeidsdeck, ikke for MONS. Samler det som er gjort 20.–22.11. (logg del 47–62). Rapporter: rapport_dekomponering_tid.md, rapport_dekomponering_obt.md §9–10, rapport_infinitiv_styrere.md, rapport_verbtyper.md §7.1–7.2.");

// 2 Formelen
pres.addSection({ title: "Metode" });
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Metode" });
s.addText("Én formel bak alle anslagene", { placeholder: "title" });
chip(s, "f(O) = x₁ + x₂", MX, 1.6, { w: 3.6, h: 0.8, fontSize: 24, italic: false, bold: true, fill: C.accent1, color: C.background1 });
chip(s, "xᵢ = ρᵢ · Rᵢ", MX + 4.0, 1.6, { w: 3.0, h: 0.8, fontSize: 24, italic: false, bold: true });
body(s, bullets([
  "f(O): observert frekvens for den flertydige formen O",
  "Rᵢ: det vi ser av leksem i ellers. Enten resten av paradigmet (døren, dører …) eller kontekstene (å tro, kan tro …)",
  "ρᵢ: typisk forhold mellom formen og Rᵢ, lært på entydige ord",
  "Kalibrering: Σ x̂ᵢ / f(O) nær 1 betyr at modellen stemmer med det observerte",
]), MX, 2.8, 7.2, 3.4, 17);
stat(s, "±15 pp", "typisk usikkerhet for en enkelt form (80 %-intervall); ±29 pp når leksemene er omtrent like vanlige", 8.6, 1.6, 4.1);
stat(s, "≈ 0", "usikkerheten i endringen over tid: profilfeilen er den samme hvert år", 8.6, 4.0, 4.1, C.accent2);
FOOT(s, "rapport_dekomponering_tid.md §2–3. Over tid antas stabil profil: xᵢ(t) = (x̂ᵢ/Rᵢ) · Rᵢ(t). Nivået er usikkert, endringen langt sikrere. Harde grenser (60 %-regelen) ble vurdert, men en celle kan ha opptil 90 % (P99), så usikkerheten er i stedet modellert som spredning i ρ.");

// 3 døde
pres.addSection({ title: "Dekomponereren" });
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Dekomponereren" });
s.addText("«døde»: adjektivet er 28 %, og dø er fortsatt 2A", { placeholder: "title" });
s.addChart(pres.charts.BAR, [
  { name: "inf", labels: ["Uten korreksjon", "28 % adjektiv (OBT)", "46 % adjektiv (høyeste overslag)"], values: [17.4, 21.9, 26.3] },
  { name: "pres", labels: ["Uten korreksjon", "28 % adjektiv (OBT)", "46 % adjektiv (høyeste overslag)"], values: [8.7, 10.9, 13.1] },
  { name: "pret", labels: ["Uten korreksjon", "28 % adjektiv (OBT)", "46 % adjektiv (høyeste overslag)"], values: [74.0, 67.2, 60.5] },
], chartOpts({ x: MX, y: 1.45, w: 7.6, h: 4.9, barDir: "col", barGrouping: "clustered", chartColors: [FORM.inf, FORM.pres, FORM.pret], showLegend: true, legendPos: "b", showTitle: true, title: "Profilen til dø i bokkorpuset (%)", valAxisMaxVal: 90, valAxisHidden: true, valGridLine: { style: "none" } }));
stat(s, "28 %", "av «døde» er adjektivet død i det taggede korpuset (dekomponereren: 29 %)", 8.6, 1.5, 4.1);
stat(s, "< 77 %", "så lenge adjektivet er under dette, står pret > inf > pres (2A)", 8.6, 3.75, 4.1, C.accent2);
FOOT(s, "rapport_verbtyper.md §7.2 punkt 5; rapport_dekomponering_obt.md §9. Paradigmeankrene alene kan ikke bestemme adjektivandelen (dødd, dødt og dødene er atypisk sjeldne; sum anslag / obs. 0,05). Adjektivankre (sqlite/adjektiv_gold.py) ga dekomponereren 71/29 i OBT-korpuset mot fasit 72/28.");

// 4 OBT-validering
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Dekomponereren" });
s.addText("Dekomponereren mot tagget korpus: fire forbedringer", { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "Median avvik", labels: ["Før (20.11.)", "+ adjektivankre", "+ homografvekting", "+ leksemnivå"], values: [18.4, 13.9, 13.5, 13.7] }],
  chartOpts({ x: MX, y: 1.45, w: 7.4, h: 4.6, barDir: "bar", catAxisOrientation: "maxMin", chartColors: [HEX.accent1], showLegend: false, showTitle: true, title: "Median avvik fra OBT, 1 721 innholdsordformer (prosentpoeng)", valAxisHidden: true, valGridLine: { style: "none" }, valAxisMaxVal: 22, dataLabelFormatCode: "0.0" }));
stat(s, "69 → 74 %", "riktig leksem får størst andel", 8.5, 1.5, 4.2);
body(s, bullets(["«døde»: fra 28 til 1 pp avvik", "Sjeldne ordbokshomografer (ei grunne, troe) vektes ned etter entydig bruk", "grunn og bein løses bare med OBT som kilde for delte former"]), 8.5, 3.6, 4.2, 2.6, 15);
FOOT(s, "rapport_dekomponering_obt.md §9–10 og rapport_dekomponering_tid.md §4. Leksemnivå: homografe oppslag av samme leksem regnes sammen (median 13,7 pp, men 90-persentil 78,8 mot 80,4 og riktig flest 74,0 %). OBT-fordelte ankre er ikke med i valideringen (sirkulært).");

// 5 Kontekstrater
pres.addSection({ title: "Bigrammer" });
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Bigrammer" });
s.addText("Kontekst skiller verb fra substantiv, men bare fra verbsiden", { placeholder: "title" });
const hdr = { bold: true, color: HEX.lt1, fill: { color: HEX.dk1 } };
s.addTable([
  [{ text: "Celle", options: hdr }, { text: "Kontekst (ordet foran)", options: hdr }, { text: "Median andel", options: hdr }, { text: "Spenn mellom ord", options: hdr }],
  ["Infinitiv", "å, kan, vil, skal, må", "56 %", "38–70 %"],
  ["Presens", "jeg, han, hun, vi, de, som, det, den", "24 %", "14–34 %"],
  ["Subst. ent ub", "en/ei/et, min/mi/mitt … , hans, hennes, deres", "10 %", "0–32 %"],
], { x: MX, y: 1.6, w: 12.1, colW: [2.2, 5.3, 2.2, 2.4], fontSize: 16, color: HEX.dk1, border: { type: "solid", color: HEX.lt2, pt: 1 }, rowH: 0.6 });
body(s, bullets([
  "Verbkontekstene er stabile: verbet = bigramtall / rate, substantivet er resten",
  "Substantivkonteksten varierer med betydningen: månedsnavn og masseord 0 %, serie og følelse 40–48 %. Kjønnstilpasning hjelper lite",
  "Kilde: NB N-gram (api.nb.no/dhlab/nb_ngram), som gir uni-, bi- og trigrammer",
]), MX, 4.3, 12.1, 2.2, 16);
FOOT(s, "sqlite/bigram_kontekst.py; rapport_dekomponering_tid.md §7. Ratene er lært på 120 entydige ord per celle. Flertallsandelen korrelerer med substantivraten (0,72), men forklarer for lite (sd log 1,22 → 1,05).");

// 6 Validering bigram
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Bigrammer" });
s.addText("Bigrammer treffer best: 5 pp median mot tagget korpus", { placeholder: "title" });
s.addChart(pres.charts.BAR, [
  { name: "Median", labels: ["Paradigme", "Bigram", "Kombinert"], values: [9.7, 5.0, 5.4] },
  { name: "80-persentil", labels: ["Paradigme", "Bigram", "Kombinert"], values: [37.4, 14.5, 15.4] },
], chartOpts({ x: MX, y: 1.45, w: 7.4, h: 4.8, barDir: "col", barGrouping: "clustered", chartColors: [HEX.accent1, "C9CCD3"], showLegend: true, legendPos: "b", showTitle: true, title: "Avvik i verbandel fra OBT, 150 substantiv/verb-homografer (pp)", valAxisHidden: true, valGridLine: { style: "none" }, valAxisMaxVal: 45, dataLabelFormatCode: "0.0" }));
stat(s, "95 %", "riktig flertallsleksem med bigrammer (paradigme 79 %)", 8.5, 1.5, 4.2);
body(s, bullets(["Kombinasjonen hjelper ikke når usikkerheten er kalibrert", "Anbefaling: bigram der verbet har kontekster, ellers paradigme", "«dør» 51 % verb (OBT 52), «tro» 54 % (OBT 68)"]), 8.5, 3.6, 4.2, 2.6, 15);
FOOT(s, "python3 -m sqlite.kombinert; resultater/kombinert_validering.tsv; rapport_dekomponering_tid.md §8. Med de opprinnelige usikkerhetene lå fasiten innenfor 80 %-intervallet bare for 42–46 % av formene; faktor 2,3 (paradigme) og 4,3 (bigram) trengs, tilpasset på de samme formene. Fasiten er fra et annet korpus.");

// 7 dør/tro
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Bigrammer" });
s.addText("«dør» og «tro» over tid", { placeholder: "title" });
s.addImage({ path: FIG("dor_tro_metoder.png"), x: MX, y: 1.3, w: 11.4, h: 4.71, altText: "Verbandel av dør og tro per år 1950–2020, bigram og paradigme, med det taggede korpuset som kontroll" });
body(s, [{ text: "«tro» blir mer verb (ca. 40 → 60 %), med begge metodene; «dør» er stabil rundt 50 % verb.", options: { bold: true, color: C.text1 } }], MX, 6.15, 12.1, 0.6, 16);
FOOT(s, "Samme figur som lysbilde 13 i hoveddecket. Brukstilfellet: ordbokbrukeren vil se kurven for leksemet, ikke for overflateformen.");

// 8 Infinitivstyrere
pres.addSection({ title: "Utforskende" });
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Utforskende" });
s.addText("Hva står foran infinitivene?", { placeholder: "title" });
s.addImage({ path: FIG("infinitiv_styrere.png"), x: MX, y: 1.3, w: 11.6, h: 4.62, altText: "Infinitiver rett etter å, modal i presens og modal i preteritum per 100 infinitiver per tiår, og infinitivandelen per tiår" });
body(s, [{ text: "Økning til 1990: å og modalene i presens. Nedgang etter 1990: modalene i presens og infinitiver uten styringsord rett foran. ", options: { bold: true, color: C.text1 } }, { text: "Modalene i preteritum endrer seg lite.", options: {} }], MX, 6.05, 12.1, 0.7, 15);
FOOT(s, "rapport_infinitiv_styrere.md. 60 hyppige entydige verb, NB N-gram. 65 % av infinitivene står rett etter et styringsord; å står for 61 % av disse. «Ustyrt» blander avstand (vil ikke gå), imperativ med samme form og ekte ustyrte; trigrammer kan skille dem.");

// 9 Frukt
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Utforskende" });
s.addText("Frukt: telling eller masse?", { placeholder: "title" });
const fr = ["drue", "potet", "nøtt", "tomat", "eple", "banan", "appelsin", "gulrot", "sitron", "fersken", "løk"];
s.addChart(pres.charts.BAR, [
  { name: "ent ub", labels: fr, values: [11, 12, 17, 30, 30, 34, 40, 43, 77, 78, 76] },
  { name: "fl ub", labels: fr, values: [61, 72, 64, 53, 45, 51, 45, 45, 14, 15, 1] },
], chartOpts({ x: MX, y: 1.45, w: 8.2, h: 4.9, barDir: "col", barGrouping: "clustered", chartColors: [FORM.pres, FORM.inf], showLegend: true, legendPos: "b", showTitle: true, title: "Andel av alle fire formene, bokkorpuset 1950–2020 (%)", valAxisHidden: true, valGridLine: { style: "none" }, valAxisMaxVal: 90, dataLabelFormatCode: "0", dataLabelFontSize: 10 }));
body(s, bullets(["Telling: druer, poteter, nøtter, epler: flertall alle år", "Smak/ingrediens: sitron, fersken, løk: masseord i entall", "På vei: banan (krysser 2013), appelsin, gulrot (2000–2008)"]), 9.1, 1.6, 3.7, 4.6, 15);
FOOT(s, "Rask beregning 21.11. (ikke lagret som skript). pære og bær er utelatt (flertydige former). Hypotese: oppskriftsspråket (moset banan, revet gulrot) gjør tellbare frukter til masseord.");

// 10 Matbøker
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Utforskende" });
s.addText("Matbøker: et subspråk med egen profil", { placeholder: "title" });
s.addImage({ path: FIG("matboker_eple_ppm.png"), x: MX, y: 1.35, w: 5.7, h: 2.63, altText: "eple, eplet, epler, eplene per million ord i matbøker 1950–2025" });
s.addImage({ path: FIG("matboker_eple_burstiness.png"), x: MX, y: 4.1, w: 5.7, h: 2.63, altText: "Forekomster per bok med ordet (burstiness) for eple-formene i matbøker 1950–2025" });
body(s, bullets([
  "Ca. 5 500 matbøker; epler i 63 %, eple i 59 %",
  "1950–60: epler/eplene dominerer, 40–70 per bok. Bøker om epler (sylting, frukthage)",
  "Etter 2000: alle former 5–8 per bok. eple krysser epler ca. 2013 gjennom spredning, ikke intensitet",
  "ppm ∝ andel bøker med formen × burstiness",
  "Endring = innenfor subspråket + sammensetning (shift-share; jf. Harris)",
]), 6.9, 1.45, 5.9, 5.2, 15);
FOOT(s, "Figurer fra Lars' korpusverktøy (matbokkorpus, ppm og forekomster per bok med ordet). Sjekk: bindestrekformer (eple- og pæremos) og antall bøker per år i begynnelsen og slutten av perioden.");

// 11 Koselleck
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Utforskende" });
s.addText("Bestemt entall som felles bakgrunn", { placeholder: "title" });
s.addText("Nøkkelbegreper", { x: MX, y: 1.55, w: 2.4, h: 0.55, fontSize: 15, bold: true, color: C.text2, margin: 0, valign: "middle", isTextBox: true });
s.addText("Hverdagsting", { x: MX, y: 2.35, w: 2.4, h: 0.55, fontSize: 15, bold: true, color: C.text2, margin: 0, valign: "middle", isTextBox: true });
let cx = MX + 2.5;
for (const w of ["staten", "folket", "markedet"]) cx += chip(s, w, cx, 1.55) + 0.2;
cx = MX + 2.5;
for (const w of ["ammen", "kakkelovnen", "budeia"]) cx += chip(s, w, cx, 2.35) + 0.2;
body(s, bullets([
  "Bestemt form forutsetter at leseren vet hvilken referent det er snakk om",
  "Nøkkelbegreper (Koselleck) og hverdagsting har høy andel bestemt entall i sin tid",
  "Når tingen forsvinner, blir ordet ubestemt eller forklart: «en amme, det vil si …»",
  "Test: rangér substantiv etter endring i andel ent be fra 1800-tallet til i dag, og kontroller for sjanger og spredning",
]), MX, 3.5, 12.1, 3.0, 17);
FOOT(s, "Idé fra samtalen 22.11. Henger sammen med funnet i rapport_substantivtyper.md: ent be på topp for unike eller situasjonsgitte referenter (regjering, staten, sommeren, gården).");

// 12 Til møtet
pres.addSection({ title: "Møtet" });
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Møtet" });
s.addText("Til møtet", { placeholder: "title" });
body(s, [{ text: "Tagging (Marie)", options: { bold: true, color: C.text1, breakLine: true } }, ...bullets([
  "Hele det utvidede korpuset (lag 1–5, 1 097 dok.) tagges; LFS-databasen beholder bare lag 1",
  "Kjøre OBT-validering og kombinert validering på nytt med flere lag",
  "OBT-kvalitet: tro som trå (8 %), å som interjeksjon, adj./verb i «døde» og «stille»",
])], MX, 1.5, 6.0, 4.8, 16);
body(s, [{ text: "Foredraget (torsdag)", options: { bold: true, color: C.text1, breakLine: true } }, ...bullets([
  "UTKAST: lysbilde 11 (dør), 12 (fisker), 13 (dør/tro), 15 (Hva er nytt?)",
  "Skal bigrammene inn i hoveddecket, eller bare nevnes?",
  "Subspråk og shift-share: forbehold om stabiliteten i hele korpuset",
])], 6.9, 1.5, 5.9, 4.8, 16);
FOOT(s, "Logg del 62 (Marie): taggingen kjøres med lav prioritet over helgen; den store databasen deles utenfor repoet med eksporter --til.");

(async () => {
  await pres.writeFile({ fileName: OUT });
  if (APPLY_THEME) {
    const { applyTheme } = require(APPLY_THEME);
    await applyTheme(OUT, THEME);
  }
  console.log("Skrev", OUT);
})();
