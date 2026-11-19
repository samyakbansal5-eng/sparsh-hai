// SPARSH presentation deck (pptxgenjs, structured: theme + layouts + sections)
const pptxgen = require("pptxgenjs");
const path = require("path");
const { applyTheme } = require("/mnt/skills/public/pptx/scripts/apply_theme.js");
const R = (p) => path.join(__dirname, "..", p);

const THEME = {
  name: "SPARSH",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1F2A44", lt1: "FFFFFF", dk2: "4A5572", lt2: "F2F4F8",
    accent1: "F4B942", accent2: "1E8A5A", accent3: "D98A00", accent4: "B54646",
    accent5: "2B62C9", accent6: "8A93A8", hlink: "2B62C9", folHlink: "6D2E46",
  },
};
const HEX = { ink: "1F2A44", ink2: "4A5572", acc: "F4B942", tint: "F2F4F8", line: "DDE2EC", green: "1E8A5A", amber: "D98A00", red: "B54646", blue: "2B62C9", heur: "3B5BDB", learn: "E8590C" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = "SPARSH – BITS F364 Human-AI Interaction";
pres.author = "Team SPARSH";
pres.company = "BITS Pilani";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "SPARSH_DARK_TITLE", background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.3, w: 11.7, h: 1.4, fontSize: 60, bold: true, color: C.background1, charSpacing: 6 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.75, w: 11.7, h: 1.2, fontSize: 22, color: C.accent1 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SPARSH_CONTENT", background: { color: C.background1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.9, fontSize: 34, bold: true, color: C.text1, valign: "middle" }, text: "" } },
    { text: { text: "SPARSH · BITS F364", options: { x: 0.6, y: 7.05, w: 4, h: 0.3, fontSize: 10, color: C.accent6, isTextBox: true } } },
  ],
  slideNumber: { x: 12.3, y: 7.05, w: 0.5, h: 0.3, fontSize: 10, color: "8A93A8" },
});
pres.defineSlideMaster({
  title: "SPARSH_DIVIDER", background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.8, w: 11.7, h: 1.2, fontSize: 44, bold: true, color: C.background1 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.0, w: 11.7, h: 1.0, fontSize: 20, color: C.accent1 }, text: "" } },
  ],
});

const T = (s, txt, o) => s.addText(txt, Object.assign({ isTextBox: true, fontSize: 15, color: C.text2, valign: "top", margin: 0 }, o));
function card(s, x, y, w, h, opts = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: opts.fill || C.background2 }, line: { color: opts.line || C.background2, width: 1 }, objectName: opts.name || "card" });
}
function chip(s, x, y, txt, fill, color) {
  s.addShape(pres.shapes.OVAL, { x, y, w: 0.62, h: 0.62, fill: { color: fill || C.accent1 }, line: { color: fill || C.accent1 } });
  T(s, txt, { x, y: y + 0.02, w: 0.62, h: 0.58, fontSize: 18, bold: true, color: color || C.text1, align: "center", valign: "middle" });
}
let sec = "";
function slide(master, title, section, notes) {
  if (section && section !== sec) { pres.addSection({ title: section }); sec = section; }
  const s = pres.addSlide({ masterName: master, sectionTitle: sec });
  if (title) s.addText(title, { placeholder: "title" });
  if (notes) s.addNotes(notes);
  return s;
}

// 1 Title
{
  const s = slide("SPARSH_DARK_TITLE", "SPARSH  स्पर्श", "Opening",
    "Speaker M4. Good morning. We are Team SPARSH. SPARSH means touch. Our project lets a visually impaired person identify switches on ANY switchboard by touch, with AI used once at setup, never needed afterwards.");
  s.addText("Any switchboard, readable by touch: AI-assisted tactile labelling of switchboards", { placeholder: "body" });
  s.addImage({ path: R("media/assets/stk_light.png"), x: 9.6, y: 0.5, w: 1.6, h: 1.6, objectName: "sticker" });
  s.addImage({ path: R("media/assets/stk_fan.png"), x: 11.2, y: 0.5, w: 1.6, h: 1.6, objectName: "sticker" });
  T(s, "BITS F364 Human-AI Interaction · Group [GROUP ID]\nDeepansh Saha · [Member 2] · [Member 3] · [Member 4]\nBITS Pilani, Pilani Campus · [Instructor name]", { x: 0.8, y: 5.6, w: 11.5, h: 1.2, fontSize: 16, color: "C9D0E2" });
}

