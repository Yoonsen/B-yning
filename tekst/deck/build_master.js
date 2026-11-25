// GJELDENDE MONS-PRESENTASJON (master): tekst/mons_master.pptx
//
// Laget 2026-11-23 (logg del 68) ved å slå sammen
//   - build_deck.js   (hoveddecket, tekst/mons_presentasjon.pptx, sist endret 2026-11-21)
//   - build_tillegg.js (arbeidsdecket «Nytt siden fredag», 2026-11-23): formelen, «døde»,
//     kontekstrater og bigramvalideringen
//   - to nye lysbilder om det utvidede OBT-korpuset (rapport_dekomponering_obt.md §11,
//     rapport_stabilitet_obt.md)
// Videre endringer gjøres HER. build_deck.js og build_tillegg.js er historikk og skal ikke
// lenger oppdateres. Se tekst/deck/HANDOVER_master.md.
//
// Krever pptxgenjs 3.12.0 (MIT-lisens), installert et sted utenfor repoet, og kjøres med
//   NODE_PATH=<sti til node_modules> node tekst/deck/build_master.js
// Valgfritt: APPLY_THEME_JS=<sti til apply_theme.js fra pptx-skillen> skriver temafargene inn.
//
// Lysbilder/felt markert «MANGLER», «MERK» eller «UTKAST» er ikke ferdige.

const path = require("path");
const pptxgen = require("pptxgenjs");

const OUT = path.join(__dirname, "..", "mons_master.pptx");
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
pres.title = "Leksikalske bøyningsprofiler";
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

// Sand-farget merknad: innhold som er motsagt eller må sjekkes (samme stil som «MANGLER»).
function note(slide, label, x, y, w, h) {
  slide.addText(
    [
      { text: "MERK", options: { bold: true, fontSize: 14, breakLine: true, color: C.text1 } },
      { text: label, options: { fontSize: 14, color: C.text1 } },
    ],
    { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.1, x, y, w, h, fill: { color: C.accent3, transparency: 55 }, line: { color: C.accent3, width: 1.5, dashType: "dash" }, align: "left", valign: "middle", margin: 0.15, objectName: "merk-markering" }
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

// 1 Tittel
pres.addSection({ title: "Innledning" });
let s = pres.addSlide({ masterName: "TITTEL", sectionTitle: "Innledning" });
s.addText("Leksikalske bøyningsprofiler", { placeholder: "title" });
s.addText("Ordboksdata og historiske n-gram\n[Navn på foredragsholdere] · Nasjonalbiblioteket · MONS 2026", { placeholder: "body" });
chip(s, "gikk", MX, 1.2, { fill: C.accent1, color: C.background1, bold: true });
chip(s, "vet", MX + 1.25, 1.2, { fill: C.text2, color: C.background1 });
chip(s, "bussen", MX + 2.5, 1.2, { fill: C.text2, color: C.background1 });
chip(s, "eple", MX + 4.05, 1.2, { fill: C.text2, color: C.background1 });
s.addNotes("Fyll inn navn på foredragsholdere. Brikkene viser den dominerende formen i hvert av eksemplene fra abstractet.");

// 2 Spørsmålet
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Innledning" });
s.addText("Hvert leksem har sin favorittform", { placeholder: "title" });
const CH2 = { w: 2.05, fontSize: 15 }; // lik bredde, så radene får plass ved siden av teksten
s.addText("Verb: inf / pres / pret", { x: MX, y: 1.35, w: 6, h: 0.45, fontSize: 20, bold: true, color: C.text1, margin: 0, isTextBox: true });
chipRow(s, ["vurdere 70 %", "vurderer 21 %", "vurderte 9 %"], MX, 1.85, CH2);
chipRow(s, ["vet 55 %", "visste 26 %", "vite 19 %"], MX, 2.5, CH2);
chipRow(s, ["forsvant 54 %", "forsvinner 29 %", "forsvinne 18 %"], MX, 3.15, CH2);
s.addText("Substantiv: andel av alle fire former", { x: MX, y: 4.0, w: 6.5, h: 0.45, fontSize: 20, bold: true, color: C.text1, margin: 0, isTextBox: true });
chipRow(s, ["tid 63 %", "tiden/tida 30 %", "tider 6 %"], MX, 4.5, CH2);
chipRow(s, ["sommeren 69 %", "sommer 26 %", "somre 3 %"], MX, 5.15, CH2);
chipRow(s, ["epler 45 %", "eple 30 %", "eplet 11 %"], MX, 5.8, CH2);
body(s, [{ text: "Spørsmål: Hvor mye av fordelingen skyldes leksemet selv — og er den stabil over tid?", options: { bold: true, color: C.text1 } }], 8.5, 1.85, 4.2, 1.6, 20);
body(s, [{ text: "Alle seks har samme form på topp i alle 71 år (bokkorpuset 1950–2020).", options: {} }], 8.5, 3.6, 4.2, 0.9, 16);
s.addNotes("Tall fra bokkorpuset 1950–2020: verb fra rapport_verbtyper.md §4, substantiv fra resultater/substantivtyper.tsv (rapport_substantivtyper.md §3–5). For substantiv vises ent ub, ent be og fl ub; bestemt flertall er utelatt (for eple er epla/eplene 14 %, mer enn eplet). vurdere, forsvinne, tid og sommer er helt entydige i Ordbanken. vite og eple er også rene i kjerneformene (sideformen veit = ei veit). Abstractet er samkjørt 2026-11-21: den innsendte versjonen hadde gikk, infinitiv vite, ubestemt entall eple og bussen. Dataene gir vet > visste > vite og epler > eple > eplet; gikk er på topp bare 70 % av årene og «går» inkluderer i går; alle formene til buss kolliderer med busse. Se abstract.md.");

// 3 Data
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Innledning" });
s.addText("To datakilder, koblet på ordform", { placeholder: "title" });
const cardY = 1.7, cardH = 3.6, cardW = 5.3;
[[MX, "Norsk Ordbank (bokmål)", ["154 824 lemmaer", "1 143 887 fullformer", "803 paradigmer", "Gir: leksem, ordklasse og bøyningskategori for hver form"]],
 [W - MX - cardW, "NB n-gram (dhlab)", ["Bokkorpuset 1950–2020: 71 enkeltår", "Totalfrekvenser for hele NB-korpuset", "Gir: frekvens per ordform og år, men ikke leksem"]]].forEach(([x, head, items]) => {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: cardY, w: cardW, h: cardH, rectRadius: 0.15, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: `kort ${head}` });
  s.addText(head, { x: x + 0.35, y: cardY + 0.3, w: cardW - 0.7, h: 0.5, fontSize: 22, bold: true, color: C.text1, margin: 0, isTextBox: true });
  body(s, bullets(items), x + 0.35, cardY + 1.0, cardW - 0.7, cardH - 1.2, 16);
});
s.addText("ordform", { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.12, x: W / 2 - 0.7, y: cardY + cardH / 2 - 0.3, w: 1.4, h: 0.6, fontSize: 16, italic: true, bold: true, align: "center", valign: "middle", margin: 0, color: C.background1, fill: { color: C.accent1 }, objectName: "kobling" });
body(s, [{ text: "Kjernen i problemet: n-grammene teller former, ordboka kjenner leksemer.", options: { bold: true, color: C.text1 } }], MX, 5.7, W - 2 * MX, 0.6, 18);
s.addNotes("Tall fra AGENTS.md (rådatafilene). Sjekk hvilke korpusavgrensninger vi faktisk bruker i hvert resultat (ngram_book vs. nb_totals).");

