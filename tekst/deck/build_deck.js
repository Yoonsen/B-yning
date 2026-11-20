// Bygger skjelettet til MONS-presentasjonen: tekst/mons_presentasjon.pptx
//
// Krever pptxgenjs (MIT-lisens): `npm install pptxgenjs@3.12.0` et sted, og kjør med
//   NODE_PATH=<sti til node_modules> node tekst/deck/build_deck.js
//
// Tall er hentet fra rapport_verbtyper.md og logg.md (del 11–13). Lysbilder/felt markert
// «MANGLER» eller «UTKAST» svarer til hullene i tekst/mons_presentasjon_plan.md.

const path = require("path");
const pptxgen = require("pptxgenjs");

const OUT = path.join(__dirname, "..", "mons_presentasjon.pptx");
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
status(s, "UTKAST");
s.addText("Verb: inf / pres / pret", { x: MX, y: 1.5, w: 6, h: 0.45, fontSize: 20, bold: true, color: C.text1, margin: 0, isTextBox: true });
chipRow(s, ["gikk 38 %", "går 34 %", "gå 28 %"], MX, 2.05);
chipRow(s, ["vet 55 %", "visste 26 %", "vite 19 %"], MX, 2.75);
body(s, [{ text: "Bokkorpuset 1950–2020. «går» inkluderer «i går».", options: {} }], MX, 3.4, 6, 0.4, 12);
s.addText("Substantiv: ent ub / ent be / fl ub", { x: MX, y: 3.95, w: 6, h: 0.45, fontSize: 20, bold: true, color: C.text1, margin: 0, isTextBox: true });
chipRow(s, ["epler 45 %", "eple 30 %", "eplet 11 %"], MX, 4.5);
chipRow(s, ["bussen 42 %", "buss 37 %", "busser 15 %"], MX, 5.2);
body(s, [{ text: "Andeler av alle fire former; bestemt flertall er ikke vist.", options: {} }], MX, 5.85, 6, 0.4, 12);
body(s, [{ text: "Spørsmål: Hvor mye av fordelingen skyldes leksemet selv — og er den stabil over tid?", options: { bold: true, color: C.text1 } }], 7.2, 2.05, 5.5, 1.3, 20);
s.addNotes("Verbtall fra rapport_verbtyper.md §4 (Sett B), substantivtall fra rapport_substantivtyper.md §5. OBS: abstractet sier at infinitiv «vite» dominerer (dataene: vet 55 % > visste 26 % > vite 19 %) og at «eple» dominerer (dataene: epler 45 % > eple 30 %; epla/eplene 14 % > eplet 11 %). Abstract og lysbilde må samkjøres. Alle formene til «buss» kolliderer med subst./verb «busse» i Ordbanken.");

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
status(s, "UTKAST");
chip(s, "fisker", 2.3, 3.4, { w: 1.8, h: 0.75, fontSize: 24, bold: true, fill: C.accent1, color: C.background1 });
[["å fiske · pres", 1.6], ["en fisker · ent ub", 2.6], ["en fisk · fl ub", 4.2], ["et fiske · fl ub", 5.2]].forEach(([t, y]) => {
  chip(s, t, 4.9, y, { w: 2.9, h: 0.6, fontSize: 16, italic: false });
  const ty = y + 0.3, up = ty < 3.775;
  s.addShape(pres.shapes.LINE, { x: 4.1, y: up ? ty : 3.775, w: 0.8, h: Math.abs(ty - 3.775), line: { color: HEX.dk2, width: 1.25 }, flipV: up, objectName: "kant" });
});
stat(s, "87,4 %", "av lemmaene i Ordbanken deler ingen form med andre lemmaer", 8.6, 1.6, 4.1);
stat(s, "97,3 %", "ligger i grupper på høyst fire lemmaer som deler former", 8.6, 4.0, 4.1, C.accent2);
s.addNotes("Linjene fra «fisker» kan trenge justering. Tall fra rapport_verbtyper.md §7.3 (sqlite/paradigm_graph.py). Vurder en figur av paradigmegrafen.");

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
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Dekomponering" });
s.addText("«dør» er mest et substantiv", { placeholder: "title" });
status(s, "UTKAST");
s.addChart(pres.charts.BAR, [
  { name: "Råtall", labels: ["inf: dø", "pres: dør", "pret: døde"], values: [15.1, 20.6, 64.3] },
  { name: "Etter dekomponering", labels: ["inf: dø", "pres: dør", "pret: døde"], values: [17.7, 6.9, 75.4] },
], chartOpts({ x: MX, y: 1.5, w: 7.2, h: 4.6, barGrouping: "clustered", chartColors: ["C9CCD3", HEX.accent1], showLegend: true, legendPos: "b", showTitle: true, title: "Profilen til verbet dø, bokkorpuset 1950–2020", valAxisMaxVal: 85, valAxisHidden: true, valGridLine: { style: "none" } }));
stat(s, "71 %", "av «dør» er substantivet en/ei dør, anslått fra døren, døra, dører og dørene", 8.3, 1.5, 4.4);
body(s, [{ text: "dø flytter fra type 2B (pret > pres > inf) til 2A (pret > inf > pres).", options: { bold: true, color: C.text1 } }], 8.3, 3.6, 4.4, 1.0, 16);
missing(s, "«døde» er også adjektivet død. pret er derfor et øvre anslag (69–76 %).", 8.3, 4.8, 4.4, 1.3);
s.addNotes("Fra rapport_verbtyper.md §7.2 punkt 3–5. Rangeringen 2A holder i sensitivitetsoverslaget, men prosentene må regnes på nytt når adjektivandelen av «døde» er beregnet. Valideringen (lysbilde 13) viser at de faste reglene undervurderer substantivandelen for denne typen homografer (ent ub + pres) med ca. 13 pp i median, så 71 % substantiv er trolig et lavt anslag.");