// 2 Problem
{
  const s = slide("SPARSH_CONTENT", "Every switch feels the same", "Problem",
    "Speaker M4. Walk into an unfamiliar room: six to eight identical rockers. For a blind person that means trial and error, sometimes switching on a geyser, or asking for help every time. India has about 4.8 million blind people, mostly late-blind; blindness is linked to illiteracy, so braille can't be assumed. People already use bump dots, but a dot has no shared meaning, and nobody can see from a photo which switch runs which load.");
  s.addImage({ path: R("media/assets/pipe_3_rectified.jpg"), x: 0.6, y: 1.45, w: 7.2, h: 2.33, objectName: "board" });
  T(s, "A typical Indian modular board: identical 1M rockers, a socket, a blank cover. On an unfamiliar board, touch alone can't tell them apart, so people guess or ask.", { x: 0.6, y: 3.95, w: 7.2, h: 0.9, fontSize: 15 });
  const stats = [["≈ 4.8 M", "blind people in India (national survey, Vashist et al. 2022)"], ["16 / 16", "blind participants used tactile markers at home (Turkstra et al. 2025)"], ["None", "found in India's Harmonised Guidelines (MoHUA 2021 §4.15) requiring that a switch's function can be felt"]];
  stats.forEach(([n, l], i) => { card(s, 8.3, 1.45 + i * 1.75, 4.4, 1.55); T(s, n, { x: 8.55, y: 1.55 + i * 1.75, w: 4, h: 0.7, fontSize: 36, bold: true, color: C.text1, fontFace: "Cambria" }); T(s, l, { x: 8.55, y: 2.25 + i * 1.75, w: 4, h: 0.7, fontSize: 13 }); });
  card(s, 0.6, 5.1, 7.2, 1.6, { fill: "FFF6DF" });
  T(s, [{ text: "The hidden part: ", options: { bold: true, color: C.text1 } }, { text: "which switch runs the fan is in the wiring. No camera can see it, so a person has to be part of any solution." }], { x: 0.85, y: 5.3, w: 6.8, h: 1.2, fontSize: 16 });
}

// 3 Stakeholders & needs
{
  const s = slide("SPARSH_CONTENT", "Two users, one hand-over", "Problem",
    "Speaker M4. Primary users of the stickers are visually impaired adults; low-vision users are a separate sub-group. Primary users of the AI app are caregivers, family and hostel wardens. Needs come from literature first and our interviews second; the full needs-to-requirements traceability table is in the report section 6.4.");
  const people = [["VI adults", "use the stickers daily", "N1 find by touch · N2 any board · N3 no phone · N4 no braille · N12 comfortable", C.accent1],
                  ["Caregivers / wardens", "use the AI app once per board", "N7 quick & correct setup · N8 stay in control · N9 know AI's limits · N10 Hindi", C.accent5],
                  ["Support stakeholders", "NGOs, hostel admins, electricians", "N5 no rewiring · N6 low cost · N11 privacy", C.accent2]];
  people.forEach(([h, r, n, col], i) => {
    const x = 0.6 + i * 4.1;
    card(s, x, 1.5, 3.85, 4.2);
    chip(s, x + 0.3, 1.75, String(i + 1), col, i === 0 ? C.text1 : C.background1);
    T(s, h, { x: x + 0.3, y: 2.55, w: 3.3, h: 0.5, fontSize: 20, bold: true, color: C.text1 });
    T(s, r, { x: x + 0.3, y: 3.05, w: 3.3, h: 0.4, fontSize: 14, italic: true });
    T(s, n, { x: x + 0.3, y: 3.6, w: 3.3, h: 1.9, fontSize: 15 });
  });
  T(s, "Interviews [fill counts]: ≥ 5 VI adults · ≥ 3 caregivers/wardens · 1 accessibility professional · 1 electrician. Every need is traced to a requirement, an implemented feature and its validation evidence (report §6.4).", { x: 0.6, y: 6.0, w: 12.1, h: 0.8, fontSize: 14 });
}

// 4 RQs
{
  const s = slide("SPARSH_CONTENT", "Four questions, four separate experiments", "Problem",
    "Speaker M4. We deliberately keep these as separate studies with separate measures instead of one combined score. P1 and the refinement tool pick the sticker code first; Study B is our core human-AI experiment.");
  const rq = [["RQ1", "Appropriate reliance (core)", "Do confidence bands + reasons + forced review help installers catch seeded AI errors, vs bare suggestions?", "Study B"],
              ["RQ2", "Accessibility", "Does the sticker code make identification faster and more accurate than a plain board?", "Study A"],
              ["RQ3", "Generalisation", "Does the code transfer to a board layout the user has never touched?", "Study C"],
              ["RQ4", "Code refinement", "Which stickers get confused by touch, and does the refined code reduce confusions?", "P1"]];
  rq.forEach(([id, h, q, st], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.5 + Math.floor(i / 2) * 2.65;
    card(s, x, y, 5.95, 2.4);
    T(s, id, { x: x + 0.3, y: y + 0.25, w: 1.2, h: 0.5, fontSize: 24, bold: true, color: C.accent3, fontFace: "Cambria" });
    T(s, h, { x: x + 1.5, y: y + 0.3, w: 4.2, h: 0.45, fontSize: 19, bold: true, color: C.text1 });
    T(s, q, { x: x + 0.3, y: y + 0.9, w: 5.4, h: 0.95, fontSize: 15 });
    T(s, st, { x: x + 0.3, y: y + 1.85, w: 5.4, h: 0.35, fontSize: 13, bold: true, color: C.accent2 });
  });
}