// 4 Former ≠ leksemer
pres.addSection({ title: "Metode" });
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Metode" });
s.addText("Én form, flere leksemer", { placeholder: "title" });
s.addImage({ path: FIG("paradigmegraf_fisker.png"), x: MX, y: 1.35, w: 6.66, h: 5.3, altText: "Paradigmegrafen rundt fisker: substantivene fisker, fisk og fiske og verbet fiske deler ordformer; substantivet fiske har ingen entydige former" });
// Ordboka mot bruken: andel lemmaer talt én gang hver, og vektet etter frekvens i NB (nb_totals)
{
  const x0 = 8.6, cw = 2.05;
  [["I ordboka", 0], ["I bruk (NB)", 1]].forEach(([h, i]) =>
    s.addText(h, { x: x0 + i * cw, y: 1.45, w: cw, h: 0.4, fontSize: 14, bold: true, color: C.text1, margin: 0, isTextBox: true }));
  [[["87,4 %", "29 %"], "deler ingen form med andre lemmaer", 1.85],
   [["97,3 %", "62 %"], "hører til en gruppe på høyst fire lemmaer som henger sammen via delte former, som fisker", 3.45]].forEach(([vals, label, y]) => {
    vals.forEach((v, i) => s.addText(v, { x: x0 + i * cw, y, w: cw, h: 0.85, fontSize: 40, bold: true, fontFace: THEME.headFontFace,
      color: i === 0 ? C.accent1 : C.accent2, margin: 0, valign: "bottom", isTextBox: true, objectName: `stat ${v}` }));
    s.addText(label, { x: x0, y: y + 0.9, w: 2 * cw, h: 0.65, fontSize: 14, color: C.text2, margin: 0, valign: "top", isTextBox: true });
  });
  body(s, [{ text: "Ordboka er glissen, bruken er ikke: de hyppige ordene er de flertydige.", options: { bold: true, color: C.text1 } }], x0, 5.4, 2 * cw, 0.9, 16);
}
s.addNotes("Figuren lages av python3 -m sqlite.figurer fra paradigmegrafen (sqlite/paradigm_graph.py). Fire lemmaer deler «fisker». I boksene står de entydige formene (ankrene): fisker har tre, fisk har bare fisken, verbet fiske bare s-passiv fiskes (partisippformene er utelatt), og substantivet et fiske har ingen. Det er derfor et fiske ikke kan anslås. Slike firergrupper er sjeldne: 452 komponenter, 1,2 % av lemmaene. 87,4 % av 151 648 lemmaer deler ingen form; 97,3 % ligger i komponenter på høyst fire lemmaer (rapport_verbtyper.md §7.3). Høyre kolonne vekter hvert lemma med summen av NB-frekvensen (nb_totals) til formene sine: da er bare 29 % isolert og 62 % i grupper på høyst fire. Blant de 1 000 hyppigste lemmaene er 24 % isolert. 3,3 % av ordformene er flertydige mellom lemmaer, men de står for 29 % av forekomstene (substantiv, verb, adjektiv; logg.md del 71). Poenget: glissen graf gjør dekomponeringen mulig, hyppig flertydighet gjør den nødvendig.");

// 5 Gullstandard
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Metode" });
s.addText("Gullstandard: verb uten konkurrenter", { placeholder: "title" });
const funnel = [["606", "verb der inf, pres og pret ikke deler form med noe annet lemma"], ["580", "også perf-part entydig (Sett A)"], ["533", "alle fire former belagt i korpuset"]];
funnel.forEach(([n, t], i) => {
  const x = MX + i * 4.1;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.7, w: 3.8, h: 2.6, rectRadius: 0.15, fill: { color: i === 1 ? C.accent1 : C.background2 }, line: { color: i === 1 ? C.accent1 : C.background2 }, objectName: `trinn ${n}` });
  s.addText(n, { x: x + 0.3, y: 1.9, w: 3.2, h: 1.0, fontSize: 54, bold: true, fontFace: THEME.headFontFace, color: i === 1 ? C.background1 : C.text1, margin: 0, isTextBox: true });
  s.addText(t, { x: x + 0.3, y: 3.0, w: 3.2, h: 1.1, fontSize: 15, color: i === 1 ? C.background1 : C.text2, margin: 0, valign: "top", isTextBox: true });
});
body(s, [
  { text: "Sett B: ", options: { bold: true, color: C.text1 } },
  { text: "høyfrekvente kjerneverb med én kjent kollisjon (gå/går ~ i går, ha ~ ha!), tatt med og flagget.", options: { breakLine: true } },
  { text: "Krav: inf + pres + pret ≥ 100 000 treff; ingen form står i to kategorier (pret ≠ perf-part).", options: {} },
], MX, 4.7, W - 2 * MX, 1.0, 16);
s.addNotes("Gjenskapes med python3 -m sqlite.verbtyper (resultater/verbtyper.tsv). 100 000-grensen gjelder inf + pres + pret i nb_totals. «Internt distinkt» betyr at ingen form står i to av de fire kategoriene.");