// 11 fisker over tid
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Dekomponering" });
s.addText("«fisker» fordelt på leksemer over tid", { placeholder: "title" });
status(s, "UTKAST");
chip(s, "fisker", MX, 1.7, { w: 1.8, h: 0.7, fontSize: 22, bold: true, fill: C.accent1, color: C.background1 });
body(s, bullets(["Ankre: fiskeren, fiskere, fiskerne (en fisker)", "fisken, fiskene (en fisk)", "fiske, fisket/fiska, fiskes (å fiske)"]), MX, 2.7, 4.4, 2.4, 16);
s.addImage({ path: FIG("fisker_over_tid.png"), x: 5.4, y: 1.5, w: 7.3, h: 4.33, altText: "Ordformen fisker fordelt på en fisker, fisk i flertall og å fiske i presens, andel per år 1950–2020" });
missing(s, "Nivået avhenger av hvor forholdstallene er lært: en fisker 14–21 % eller ca. 50 %. Bare økningen for fisk (flertall) er robust.", MX, 5.0, 4.4, 1.5);
s.addNotes("python3 -m sqlite.figurer. Heltrukket: forholdstall lært i bokkorpuset (log-regresjon på 5 799 gullstandard-substantiv; pres / s-passiv for aktivitetsverb), sqlite/decompose_fisker.py book_decomposition. Stiplet: forholdstallene fra nb_totals (mest aviser) overført til bøker. «fiskene» er relativt nesten dobbelt så vanlig i bøker som i nb_totals, så tall lært i ett korpus passer dårlig i et annet. Andeler 1950 / 2020, bok: en fisker 21 / 14 %, fisk (fl) 57 / 74 %, å fiske 22 / 12 %. Sum av ukappede anslag / observert: 1,3 (bok) mot 2,0 (overført). 5 års glidende snitt.");

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
s.addNotes("python3 -m sqlite.valider_dekomponering. Gullstandarden (2 772 substantiv og 533 verb med alle kategorier i nb_totals) har kjent fasit. Test 1: én kategori holdes ute og anslås fra de andre; typisk avvik ×1,55–2,0 med log-regresjon, ×1,7–2,7 med de faste reglene i decomposer.py. Test 2: en substantivform og en verbform slås sammen til en kunstig homograf; 90-persentilen for feilen er fortsatt ca. 30 pp. De faste reglene er skjeve: for ent ub + pres (dør-typen) undervurderer de substantivandelen med 13 pp i median, så 71 % substantiv for «dør» er trolig et lavt anslag. Log-regresjonen er lært med 5-delt kryssvalidering.");

// 13 Litteratur
pres.addSection({ title: "Avslutning" });
s = pres.addSlide({ masterName: "INNHOLD", sectionTitle: "Avslutning" });
s.addText("Hva er nytt?", { placeholder: "title" });
status(s, "UTKAST");
const refs = [["Fokalformer", "Karlsson 1986; Arppe 2006 (finsk)"], ["Grammatiske profiler", "Janda & Lyashevskaya 2011; Newman 2008"], ["Paradigmer i mentalt leksikon", "Milin, Filipović Đurđević & Baayen 2009"]];
refs.forEach(([h, r], i) => {
  const y = 1.6 + i * 1.05;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y, w: 5.8, h: 0.9, rectRadius: 0.12, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: `ref ${h}` });
  s.addText([{ text: h, options: { bold: true, color: C.text1, breakLine: true } }, { text: r, options: { color: C.text2 } }], { x: MX + 0.25, y, w: 5.4, h: 0.9, fontSize: 15, valign: "middle", margin: 0, isTextBox: true });
});
s.addText("Vårt bidrag", { x: 7.0, y: 1.6, w: 5.7, h: 0.5, fontSize: 20, bold: true, color: C.accent1, margin: 0, isTextBox: true });
body(s, bullets(["70 år med årlige rangeringer, ikke ett tverrsnitt", "Alle seks rekkefølger av inf/pres/pret", "Profilene brukt baklengs: fordeler rå n-gram på leksemer uten POS-tagget korpus", "Paradigmegraf over et helt nasjonalt ordforråd"]), 7.0, 2.2, 5.7, 3.4, 16);
s.addNotes("Referansene må sjekkes mot kildene (hull 6). Milin mfl. 2009 er trolig et kapittel i Blevins & Blevins (red.), Analogy in Grammar (OUP), ikke Cognitive Linguistics 20(1).");

// 14 Oppsummering
s = pres.addSlide({ masterName: "TITTEL", sectionTitle: "Avslutning" });
s.addText("Bøyningsprofiler er leksikalske — og stabile", { placeholder: "title" });
s.addText("1  Verb fordeler seg på seks profiltyper som speiler aksjonsart\n2  Rangeringen holder seg uendret over 70 år\n3  Stabile profiler gjør det mulig å fordele flertydige former på leksemer\n[Substantivfunn og valideringsresultat settes inn]", { placeholder: "body" });
s.addNotes("Oppsummeringen er et utkast; punkt 3 forutsetter at valideringen (lysbilde 12) gir et akseptabelt resultat.");

(async () => {
  await pres.writeFile({ fileName: OUT });
  if (APPLY_THEME) {
    const { applyTheme } = require(APPLY_THEME);
    await applyTheme(OUT, THEME);
  }
  console.log("Skrev", OUT);
})();