// 5 Literature & gap
{
  const s = slide("SPARSH_CONTENT", "Closest prior work, and the gap that is left", "Research",
    "Speaker M4. 54 verified sources. Facade (CHI 2017) is our closest prior work and we say so: a photo turned into a 3D-printed tactile overlay for appliance panels. But appliance panels have visible labels; switchboards do not. That forces a human into the loop. Our gap is narrow but real.");
  const rows = [
    ["", "VizLens (UIST '16)", "Facade (CHI '17)", "SPARSH"],
    ["Target", "appliance panels", "appliance panels", "Indian wall switchboards"],
    ["Function visible in photo?", "yes (printed labels)", "yes (printed labels)", "no: hidden in wiring"],
    ["Who labels", "crowd", "crowd (simulated)", "AI detects; caregiver confirms + assigns"],
    ["Confidence shown", "no", "no", "3 bands + reasons"],
    ["Daily use needs phone", "yes", "no", "no"],
    ["Encoding", "audio", "braille / letters", "1 / 2 / 3 bumps + texture, off the shelf"],
  ];
  s.addTable(rows.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: i === 0 || j === 0, color: (j === 3 && i > 0) ? HEX.ink : HEX.ink2, fill: { color: i === 0 ? HEX.tint : (j === 3 ? "FFF6DF" : "FFFFFF") }, fontSize: 14 } }))),
    { x: 0.6, y: 1.45, w: 12.1, colW: [2.8, 2.7, 2.7, 3.9], border: { type: "solid", color: HEX.line, pt: 1 }, rowH: 0.48, valign: "middle", margin: 0.08 });
  T(s, [{ text: "What we do not claim: ", options: { bold: true, color: C.text1 } }, { text: "the first photo-to-tactile system (that's Facade). What's new: switchboards with invisible function, a caregiver-in-the-loop with confidence and forced verification, a braille-free code made of stickers anyone can buy, and a seeded-error test of whether showing AI confidence makes installers catch its mistakes." }], { x: 0.6, y: 5.25, w: 12.1, h: 1.2, fontSize: 15 });
}

// 6 Solution overview
{
  const s = slide("SPARSH_CONTENT", "One photo at setup, touch forever after", "Solution",
    "Speaker M2. Three parts: the caregiver's photo, the AI-plus-human mapping, and the stickers. The AI never decides what a switch controls.");
  const steps = [["1", "Photo", "Caregiver takes one photo of the board"], ["2", "AI finds where", "Switches detected, numbered S1…Sn, confidence shown"], ["3", "Human decides what", "Check boxes, flip each switch, assign + verify"], ["4", "Stickers + guide", "Bilingual guide: which sticker goes on which switch"]];
  steps.forEach(([n, h, d], i) => {
    const x = 0.6 + i * 3.1;
    card(s, x, 1.5, 2.85, 2.5);
    chip(s, x + 0.25, 1.7, n);
    T(s, h, { x: x + 0.25, y: 2.45, w: 2.4, h: 0.5, fontSize: 19, bold: true, color: C.text1 });
    T(s, d, { x: x + 0.25, y: 2.95, w: 2.4, h: 0.9, fontSize: 14 });
    if (i < 3) s.addShape(pres.shapes.RIGHT_TRIANGLE, { x: x + 2.9, y: 2.6, w: 0.15, h: 0.3, rotate: 0, fill: { color: C.accent6 }, line: { color: C.accent6 } });
  });
  s.addImage({ path: R("media/assets/stickers_row.png"), x: 0.6, y: 4.15, w: 8.4, h: 2.53, objectName: "sticker code" });
  card(s, 9.3, 4.25, 3.4, 2.3, { fill: "FFF6DF" });
  T(s, [{ text: "Daily use\n", options: { bold: true, color: C.text1, fontSize: 18 } }, { text: "no phone · no internet · no power. Plain switch = unused." }], { x: 9.5, y: 4.45, w: 3.0, h: 1.9, fontSize: 15 });
}