// 6 Seks verbtyper
pres.addSection({ title: "Verb" });
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Verb" });
s.addText("Seks verbtyper, ikke tre", { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "Andel av Sett A", labels: ["1A inf>pres>pret", "1B inf>pret>pres", "2A pret>inf>pres", "2B pret>pres>inf", "3A pres>inf>pret", "3B pres>pret>inf"], values: [26.9, 27.1, 20.2, 7.4, 12.2, 6.2] }],
  chartOpts({ x: MX, y: 1.5, w: 7.4, h: 5.2, barDir: "bar", catAxisOrientation: "maxMin", chartColors: [FORM.inf, FORM.inf, FORM.pret, FORM.pret, FORM.pres, FORM.pres], showLegend: false, showTitle: true, title: "Andel av verbene i Sett A (N = 580), bøker 1950–2020", valAxisMaxVal: 35, valAxisHidden: true, valGridLine: { style: "none" } }));
s.addText("Infinitiv vil helst stå på 2. plass", { x: 8.4, y: 1.7, w: 4.3, h: 0.9, fontSize: 20, bold: true, color: C.text1, margin: 0, valign: "top", isTextBox: true });
body(s, bullets(["pret på topp: 73 % har inf på 2. plass", "pres på topp: 66 % har inf på 2. plass", "Unntakene er ikke-viljestyrte overganger (forsvinne, ankomme) og tilstander (trenge, bestå)"]), 8.4, 2.7, 4.3, 2.6, 16);
s.addNotes("Tall fra rapport_verbtyper.md §3, bokkorpuset 1950–2020 (python3 -m sqlite.verbtyper). Når inf er på topp, deler verbene seg likt mellom 1A og 1B (49,8 / 50,2 %). I hele NB-korpuset (nb_totals) er fordelingen 1A 29,8 / 1B 21,2 / 2A 17,9 / 2B 7,2 / 3A 14,8 / 3B 9,0 %; inf på 2. plass holder der også (71 % og 62 %). Hver farge er én hovedtype. Fargene følger formen på topp, som i trekanten på neste lysbilde.");

// 6b Trekanten
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Verb" });
s.addText("Hvert verb er et punkt i trekanten", { placeholder: "title" });
s.addImage({ path: FIG("verb_ternaer.png"), x: MX, y: 1.35, w: 7.09, h: 5.3, altText: "Trekantplott: andel infinitiv, presens og preteritum for 580 verb, farget etter formen på topp" });
body(s, bullets(["Hjørnene er 100 % av én form; midten er en jevn fordeling", "Skillelinjene viser hvilken form som er på topp", "Få verb ligger nær hjørnene: nesten alle bruker hele paradigmet", "Punktene samler seg mot infinitiv-hjørnet og langs aksen fra infinitiv til preteritum"]), 8.0, 1.7, 4.7, 4.6, 16);
s.addNotes("580 verb i Sett A, bokkorpuset 1950–2020 (python3 -m sqlite.figurer). Hver prikk er ett verb, plassert etter andelen inf/pres/pret; fargen er formen på topp (inf 54 %, pret 28 %, pres 18 %). Utvalgte verb er merket. Prikker nær en skillelinje har to nesten like store former.");

// 7 Stabilitet
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Verb" });
s.addText("Rangeringen står stille i 70 år", { placeholder: "title" });
stat(s, "71 av 71", "år (1950–2020) med nøyaktig samme rekkefølge av alle tre formene", MX, 1.6, 4.2);
const stable = ["vurdere", "undersøke", "overta", "forsvinne", "ankomme", "rope", "trenge", "bestå"];
stable.forEach((v, i) => chip(s, v, MX + (i % 2) * 2.1, 3.6 + Math.floor(i / 2) * 0.7, { w: 1.95, h: 0.55, fontSize: 16 }));
s.addImage({ path: FIG("verb_stabilitet.png"), x: 5.85, y: 1.45, w: 6.84, h: 4.9, altText: "Andel infinitiv, presens og preteritum per år 1950–2020 for vurdere, undersøke, forsvinne og trenge" });
s.addNotes("Alle åtte er Sett A-verb (rapport_verbtyper.md §4). De er utvalgte eksempler: for hele Sett A har 46 % samme topp alle 71 år og 14 % samme hele rangering (80 av 569 verb). Figuren viser fire av dem (python3 -m sqlite.figurer). Merk: rekkefølgen står stille, men andelene glir: vurdere går fra ca. 80 til 63 % infinitiv, trenger stiger fra 50 til 70 %.");

// 8 Substantiv
pres.addSection({ title: "Substantiv" });
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Substantiv" });
s.addText("Substantiv velger tall før bestemthet", { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "Andel", labels: ["ent ub", "ent be", "fl ub", "fl be"], values: [67.1, 16.5, 14.5, 1.9] }],
  chartOpts({ x: MX, y: 1.5, w: 5.4, h: 4.6, chartColors: [HEX.accent2], showLegend: false, showTitle: true, title: "Formen på 1. plass, Sett A (N = 5 799)", valAxisMaxVal: 80, valAxisHidden: true, valGridLine: { style: "none" } }));
const ntypes = [
  ["ent ub", "tid, utvikling, kvalitet, kirke"],
  ["ent be", "regjeringen, sommeren, hodet, senga"],
  ["fl ub", "medlemmer, millioner, personer, uker"],
  ["fl be", "amerikanerne, britene, bøndene"],
];
ntypes.forEach(([t, ex], i) => {
  const y = 1.6 + i * 0.68;
  chip(s, t, 6.5, y, { w: 1.3, h: 0.5, fontSize: 14, italic: false, bold: true, fill: C.accent2, color: C.background1 });
  s.addText(ex, { x: 8.0, y, w: 4.7, h: 0.5, fontSize: 15, italic: true, color: C.text2, valign: "middle", margin: 0, isTextBox: true });
});
stat(s, "91 %", "av substantivene med ent be på topp har ent ub på 2. plass (fl be → fl ub: 82 %)", 6.5, 4.4, 3.0);
stat(s, "53 %", "har samme form på topp i alle 71 år (1950–2020)", 9.8, 4.4, 2.9, C.accent2);
s.addNotes("Fra rapport_substantivtyper.md (python3 -m sqlite.substantivtyper). Gullstandard: alle fire former entydige i Ordbanken, internt distinkte, ≥ 100 000 treff, alle former belagt i bokkorpuset. Unntak fra «tall først»: fl ub på topp har ent ub på 2. plass i 71,5 % (en person / tre personer). Full rangering av alle fire former er stabil i 71 av 71 år for 7,9 % (343 lemmaer), median 78,9 % av årene.");

// 9 Enkeltbøker
pres.addSection({ title: "Enkeltbøker" });
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Enkeltbøker" });
s.addText("Én bok bruker sjelden hele paradigmet", { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "Verb", labels: ["Global #1", "Global #2", "Global #3"], values: [57.2, 26.1, 16.7] }],
  chartOpts({ x: MX, y: 1.5, w: 5.6, h: 4.2, chartColors: [HEX.accent1], showLegend: false, showTitle: true, title: "Verb: bøker med bare én form (N = 1 145)", valAxisMaxVal: 70, valAxisHidden: true, valGridLine: { style: "none" } }));
s.addChart(pres.charts.BAR, [{ name: "Substantiv", labels: ["Global #1", "Global #2", "Global #3", "Global #4"], values: [56.0, 32.5, 9.7, 1.8] }],
  chartOpts({ x: 6.9, y: 1.5, w: 5.8, h: 4.2, chartColors: [HEX.accent2], showLegend: false, showTitle: true, title: "Substantiv: bøker med bare én form (N = 813)", valAxisMaxVal: 70, valAxisHidden: true, valGridLine: { style: "none" } }));
body(s, [{ text: "Med 3–5 forekomster av et verb i en bok har bare 14 % alle tre formene. Formen som blir med, følger den globale profilen.", options: { color: C.text1 } }], MX, 5.9, W - 2 * MX, 0.8, 16);
s.addNotes("400 bøker 1980–2020 (200 skjønn, 200 fag), 20 verb og 12 substantiv. Fra sqlite/book_dispersion.py og logg.md del 11. Sjangereffekten (spise: inf>pret>pres i skjønn, inf>pres>pret i fag) kan bli et eget lysbilde.");

// 10 dø / dør
pres.addSection({ title: "Dekomponering" });

// 10a Formelen (fra build_tillegg.js lysbilde 2)
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Dekomponering" });
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
s.addNotes("Fra build_tillegg.js (lysbilde 2). rapport_dekomponering_tid.md §2–3. Over tid antas stabil profil: xᵢ(t) = (x̂ᵢ/Rᵢ) · Rᵢ(t). Nivået er usikkert, endringen langt sikrere. Harde grenser (60 %-regelen) ble vurdert, men en celle kan ha opptil 90 % (P99), så usikkerheten er i stedet modellert som spredning i ρ.");

// 10b dø / dør
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Dekomponering" });
s.addText("«dør» er mest et substantiv", { placeholder: "title" });
status(s, "UTKAST");
s.addChart(pres.charts.BAR, [
  { name: "Råtall", labels: ["inf: dø", "pres: dør", "pret: døde"], values: [15.1, 20.6, 64.3] },
  { name: "Etter dekomponering", labels: ["inf: dø", "pres: dør", "pret: døde"], values: [17.4, 8.7, 74.0] },
], chartOpts({ x: MX, y: 1.5, w: 7.2, h: 4.6, barGrouping: "clustered", chartColors: ["C9CCD3", HEX.accent1], showLegend: true, legendPos: "b", showTitle: true, title: "Profilen til verbet dø, bokkorpuset 1950–2020", valAxisMaxVal: 85, valAxisHidden: true, valGridLine: { style: "none" } }));
stat(s, "64 %", "av «dør» er substantivet en/ei dør, anslått fra døren, døra, dører og dørene (±10–15 pp)", 8.3, 1.5, 4.4);
body(s, [{ text: "dø flytter fra type 2B (pret > pres > inf) til 2A (pret > inf > pres).", options: { bold: true, color: C.text1 } }], 8.3, 3.6, 4.4, 1.0, 16);
note(s, "Tagget korpus (OBT) og bigrammer gir «dør» om lag 50/50 (OBT 50 % substantiv, bigram 49 %). Paradigmeanslaget på 64 % er trolig for høyt. Tittel og tall må avklares.", 8.3, 4.65, 4.4, 1.6);
s.addNotes("Fra rapport_verbtyper.md §7.2 punkt 3–5, regnet om 2026-11-20 med log-regresjon lært i bokkorpuset: estimate_wordform_shares(\"dør\", corpus=\"book\") gir 63,5 % substantiv / 36,5 % verb; summen av de ukappede anslagene er 1,05 × observert. Tidligere tall (faste regler fra nb_totals) var 71 / 29 %. For at pres skulle komme over inf, måtte verbandelen være over 73 %, altså 36 pp feil, mer enn 90-persentilen i valideringen. «døde» er også adjektivet død (rapport §7.2 punkt 5). Dekomponereren har nå adjektivankre, men for «døde» er summen av anslagene bare 0,05 × observert: dødd, dødt og dødene er alle atypisk sjeldne. Adjektivandelen er derfor ikke bestemt; overslagene spenner fra 2 % (alle adjektiv) via 14–35 % (tilstandsadjektiv som syk, blind, gammel) til 46 %. Det gir pret 74–61 / inf 18–26 / pres 9–13 %. 2A holder så lenge adjektivet er under 77 % av «døde». I det OBT-taggede korpuset er 28 % av «døde» adjektivet (rapport_dekomponering_obt.md §9); med 28 % blir profilen pret 67 / inf 22 / pres 11 %. MERK-boksen (2026-11-23): i det OBT-taggede korpuset med alle lag (43,7 mill. tokens) er «dør» 50 % substantiv / 50 % verb (rapport_dekomponering_obt.md §11), og bigrammene gir 51 % verb (rapport_dekomponering_tid.md §8). Begge er langt fra 64 % substantiv. OBT-korpuset er et annet utvalg enn bokkorpuset, men forskjellen er stor.");