// 7 Sticker code v1 (v3)
{
  const s = slide("SPARSH_CONTENT", "A tactile code you can buy, not print", "Solution",
    "Speaker M4. Version 3 uses only off-the-shelf parts: clear bump-on stickers and the hook side of a hook-and-loop square. Light is one bump, fan two, socket three in a triangle, and anything else is a rough square. We avoided a bar because ISO 24503 says a bar means stop. The code is provisional: after the P1 touch pilot, our refinement tool reads the confusion matrix and proposes swaps for any sticker below 90% recall. 3D-printed caps from our earlier iteration stay as an optional upgrade.");
  const stk = [["stk_light", "Light", "one bump"], ["stk_fan", "Fan", "two bumps"], ["stk_socket", "Socket", "three bumps"], ["stk_other", "Other", "rough square"]];
  stk.forEach(([f, h, d], i) => {
    const x = 0.6 + i * 2.2;
    s.addImage({ path: R(`media/assets/${f}.png`), x: x, y: 1.4, w: 2.0, h: 2.0, objectName: h });
    T(s, h, { x, y: 3.4, w: 2.0, h: 0.4, fontSize: 18, bold: true, color: C.text1, align: "center" });
    T(s, d, { x, y: 3.8, w: 2.0, h: 0.4, fontSize: 13, align: "center" });
  });
  card(s, 0.6, 4.45, 8.6, 2.3);
  T(s, [{ text: "Error-driven refinement (tools/refine_vocabulary.py)\n", options: { bold: true, color: C.text1, fontSize: 16, breakLine: true } },
        { text: "P1: each sticker presented 4× by touch → confusion matrix", options: { bullet: true, breakLine: true } },
        { text: "keep a sticker only if recall ≥ 90% and no confusion > 10%", options: { bullet: true, breakLine: true } },
        { text: "otherwise swap in the tested candidate least confused with the rest → code v2", options: { bullet: true } }], { x: 0.8, y: 4.55, w: 8.2, h: 2.1, fontSize: 14, paraSpaceAfter: 4 });
  card(s, 9.5, 1.4, 3.2, 5.35, { fill: "FFF6DF" });
  T(s, [{ text: "Why stickers\n", options: { bold: true, color: C.text1, fontSize: 18, breakLine: true } },
        { text: "no printer, CAD or wiring: any household can buy them", options: { bullet: true, breakLine: true } },
        { text: "blind users already use bump dots, but with no shared meaning (Turkstra 2025)", options: { bullet: true, breakLine: true } },
        { text: "ISO 24503: bar = STOP, so no bar in our code", options: { bullet: true, breakLine: true } },
        { text: "count of bumps + texture = two separate cues", options: { bullet: true } }], { x: 9.7, y: 1.6, w: 2.85, h: 5.0, fontSize: 14, paraSpaceAfter: 6 });
}

// 8 Architecture
{
  const s = slide("SPARSH_CONTENT", "Eight separate modules", "System",
    "Speaker M5. Each module is its own file. The detector sits behind one function, so we can swap in YOLO later without touching the interface. Nothing goes to the cloud; logging is only on in Study Mode.");
  const mods = [["M1", "Acquisition", "photo + quality tips"], ["M2", "Preprocess", "find plate, straighten, CLAHE"], ["M3", "Detect", "proposals + verifier + bands"], ["M4", "Layout", "rows, S1…Sn"],
                ["M5", "Confirmation", "rules R1–R6, validation"], ["M6", "Tactile map", "vocabulary v1 (data)"], ["M7", "Guide", "print EN / हिंदी"], ["M8", "Logger", "Study Mode, IDs only"]];
  mods.forEach(([id, h, d], i) => {
    const x = 0.6 + (i % 4) * 3.1, y = 1.55 + Math.floor(i / 4) * 2.35;
    card(s, x, y, 2.85, 1.9, { fill: i === 4 ? "FFF6DF" : C.background2 });
    T(s, id, { x: x + 0.25, y: y + 0.2, w: 0.8, h: 0.4, fontSize: 16, bold: true, color: C.accent3 });
    T(s, h, { x: x + 0.25, y: y + 0.6, w: 2.4, h: 0.45, fontSize: 19, bold: true, color: C.text1 });
    T(s, d, { x: x + 0.25, y: y + 1.1, w: 2.4, h: 0.6, fontSize: 14 });
  });
  T(s, "Python · OpenCV · scikit-learn · Flask · vanilla JS (no build) · 12/12 unit tests · runs offline on a laptop; phones connect over local Wi-Fi", { x: 0.6, y: 6.35, w: 12.1, h: 0.5, fontSize: 14, italic: true });
}