// 10c døde (fra build_tillegg.js lysbilde 3)
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Dekomponering" });
s.addText("«døde»: adjektivet er 28 %, og dø er fortsatt 2A", { placeholder: "title" });
s.addChart(pres.charts.BAR, [
  { name: "inf", labels: ["Uten korreksjon", "28 % adjektiv (OBT)", "46 % adjektiv (høyeste overslag)"], values: [17.4, 21.9, 26.3] },
  { name: "pres", labels: ["Uten korreksjon", "28 % adjektiv (OBT)", "46 % adjektiv (høyeste overslag)"], values: [8.7, 10.9, 13.1] },
  { name: "pret", labels: ["Uten korreksjon", "28 % adjektiv (OBT)", "46 % adjektiv (høyeste overslag)"], values: [74.0, 67.2, 60.5] },
], chartOpts({ x: MX, y: 1.45, w: 7.6, h: 4.9, barDir: "col", barGrouping: "clustered", chartColors: [FORM.inf, FORM.pres, FORM.pret], showLegend: true, legendPos: "b", showTitle: true, title: "Profilen til dø i bokkorpuset (%)", valAxisMaxVal: 90, valAxisHidden: true, valGridLine: { style: "none" } }));
stat(s, "28 %", "av «døde» er adjektivet død i det taggede korpuset (29 % med alle fem lag)", 8.6, 1.5, 4.1);
stat(s, "< 77 %", "så lenge adjektivet er under dette, står pret > inf > pres (2A)", 8.6, 3.75, 4.1, C.accent2);
s.addNotes("Fra build_tillegg.js (lysbilde 3). rapport_verbtyper.md §7.2 punkt 5; rapport_dekomponering_obt.md §9 og §11. Paradigmeankrene alene kan ikke bestemme adjektivandelen (dødd, dødt og dødene er atypisk sjeldne; sum anslag / obs. 0,05). Adjektivankre (sqlite/adjektiv_gold.py) ga dekomponereren 71/29 i OBT-korpuset mot fasit 72/28 (lag 1). Med alle fem lag: OBT 71/29, dekomponereren 65/33.");

// 11 fisker over tid
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Dekomponering" });
s.addText("«fisker» fordelt på leksemer over tid", { placeholder: "title" });
status(s, "UTKAST");
chip(s, "fisker", MX, 1.7, { w: 1.8, h: 0.7, fontSize: 22, bold: true, fill: C.accent1, color: C.background1 });
body(s, bullets(["Ankre: fiskeren, fiskere, fiskerne (en fisker)", "fisken, fiskene (en fisk)", "fiske, fisket/fiska, fiskes (å fiske)"]), MX, 2.7, 4.4, 2.4, 16);
s.addImage({ path: FIG("fisker_over_tid.png"), x: 5.4, y: 1.5, w: 7.3, h: 4.33, altText: "Ordformen fisker fordelt på en fisker, fisk i flertall og å fiske i presens, andel per år 1950–2020" });
note(s, "I det taggede korpuset er bare 6–20 % av «fisker» flertall av fisk (bøker, per tiår). Paradigmeanslaget (57–74 %) er for høyt. Nivået må avklares.", MX, 4.95, 4.4, 1.6);
s.addNotes("python3 -m sqlite.figurer. Heltrukket: forholdstall lært i bokkorpuset (log-regresjon på 5 799 gullstandard-substantiv; pres / s-passiv for aktivitetsverb), sqlite/decompose_fisker.py book_decomposition. Stiplet: forholdstallene fra nb_totals (mest aviser) overført til bøker. «fiskene» er relativt nesten dobbelt så vanlig i bøker som i nb_totals, så tall lært i ett korpus passer dårlig i et annet. Andeler 1950 / 2020, bok: en fisker 21 / 14 %, fisk (fl) 57 / 74 %, å fiske 22 / 12 %. Sum av ukappede anslag / observert: 1,3 (bok) mot 2,0 (overført). 5 års glidende snitt. MERK-boksen (2026-11-23): i det OBT-taggede korpuset (alle lag) er «fisker» 57 % å fiske, 33 % en fisker og 10 % fisk (rapport_dekomponering_obt.md §11); i bøkene alene er fisk-andelen 6–20 % per tiår (rapport_stabilitet_obt.md §4.1). Paradigmeanslaget for fisk (flertall) i figuren er dermed langt for høyt.");

// 11b Kontekstrater (fra build_tillegg.js lysbilde 5)
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Dekomponering" });
s.addText("Bare verbet har stabile kontekster", { placeholder: "title" });
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
s.addNotes("Fra build_tillegg.js (lysbilde 5). sqlite/bigram_kontekst.py; rapport_dekomponering_tid.md §7. Ratene er lært på 120 entydige ord per celle. Flertallsandelen korrelerer med substantivraten (0,72), men forklarer for lite (sd log 1,22 → 1,05).");

// 11c Bigramvalidering (fra build_tillegg.js lysbilde 6)
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Dekomponering" });
s.addText("Bigrammer treffer best: 5 pp median", { placeholder: "title" });
s.addChart(pres.charts.BAR, [
  { name: "Median", labels: ["Paradigme", "Bigram", "Kombinert"], values: [9.7, 5.0, 5.4] },
  { name: "80-persentil", labels: ["Paradigme", "Bigram", "Kombinert"], values: [37.4, 14.5, 15.4] },
], chartOpts({ x: MX, y: 1.45, w: 7.4, h: 4.8, barDir: "col", barGrouping: "clustered", chartColors: [HEX.accent1, "C9CCD3"], showLegend: true, legendPos: "b", showTitle: true, title: "Avvik i verbandel fra OBT, 150 substantiv/verb-homografer (pp)", valAxisHidden: true, valGridLine: { style: "none" }, valAxisMaxVal: 45, dataLabelFormatCode: "0.0" }));
stat(s, "95 %", "riktig flertallsleksem med bigrammer (paradigme 79 %)", 8.5, 1.5, 4.2);
body(s, bullets(["Kombinasjonen hjelper ikke når usikkerheten er kalibrert", "Anbefaling: bigram der verbet har kontekster, ellers paradigme", "«dør» 51 % verb (OBT 52), «tro» 54 % (OBT 68)"]), 8.5, 3.6, 4.2, 2.6, 15);
s.addNotes("Fra build_tillegg.js (lysbilde 6). python3 -m sqlite.kombinert; resultater/kombinert_validering.tsv; rapport_dekomponering_tid.md §8. Med de opprinnelige usikkerhetene lå fasiten innenfor 80 %-intervallet bare for 42–46 % av formene; faktor 2,3 (paradigme) og 4,3 (bigram) trengs, tilpasset på de samme formene. Fasiten er fra et annet korpus. OBT-tallene her er fra lag 1; kombinert validering er ikke kjørt på nytt med alle lag.");

// 12b dør/tro over tid: brukstilfellet (ordbok → kurve for leksemet)
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Dekomponering" });
s.addText("Fra ordboka til kurven: «dør» og «tro»", { placeholder: "title" });
status(s, "UTKAST");
s.addImage({ path: FIG("dor_tro_metoder.png"), x: MX, y: 1.3, w: 11.4, h: 4.71, altText: "Verbandelen av ordformene dør og tro per år 1950–2020, anslått med bigrammer og med paradigmet, sammenlignet med det taggede korpuset" });
body(s, [{ text: "Bigrammer (å/kan/vil … tro, jeg/han/som/det … dør) treffer verbandelen best: median avvik 5 pp mot tagget korpus. ", options: { bold: true, color: C.text1 } },
         { text: "«tro» blir mer verb over tid; «dør» er stabil.", options: {} }], MX, 6.15, 12.1, 0.7, 15);
s.addNotes("Brukstilfellet: en bruker ser paradigmet i en ordbok og vil se kurven for ordet, ikke for overflateformen. Figur: python3 -m sqlite.figurer (dor_tro_metoder.png). Metode (rapport_dekomponering_tid.md §7–8): kontekstraten r = andelen av en infinitiv som står etter å/kan/vil/skal/må (56 %), og av en presensform etter jeg/han/hun/vi/de/som/det/den (24 %), lært på 120 entydige verb. Verbet = bigramtall / r; resten er substantivet. Substantivkonteksten (en/ei/et/min …) er for ustabil (0–32 % mellom ord) til å brukes som rate. Validert på 150 substantiv/verb-homografer mot OBT: median avvik 5,0 pp, riktig flertallsleksem 95 %; paradigmeanslaget 9,7 pp og 79 %. Usikkerhet: ±15 pp generelt, ±29 pp for jevnt fordelte former (båndet). «dør»: 51 % verb (OBT 52 %). «tro»: 54 % verb (OBT 68 % av substantiv + verb); verbet øker fra ca. 40–50 % til ca. 60 % 1950–2020, med begge metodene. Stiplet linje: paradigmeanslaget (for «tro» med OBT-fordelte ankre).");

// 12 Validering
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Dekomponering" });
s.addText("Hvor godt treffer metoden?", { placeholder: "title" });
s.addChart(pres.charts.BAR, [
  { name: "Faste regler (i dag)", labels: ["fl ub + pres (fisker)", "ent be + pret (landet)", "ent ub + inf (fiske)", "ent ub + pres (dør)"], values: [13.3, 14.6, 14.4, 16.8] },
  { name: "Log-regresjon", labels: ["fl ub + pres (fisker)", "ent be + pret (landet)", "ent ub + inf (fiske)", "ent ub + pres (dør)"], values: [11.0, 11.5, 10.5, 10.1] },
], chartOpts({ x: MX, y: 1.5, w: 7.4, h: 4.7, barDir: "bar", barGrouping: "clustered", catAxisOrientation: "maxMin", chartColors: ["C9CCD3", HEX.accent1], showLegend: true, legendPos: "b", showTitle: true, title: "Median feil i substantivandel (prosentpoeng), 3 000 kunstige homografer per type", valAxisMaxVal: 20, valAxisHidden: true, valGridLine: { style: "none" } }));
stat(s, "78–80 %", "av de kunstige homografene får riktig leksem i flertall (log-regresjon; faste regler 66–76 %)", 8.4, 1.5, 4.3);
stat(s, "× 1,6–2", "typisk avvik når én form anslås fra resten av paradigmet (log-regresjon)", 8.4, 3.55, 4.3, C.accent2);
body(s, [{ text: "Retning: ja. Presise andeler: ±10–15 pp.", options: { bold: true, color: C.text1 } }], 8.4, 5.55, 4.3, 0.7, 16);
s.addNotes("python3 -m sqlite.valider_dekomponering. Gullstandarden (2 772 substantiv og 533 verb med alle kategorier i nb_totals) har kjent fasit. Test 1: én kategori holdes ute og anslås fra de andre; typisk avvik ×1,55–2,0 med log-regresjon, ×1,7–2,7 med de faste reglene i decomposer.py. Test 2: en substantivform og en verbform slås sammen til en kunstig homograf; 90-persentilen for feilen er fortsatt ca. 30 pp. De faste reglene er skjeve (for ent ub + pres undervurderer de substantivandelen med 13 pp i median). Dekomponereren bruker derfor nå log-regresjon lært i samme korpus; for «dør» i bøker gir det 64 % substantiv, mot 71 % før. Det enkelte ordet kan altså avvike fra den typiske skjevheten. Log-regresjonen er lært med 5-delt kryssvalidering.");