// 9 CV pipeline
{
  const s = slide("SPARSH_CONTENT", "What the AI does with one photo", "System",
    "Speaker M1. The photo is a hard case: glossy plate, flash glare. Step one finds the plate by scoring quadrilaterals on area, rectangularity and how strong their outline is. Step two straightens it. Step three proposes every rectangle that might be a rocker, then a small learned verifier, HOG features plus logistic regression, scores each one. Here it found four, flagged one as a guess, and missed two under glare. That is exactly why the human step exists.");
  s.addImage({ path: R("media/assets/pipe_2_plate.jpg"), x: 0.6, y: 1.45, w: 5.6, h: 4.2, objectName: "plate found" });
  s.addImage({ path: R("media/assets/pipe_3_rectified.jpg"), x: 6.5, y: 1.45, w: 6.2, h: 2.01, objectName: "rectified" });
  s.addImage({ path: R("media/assets/pipe_4_detect.jpg"), x: 6.5, y: 3.64, w: 6.2, h: 2.01, objectName: "detected" });
  T(s, "1  Find the plate (yellow)", { x: 0.6, y: 5.8, w: 5.6, h: 0.4, fontSize: 15, bold: true, color: C.text1 });
  T(s, "2  Straighten  ·  3  Find switches + score confidence (green = sure, orange = guess)", { x: 6.5, y: 5.8, w: 6.2, h: 0.4, fontSize: 15, bold: true, color: C.text1 });
  T(s, "Two-stage detector: recall-oriented classical proposals → learned verifier (HOG + logistic regression, trained only on the train split). ≈ 0.2 s per photo on a CPU.", { x: 0.6, y: 6.25, w: 12.1, h: 0.6, fontSize: 13 });
}

// 10 Technical results
{
  const s = slide("SPARSH_CONTENT", "Detector: 0.995 F1 on test, 0.909 on unseen conditions", "Evaluation",
    "Speaker M1. Synthetic benchmark: 240 test photos, 1,020 switches, plus 90 stress photos with conditions never seen in training. The learned verifier beats the hand-tuned heuristic everywhere except glare. These are synthetic numbers, an upper bound; real photos are evaluated separately.");
  const labels = ["normal", "dim", "uneven", "angled", "blur", "dark plate", "glare*", "combined*", "far/small*"];
  s.addChart(pres.charts.BAR, [
    { name: "Heuristic", labels, values: [0.987, 0.988, 0.986, 0.929, 0.955, 0.968, 0.896, 0.922, 0.783] },
    { name: "Learned verifier", labels, values: [0.997, 0.994, 0.997, 0.985, 1.0, 0.994, 0.877, 1.0, 0.849] }], {
    x: 0.6, y: 1.4, w: 8.4, h: 5.3, barDir: "col", barGrouping: "clustered", chartColors: [HEX.heur, HEX.learn], showValue: false,
    showTitle: true, title: "F1 by photo condition (* = held-out stress)", titleFontSize: 13, titleColor: HEX.ink, titleFontFace: "+mn-lt",
    valAxisMinVal: 0.6, valAxisMaxVal: 1.0, valAxisLabelFormatCode: "0.0", catAxisLabelColor: HEX.ink2, valAxisLabelColor: HEX.ink2, catAxisLabelFontSize: 11, valAxisLabelFontSize: 11,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt", valGridLine: { color: "E6E3DC", size: 0.5 }, catGridLine: { style: "none" }, showLegend: true, legendPos: "b", legendFontSize: 12,
  });
  const st = [["0.995", "F1 · test (240 photos)"], ["96.3%", "photos with zero errors"], ["0.909", "F1 · unseen stress (90)"], ["0.2 s", "per photo on a CPU"]];
  st.forEach(([n, l], i) => { card(s, 9.3, 1.4 + i * 1.33, 3.4, 1.18); T(s, n, { x: 9.5, y: 1.48 + i * 1.33, w: 3.0, h: 0.6, fontSize: 30, bold: true, color: C.text1, fontFace: "Cambria" }); T(s, l, { x: 9.5, y: 2.08 + i * 1.33, w: 3.0, h: 0.4, fontSize: 13 }); });
}

// 11 Failure & iteration
{
  const s = slide("SPARSH_CONTENT", "A stress test broke it, so we fixed it", "Evaluation",
    "Speaker M1. Our stress test found that far-away boards were almost never detected: recall 0.35. The cause was a minimum plate area of 5% of the photo. Lowering it to 1.5%, with our edge-support score stopping wall blobs, doubled recall with no loss on the test set. We also added a photo tip in the app. Other failures we learned from: unrealistic wall textures and absolute edge thresholds in dim light.");
  s.addChart(pres.charts.BAR, [
    { name: "v1.0 (plate ≥ 5%)", labels: ["Recall", "Plate found", "Photos fully correct"], values: [0.347, 0.267, 0.333] },
    { name: "v1.1 (plate ≥ 1.5%)", labels: ["Recall", "Plate found", "Photos fully correct"], values: [0.75, 0.8, 0.767] }], {
    x: 0.6, y: 1.4, w: 7.0, h: 5.2, barDir: "col", barGrouping: "clustered", chartColors: ["ADB5C7", HEX.learn], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: HEX.ink, dataLabelFormatCode: "0.00",
    showTitle: true, title: "Far-away boards (held-out stress condition)", titleFontSize: 13, titleColor: HEX.ink, titleFontFace: "+mn-lt", valAxisMinVal: 0, valAxisMaxVal: 1,
    catAxisLabelColor: HEX.ink2, valAxisLabelColor: HEX.ink2, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt",
    valGridLine: { color: "E6E3DC", size: 0.5 }, catGridLine: { style: "none" }, showLegend: true, legendPos: "b", legendFontSize: 12, catAxisLabelFontSize: 12, valAxisLabelFontSize: 11,
  });
  const ls = [["Unrealistic walls", "noisy synthetic walls made the plate finder pick wall blobs (validation precision 0.33); fixed with realistic paints + edge-support scoring"], ["Dim photos", "absolute edge thresholds failed (validation F1 0.38); fixed by normalising per plate"], ["Glare", "still misses washed-out rockers (recall 0.80), so the UI forces a human check"]];
  ls.forEach(([h, d], i) => { card(s, 7.9, 1.4 + i * 1.75, 4.8, 1.55); T(s, h, { x: 8.15, y: 1.52 + i * 1.75, w: 4.3, h: 0.4, fontSize: 17, bold: true, color: C.text1 }); T(s, d, { x: 8.15, y: 1.92 + i * 1.75, w: 4.3, h: 0.95, fontSize: 13 }); });
}

// 12 HAI design
{
  const s = slide("SPARSH_CONTENT", "Designing the hand-over between AI and human", "Human-AI design",
    "Speaker M3. Bands instead of percentages, because lay users read categories better and a percentage would fake precision. Reasons are short cues, not persuasion. Bulk-keep only for green; amber and red must each be opened, which is cognitive forcing used only where it matters. And no switch counts as verified until the caregiver flips it. These rules are enforced in code and unit-tested.");
  s.addImage({ path: R("media/screens/03_low_conf_card.png"), x: 0.6, y: 1.4, w: 7.4, h: 4.63, objectName: "why card" });
  const rules = [["R1", "AI output starts as pending"], ["R2", "bulk-keep only for green; amber/red one by one"], ["R3", "AI never assigns what a switch does"], ["R4", "verified only after 'I flipped it'"], ["R5", "everything undoable, no restart"], ["R6", "confirm blocked until valid"]];
  rules.forEach(([id, d], i) => { T(s, id, { x: 8.3, y: 1.45 + i * 0.78, w: 0.7, h: 0.5, fontSize: 18, bold: true, color: C.accent3 }); T(s, d, { x: 9.0, y: 1.47 + i * 0.78, w: 3.7, h: 0.7, fontSize: 15, color: C.text1 }); });
  T(s, "Grounded in: Kay 2016 (discrete uncertainty), Bansal 2021 (explanations can raise blind acceptance), Buçinca 2021 (cognitive forcing), Zhang 2020 (complementary knowledge)", { x: 0.6, y: 6.25, w: 12.1, h: 0.6, fontSize: 12, italic: true });
}

// 13 Demo
{
  const s = slide("SPARSH_CONTENT", "Live demo: glare photo → verified guide", "Human-AI design",
    "Speaker M3. Play the demo video here (SPARSH_demo.mp4) or run the app live: python app/server.py, choose the demo_glare_board sample. Show: redraw the guess, add the two missed switches, assign plus verify, confirm, open the Hindi guide. Then show the stickers on the mock board and a tactile 'find the fan' task.");
  s.addImage({ path: R("media/screens/07_assign_mid.png"), x: 0.6, y: 1.4, w: 6.3, h: 3.94, objectName: "assign screen" });
  s.addImage({ path: R("media/screens/12_guide_hi.png"), x: 7.1, y: 1.4, w: 5.6, h: 3.5, objectName: "hindi guide" });
  T(s, "▶  SPARSH_demo.mp4  (or live: python app/server.py → sample 'demo_glare_board')", { x: 0.6, y: 5.6, w: 12.1, h: 0.45, fontSize: 17, bold: true, color: C.text1 });
  T(s, "AI found 4, flagged 1 guess, missed 2 under glare → caregiver redraws + adds → assigns 7 switches and verifies each → bilingual guide + sticker bill (3 light · 1 fan · 1 socket · 1 other)", { x: 0.6, y: 6.1, w: 12.1, h: 0.7, fontSize: 14 });
}