// 12c Decomposer mot hele det taggede korpuset (ny 2026-11-23)
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Dekomponering" });
s.addText("44 mill. ord tagget: samme treff, samme svakhet", { placeholder: "title" });
status(s, "UTKAST");
s.addChart(pres.charts.BAR, [{ name: "Median avvik", labels: ["Alle kandidater modellert", "… og godt grunnlag", "Alle innholdsord", "Minst én kandidat umodellert"], values: [10.4, 9.6, 16.5, 50.0] }],
  chartOpts({ x: MX, y: 1.45, w: 7.4, h: 4.8, barDir: "bar", catAxisOrientation: "maxMin", chartColors: [HEX.accent2, HEX.accent2, HEX.accent2, HEX.accent1], showLegend: false, showTitle: true, title: "Median avvik fra OBT, paradigmemetoden (pp), 4 170 flertydige former", valAxisHidden: true, valGridLine: { style: "none" }, valAxisMaxVal: 60, dataLabelFormatCode: "0.0" }));
stat(s, "75 %", "riktig leksem får størst andel, både med 8 og 44 mill. ord (samme 1 722 former, 13 pp median)", 8.5, 1.5, 4.2);
body(s, bullets(["Fem ganger så mye data endrer ikke treffsikkerheten", "Største feilkilde: kandidater uten modell (adjektiv, «i går»): 888 former, 50 pp", "Enkeltord kan likevel flytte seg mye (kroner, fisker)"]), 8.5, 3.75, 4.2, 2.6, 15);
s.addNotes("Ny 2026-11-23. rapport_dekomponering_obt.md §11; python -m sqlite.valider_dekomponering_obt --db <alle lag> --ut resultater/alle_lag. Korpus: OBT-tagget, 1 076 dokumenter, 43,7 mill. tokens, 3 teksttyper × 8 tiår 1950–2026 (logg del 46 og 64). Søylene: logreg-varianten; «godt grunnlag» = sum anslag / observert ≥ 0,5; «umodellert» = minst 5 % av forekomstene på et leksem dekomponereren gir 0 %. 75 % og 13 pp: de 1 722 innholdsordformene som finnes i både lag 1 og alle lag, kjørt med samme kode (lag 1: 13,7 pp / 74 %; alle lag: 13,1 pp / 75 %). Paradigmemetoden, ikke bigrammene.");

// 12d Stabilitet med OBT-fordeling (ny 2026-11-23)
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Dekomponering" });
s.addText("Endringer som tåler valg av fordeling", { placeholder: "title" });
status(s, "UTKAST");
const DEC = ["1950", "1960", "1970", "1980", "1990", "2000", "2010", "2020"];
s.addChart(pres.charts.LINE, [
  { name: "krone: ubestemt flertall", labels: DEC, values: [81, 82, 85, 88, 89, 89, 90, 89] },
  { name: "dør: bestemt entall", labels: DEC, values: [71, 69, 68, 65, 68, 72, 76, 75] },
  { name: "gå: preteritum", labels: DEC, values: [41, 38, 34, 33, 33, 34, 38, 39] },
  { name: "sette: preteritum", labels: DEC, values: [32, 24, 20, 16, 22, 19, 29, 34] },
], {
  ...chartText, x: MX, y: 1.45, w: 7.6, h: 4.9,
  chartColors: [HEX.accent2, HEX.accent1, FORM.pres, FORM.pret], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 6,
  showLegend: true, legendPos: "b", showTitle: true, title: "Andel av lemmaets kjerneformer per tiår, bøker (%), OBT-fordeling per tiår",
  valAxisMinVal: 0, valAxisMaxVal: 100, valAxisLabelFormatCode: "0\"%\"", valGridLine: { color: HEX.lt2, size: 1 }, catGridLine: { style: "none" },
});
body(s, bullets([
  "Samme kurver med OBT per tiår, fast OBT-andel, dekomponereren og rå formtall",
  "Lag 1 alene (6–10 bøker per tiår) var for lite: andelen sette av «satt» hoppet 19–43 %. Med 32–47 bøker: 29–38 %",
  "Én bok kan fortsatt styre et tiår: en slektsbok står for 57 % av «døde» på 2000-tallet",
]), 8.6, 1.6, 4.1, 4.7, 15);
s.addNotes("Ny 2026-11-23. rapport_stabilitet_obt.md §4; python -m sqlite.stabilitet_obt --db <alle lag> --ut resultater/alle_lag. N-gram for bøker (bokmål) 1950–2020; flertydige former (satt, dør, kroner, går …) fordelt med OBT-andelen fra bøkene i samme tiår (skjønn- og faglitteratur i det taggede korpuset). «2020» er bare året 2020 i n-gram. Andelene er av lemmaets kjernekategorier (subst: 4; verb: inf, pres, pret, perf-part, imp). Usikkerhet med boka som enhet (bootstrap) er ikke regnet ut. Kurvene for gå og sette kan henge sammen med andelen fortellende tekst i preteritum.");