// 14 Study design
{
  const s = slide("SPARSH_CONTENT", "How we test it with real users", "Evaluation",
    "Speaker M5. Blindfolded sighted students only debug the apparatus in P0; they are never reported as evidence about blind users. We use mock boards with no mains connection. Study B is our core human-AI experiment: the same installers review board photos with bare AI boxes and with confidence and reasons, and about a quarter of the AI output is deliberately wrong in both, debriefed right after. Installers are sighted, so we can recruit 20 to 24, which gives 80% power for a medium-large effect.");
  const rows = [["Study", "Who", "Compare", "Measures"],
    ["P1 + refinement", "≥ 8 VI adults", "7 candidate stickers × 4", "confusion matrix, recall ≥ 90% → code v2"],
    ["A identification", "5–8 VI / low-vision elderly", "plain board vs stickers (AB/BA)", "time, accuracy, confidence, help"],
    ["B reliance (core)", "20–24 installers", "bare AI vs AI + confidence, 25% seeded errors", "errors missed, correct rejected, time, trust"],
    ["C generalisation", "Study A group", "learned layout → unseen layout", "accuracy vs 25% chance, recall at 24 h"]];
  s.addTable(rows.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: i === 0 || j === 0, color: i === 0 ? HEX.ink : HEX.ink2, fill: { color: i === 0 ? HEX.tint : "FFFFFF" }, fontSize: 14 } }))),
    { x: 0.6, y: 1.45, w: 12.1, colW: [2.6, 2.4, 3.4, 3.7], border: { type: "solid", color: HEX.line, pt: 1 }, rowH: 0.55, valign: "middle", margin: 0.08 });
  const st = [["Wilcoxon + effect size", "primary test (small n, skewed times); bootstrap 95% CI"], ["Study B: n = 24 → power 0.80", "for dz = 0.6 (VI studies: n = 10 for dz = 1.0)"], ["Ethics", "consent read aloud + large print · IDs only · debrief"]];
  st.forEach(([h, d], i) => { card(s, 0.6 + i * 4.1, 4.75, 3.85, 1.6); T(s, h, { x: 0.85 + i * 4.1, y: 4.9, w: 3.4, h: 0.45, fontSize: 17, bold: true, color: C.text1 }); T(s, d, { x: 0.85 + i * 4.1, y: 5.35, w: 3.4, h: 0.9, fontSize: 14 }); });
}

// 15 Results (to fill)
{
  const s = slide("SPARSH_CONTENT", "User-study results [fill from study/results]", "Evaluation",
    "Speaker M5. Replace every bracket with the numbers from study/analysis.py run on the real data. Never use the SIMULATED folder. If a result goes against us, say so: the decision rules were fixed in advance.");
  const boxes = [["P1", "Shapes kept: [ ]\nLowest recall: [shape, %]"], ["Study A", "Median time plain → stickers: [ ] s → [ ] s\nAccuracy: [ ]% → [ ]%  (r = [ ])"], ["Study B", "Seeded errors missed: bare [ ]% → confidence [ ]%\nCorrect boxes rejected: [ ]% → [ ]% (r = [ ])"], ["Study C", "Unseen-layout accuracy: [ ]% [95% CI]\nvs 25% chance"]];
  boxes.forEach(([h, d], i) => { const x = 0.6 + (i % 2) * 6.15, y = 1.45 + Math.floor(i / 2) * 2.55; card(s, x, y, 5.95, 2.3); T(s, h, { x: x + 0.3, y: y + 0.25, w: 5.3, h: 0.5, fontSize: 20, bold: true, color: C.text1 }); T(s, d, { x: x + 0.3, y: y + 0.85, w: 5.3, h: 1.2, fontSize: 16 }); });
  T(s, "Decision rules set before data collection: RQ1 holds if seeded errors missed ↓ with confidence (CI excludes 0) and correct boxes rejected ↑ ≤ 0.10 · RQ2 holds if time ↓ without accuracy ↓", { x: 0.6, y: 6.6, w: 12.1, h: 0.4, fontSize: 12, italic: true });
}

// 16 Feasibility & society
{
  const s = slide("SPARSH_CONTENT", "Cheap, removable, offline, private", "Feasibility",
    "Speaker M5. The sticker kit costs a few rupees per board (fill in from the receipt); a smart retrofit module is about 1,400 rupees. No rewiring, nothing opened. Privacy: board photos only, processed locally. Risk: a wrong sticker is a silent error for a blind user, which is why verification and a final check with the user are mandatory.");
  const st = [["₹ [ ]", "stickers per 8-switch board (from receipt)"], ["0", "parts to print, wire or solder"], ["₹1,429", "one smart retrofit module (for comparison)"]];
  st.forEach(([n, l], i) => { card(s, 0.6 + i * 4.1, 1.45, 3.85, 1.6); T(s, n, { x: 0.85 + i * 4.1, y: 1.55, w: 3.4, h: 0.75, fontSize: 34, bold: true, color: C.text1, fontFace: "Cambria" }); T(s, l, { x: 0.85 + i * 4.1, y: 2.35, w: 3.4, h: 0.5, fontSize: 14 }); });
  const items = [["Extensible", "vocabulary is data; detector swappable; languages are templates"], ["Daily setting", "passive stickers; dry-cloth cleaning; replace by marker ID"], ["Safety", "non-conductive, external, ≤ 5 N actuation (to test), no rewiring"], ["Society", "RPwD 'reasonable accommodation' for existing boards; braille-free"], ["Privacy", "board photos only, local processing, ID-only logs"], ["Environment", "tiny stickers, replaced individually; no electronics"]];
  items.forEach(([h, d], i) => { const x = 0.6 + (i % 2) * 6.15, y = 3.35 + Math.floor(i / 2) * 1.15; T(s, h, { x, y, w: 1.9, h: 0.5, fontSize: 16, bold: true, color: C.accent3 }); T(s, d, { x: x + 1.9, y, w: 4.1, h: 1.0, fontSize: 14 }); });
}

// 17 Design decisions
{
  const s = slide("SPARSH_CONTENT", "Decisions we made, and what they cost", "Feasibility",
    "Speaker M2/M3. Sixteen decisions are logged with alternatives and evidence in report section 21; here are six.");
  const rows = [["Decision", "Why", "Cost"],
    ["AI never infers function (D-03)", "wiring is invisible; a wrong sticker is undetectable for the user", "caregiver flips every switch"],
    ["Mandatory physical verify (D-04)", "turns 'assigned' into 'tested' cheaply", "+1 tap per switch"],
    ["Off-the-shelf sticker code (D-18)", "no fabrication; avoids ISO 24503 bar = STOP", "must be validated in P1"],
    ["Classical + learned detector (D-07)", "no real data; explainable; CPU-fast", "weaker on unseen glare"],
    ["Bands, not % (D-09)", "lay users read categories; no fake precision", "coarser information"],
    ["Bare vs confidence, 25% seeded errors (D-16, D-17)", "real errors are rare; isolates the effect of the display", "mild deception + debrief"]];
  s.addTable(rows.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: i === 0 || j === 0, color: i === 0 ? HEX.ink : HEX.ink2, fill: { color: i === 0 ? HEX.tint : "FFFFFF" }, fontSize: 14 } }))),
    { x: 0.6, y: 1.45, w: 12.1, colW: [3.9, 5.0, 3.2], border: { type: "solid", color: HEX.line, pt: 1 }, rowH: 0.62, valign: "middle", margin: 0.08 });
}

// 18 Conclusion
{
  const s = slide("SPARSH_DIVIDER", "The AI sees where. People decide what.", "Close",
    "Speaker M5. Summary: honest division of labour between AI and human, a low-tech daily product, and a test plan that can prove us wrong. Future: 300 real photos then a YOLO comparison, a week-long recall study, printed caps as an upgrade kit, an Android version.");
  s.addText("Four stickers you can feel, on any board. AI only at setup, and we test whether showing its confidence stops its mistakes reaching the wall.", { placeholder: "body" });
  T(s, "Next: 300 real labelled photos → YOLO comparison · week-long recall study · printed-cap upgrade kit · Android on-device app", { x: 0.8, y: 5.4, w: 11.7, h: 0.8, fontSize: 16, color: "C9D0E2" });
}

// 19 Team
{
  const s = slide("SPARSH_CONTENT", "Team SPARSH: who did what", "Close",
    "Each member answers questions on their own workstream; everyone can explain the whole system. Questions?");
  const team = [["Deepansh Saha", "AI & app", "detector, confidence display, bare condition, logging"], ["[Member 2]", "Study lead", "Study B design, seeded errors, statistics"], ["[Member 3]", "Users & ethics", "interviews, NGO partner, ethics, Studies A/C"], ["[Member 4]", "Tactile code & comms", "stickers, P1, refinement, videos, poster"]];
  team.forEach(([n, r, d], i) => { const x = 0.6 + i * 3.1; card(s, x, 1.5, 2.9, 4.4); chip(s, x + 0.2, 1.7, String(i + 1)); T(s, n, { x: x + 0.2, y: 2.5, w: 2.55, h: 0.8, fontSize: 16, bold: true, color: C.text1 }); T(s, r, { x: x + 0.2, y: 3.3, w: 2.55, h: 0.6, fontSize: 14, italic: true, color: C.accent3 }); T(s, d, { x: x + 0.2, y: 3.95, w: 2.55, h: 1.8, fontSize: 13 }); });
  T(s, "Thank you · Questions?", { x: 0.6, y: 6.2, w: 12.1, h: 0.6, fontSize: 24, bold: true, color: C.text1, fontFace: "Cambria" });
}

(async () => {
  const out = path.join(__dirname, "SPARSH_Presentation.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