// 13 Litteratur
pres.addSection({ title: "Avslutning" });
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Avslutning" });
s.addText("Hva er nytt?", { placeholder: "title" });
status(s, "UTKAST");
const refs = [["Skjev frekvens i paradigmet", "Karlsson 1986; Arppe 2006 (finsk)"], ["Grammatiske profiler", "Janda & Lyashevskaya 2011; Newman 2008"], ["Paradigmer i mentalt leksikon", "Milin, Filipović Đurđević & Moscoso del Prado Martín 2009"]];
refs.forEach(([h, r], i) => {
  const y = 1.6 + i * 1.05;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y, w: 5.8, h: 0.9, rectRadius: 0.12, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: `ref ${h}` });
  s.addText([{ text: h, options: { bold: true, color: C.text1, breakLine: true } }, { text: r, options: { color: C.text2 } }], { x: MX + 0.25, y, w: 5.4, h: 0.9, fontSize: 15, valign: "middle", margin: 0, isTextBox: true });
});
s.addText("Vårt bidrag", { x: 7.0, y: 1.6, w: 5.7, h: 0.5, fontSize: 20, bold: true, color: C.accent1, margin: 0, isTextBox: true });
body(s, bullets(["70 år med årlige rangeringer, ikke ett tverrsnitt", "Alle seks rekkefølger av inf/pres/pret", "Profilene brukt baklengs: fordeler rå n-gram på leksemer uten POS-tagget korpus", "Validert mot 44 mill. ord tagget med Oslo-Bergen-taggeren", "Paradigmegraf over et helt nasjonalt ordforråd"]), 7.0, 2.2, 5.7, 3.4, 16);
s.addNotes("Fulle referanser i rapport_verbtyper.md §7.1, sjekket 2026-11-21. Karlsson 1986: ZPSK 39(1), 19–28. Arppe 2006: festskrift for Karlsson, 175–189. Janda & Lyashevskaya 2011: Cognitive Linguistics 22(4), 717–762. Milin, Filipović Đurđević & Moscoso del Prado Martín 2009: Journal of Memory and Language 60(1), 50–64 (relativ entropi mellom leksemets og klassens profil, serbisk). «Paradigms bit by bit» er et annet arbeid: Milin, Kuperman, Kostić & Baayen 2009 i Blevins & Blevins (red.), Analogy in Grammar, OUP.");

// 14 Oppsummering
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Avslutning" });
s.addText("Bøyningsprofiler er leksikalske — og stabile", { placeholder: "title" });
[
  ["Hvert leksem har sin favorittform", "Alle seks rekkefølger av inf / pres / pret finnes blant 580 verb. Substantiv skiller seg først på tall, så på bestemthet."],
  ["Profilene står stille i 70 år", "Samme form på topp i alle 71 år for 46 % av verbene og 53 % av substantivene (bokkorpuset 1950–2020)."],
  ["Profilene kan brukes baklengs", "Flertydige former fordeles på leksemer uten tagget korpus: riktig hovedleksem i 3–4 av 5 tilfeller med paradigmet, 95 % med bigrammer. dø er type 2A også når adjektivet i «døde» trekkes fra."],
  ["Andelene er usikre", "±10–15 pp. Metoden trenger entydige former i paradigmet og svikter når de mangler (et fiske), når konkurrenten ikke modelleres (adjektiv, «i går») eller når sjeldne ordbokshomografer får for stor vekt."],
].forEach(([head, text], i) => {
  const x = MX + (i % 2) * 6.2, y = 1.55 + Math.floor(i / 2) * 2.7, w = 5.9, h = 2.45;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: i === 3 ? C.background1 : C.background2 }, line: i === 3 ? { color: HEX.accent3, width: 1.5, dashType: "dash" } : undefined, objectName: `funn ${i + 1}` });
  s.addText(String(i + 1), { shape: pres.shapes.OVAL, x: x + 0.3, y: y + 0.3, w: 0.6, h: 0.6, fontSize: 20, bold: true, align: "center", valign: "middle", margin: 0, color: C.background1, fill: { color: i === 3 ? C.text2 : C.accent1 }, objectName: `nummer ${i + 1}` });
  s.addText(head, { x: x + 1.1, y: y + 0.28, w: w - 1.35, h: 0.65, fontSize: 21, bold: true, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
  s.addText(text, { x: x + 1.1, y: y + 1.0, w: w - 1.35, h: h - 1.2, fontSize: 15, color: C.text2, valign: "top", margin: 0, isTextBox: true });
});
s.addNotes("1: lysbilde 6–8 (rapport_verbtyper.md §3, rapport_substantivtyper.md §3). 2: lysbilde 8 og rapportenes §4; 46 % = 260 av 569 Sett A-verb belagt alle 71 år, 53 % = 2 314 av 4 355 substantiv. 3 (oppdatert 2026-11-23): paradigmet 75 % riktig hovedleksem i hele det taggede korpuset (rapport_dekomponering_obt.md §11), bigrammer 95 % (rapport_dekomponering_tid.md §8). Tidligere tekst: ca. 80 % riktig hovedleksem både med kunstige homografer (rapport_dekomponering_validering.md) og for former der alle kandidatene er modellert i det OBT-taggede korpuset (rapport_dekomponering_obt.md §9). 4: et fiske har ingen entydige former (lysbilde 4); for døde er ankrene atypisk sjeldne; sjeldne adjektiv som grunn og bein får for mye. Hovedpoeng: profilene er en egenskap ved leksemet, og nettopp derfor kan de brukes til å fordele rå n-gram.");

(async () => {
  await pres.writeFile({ fileName: OUT });
  if (APPLY_THEME) {
    const { applyTheme } = require(APPLY_THEME);
    await applyTheme(OUT, THEME);
  }
  console.log("Skrev", OUT);
})();
