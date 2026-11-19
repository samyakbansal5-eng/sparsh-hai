// SPARSH onboarding UI - vanilla JS, no build step, works offline on the laptop.
const $ = (s) => document.querySelector(s);
const S = { sid: null, img: null, w: 0, h: 0, items: [], sel: null, phase: "review", drawing: false,
            dragStart: null, dragBox: null, vocab: {}, lang: "en", lastResp: null, condition: "ai" };

const I18N = {
  hi: { tag: "स्पर्श स्टिकर के लिए स्विचबोर्ड सेटअप सहायक", s1: "फ़ोटो", s2: "AI जाँचें", s3: "काम चुनें व परखें", s4: "गाइड",
    h_start: "चार चरणों में स्विचबोर्ड सेट करें", lead: "एक फ़ोटो लें। AI स्विच की जगह दिखाएगा। <b>आप</b> तय करेंगे कि हर स्विच क्या चलाता है और उसे दबाकर जाँचेंगे। फिर SPARSH बताएगा कि किस स्विच पर कौन सा स्टिकर लगेगा।",
    take: "फ़ोटो लें या अपलोड करें", tip1: "बोर्ड के ठीक सामने खड़े हों; बोर्ड फ़ोटो में बड़ा दिखे।", tip2: "कमरे की लाइट जलाएँ। चमकदार प्लेट पर फ़्लैश से बचें।", tip3: "एक फ़ोटो में एक बोर्ड।",
    samples: "नमूना बोर्ड आज़माएँ", research: "शोधकर्ता विकल्प", drawhint: "स्विच के चारों ओर बॉक्स खींचें",
    l_high: "AI लगभग निश्चित", l_check: "AI अनिश्चित – कृपया जाँचें", l_low: "AI का अनुमान – शायद स्विच नहीं", l_human: "आपने जोड़ा",
    add: "छूटा स्विच जोड़ें", undo: "वापस", restart: "नई फ़ोटो", h_review: "AI ने जो पाया उसे जाँचें",
    p_review: "हर बॉक्स दबाएँ। असली स्विच रखें, जो स्विच नहीं है (सॉकेट, रेगुलेटर, खाली कवर) उसे हटाएँ। छूटा स्विच जोड़ें।",
    h_assign: "हर स्विच क्या चलाता है?", p_assign: "कैमरा वायरिंग नहीं देख सकता। स्विच दबाएँ, देखें क्या चालू होता है, फिर यहाँ चुनें और “मैंने जाँचा” पर टिक करें।",
    next_assign: "आगे: काम चुनें →", back_review: "← बॉक्स जाँच पर वापस", confirm: "मैपिंग पक्की करें",
    h_done: "मैपिंग पक्की हो गई", p_done: "गाइड प्रिंट करें, स्टिकर लगाएँ, फिर उपयोगकर्ता के साथ अंतिम जाँच करें।", again: "दूसरा बोर्ड सेट करें" },
};
const EN = {};
document.querySelectorAll("[data-i18n]").forEach((el) => (EN[el.dataset.i18n] = el.innerHTML));
const t = (k) => (S.lang === "hi" && I18N.hi[k]) || EN[k] || k;
const TXT = {
  en: { keep: "Yes, it's a switch", remove: "Not a switch", redraw: "Redraw box", why: "Why the AI marked this", checked: "I flipped it and checked what it controls",
        name: "Optional name (e.g. 'Bedroom tube light')", acceptHigh: (n) => `Keep all ${n} green boxes`, noneHigh: "No green boxes left to keep",
        sure: { high: "AI fairly sure", check: "AI unsure", low: "AI guess", human: "Added by you", plain: "AI found" },
        bareFound: (n) => `AI found ${n} switch${n === 1 ? "" : "es"}. Please check them.`,
        found: (n, c, l) => `AI marked <b>${n}</b> possible switch${n === 1 ? "" : "es"}` + (c ? ` · <b>${c}</b> need your check` : "") + (l ? ` · ${l} likely not switches` : ""),
        cannot: "The AI can see where switches are. It <b>cannot</b> know what each one controls – you decide that in step 3.",
        manual: "Manual mode: mark every switch yourself with “+ Add missed switch”.",
        before: "Before you confirm", pending: "waiting for you", ok: "kept", rej: "removed", unassigned: "not assigned" },
  hi: { keep: "हाँ, यह स्विच है", remove: "स्विच नहीं है", redraw: "बॉक्स दोबारा", why: "AI ने इसे क्यों चुना", checked: "मैंने दबाकर देखा कि यह क्या चलाता है",
        name: "नाम (वैकल्पिक, जैसे 'बेडरूम ट्यूबलाइट')", acceptHigh: (n) => `सभी ${n} हरे बॉक्स रखें`, noneHigh: "कोई हरा बॉक्स बाकी नहीं",
        sure: { high: "AI लगभग निश्चित", check: "AI अनिश्चित", low: "AI अनुमान", human: "आपने जोड़ा", plain: "AI ने पाया" },
        bareFound: (n) => `AI ने ${n} स्विच पाए। कृपया जाँच लें।`,
        found: (n, c, l) => `AI ने <b>${n}</b> संभावित स्विच चिह्नित किए` + (c ? ` · <b>${c}</b> आपकी जाँच चाहिए` : ""),
        cannot: "AI स्विच की जगह देख सकता है, पर यह <b>नहीं</b> जान सकता कि कौन सा स्विच क्या चलाता है – यह आप चरण 3 में तय करेंगे।",
        manual: "मैनुअल मोड: हर स्विच खुद चिह्नित करें।", before: "पक्का करने से पहले", pending: "आपकी प्रतीक्षा", ok: "रखा", rej: "हटाया", unassigned: "काम नहीं चुना" },
};
const tx = () => TXT[S.lang];
const COLORS = { high: "#1e8a5a", check: "#d98a00", low: "#b54646", human: "#2b62c9", plain: "#4a5572" };

function toast(msg) { const el = $("#toast"); el.textContent = msg; el.classList.add("show"); clearTimeout(toast.t); toast.t = setTimeout(() => el.classList.remove("show"), 2200); }
async function api(path, body, isForm) {
  const opt = body ? { method: "POST", body: isForm ? body : JSON.stringify(body), headers: isForm ? {} : { "Content-Type": "application/json" } } : {};
  const r = await fetch(path, opt); const j = await r.json();
  if (j.error) toast(j.error);
  return j;
}
function setStep(n) { document.querySelectorAll(".steps span").forEach((s) => { const k = +s.dataset.step; s.className = k === n ? "on" : k < n ? "done" : ""; }); }
function applyLang() {
  document.querySelectorAll("[data-i18n]").forEach((el) => (el.innerHTML = t(el.dataset.i18n)));
  $("#langBtn").textContent = S.lang === "en" ? "हिंदी" : "English";
  document.documentElement.lang = S.lang; if (S.sid) renderAll();
}

// ---------------- start ----------------
async function init() {
  S.vocab = (await (await fetch("/api/vocabulary")).json()).items;
  const samples = await (await fetch("/api/samples")).json();
  $("#sampleGrid").innerHTML = samples.map((f) => `<img tabindex="0" src="/api/samples/${f}" data-f="${f}" alt="sample board ${f}">`).join("");
  $("#sampleGrid").onclick = (e) => { if (e.target.dataset.f) startWith({ sample: e.target.dataset.f }); };
  $("#fileIn").onchange = (e) => { if (e.target.files[0]) { const fd = new FormData(); fd.append("file", e.target.files[0]); startWith(fd, true); } };
  $("#langBtn").onclick = () => { S.lang = S.lang === "en" ? "hi" : "en"; applyLang(); };
  $("#addBtn").onclick = () => toggleDraw(true);
  $("#undoBtn").onclick = () => act({ type: "undo" });
  $("#restartBtn").onclick = () => location.reload();
  $("#againBtn").onclick = () => location.reload();
  $("#acceptHighBtn").onclick = () => act({ type: "accept_all_high" });
  $("#toAssignBtn").onclick = () => { S.phase = "assign"; S.sel = firstWhere((i) => !i.function); renderAll(); };
  $("#backReviewBtn").onclick = () => { S.phase = "review"; renderAll(); };
  $("#confirmBtn").onclick = confirmMap;
  setupCanvas();
  updateBadge();
  $("#condSel").onchange = updateBadge;
}
function updateBadge() { S.condition = $("#condSel").value; $("#modeBadge").textContent = S.condition === "ai" ? "AI + confidence" : S.condition === "ai_bare" ? "AI (bare)" : "Manual (no AI)"; }

async function startWith(payload, isForm) {
  const s = await api("/api/session", { condition: $("#condSel").value, participant_id: $("#pidIn").value,
    study_mode: $("#studyChk").checked, inject_errors: $("#injectChk").checked });
  S.sid = s.id; S.condition = s.condition;
  toast(S.lang === "hi" ? "फ़ोटो जाँची जा रही है…" : "Looking at the photo…");
  const r = await api(`/api/session/${S.sid}/photo`, payload, isForm);
  if (r.error) return;
  S.lastResp = r; S.w = r.w; S.h = r.h;
  S.img = new Image(); S.img.onload = () => { $("#start").classList.add("hidden"); $("#work").classList.remove("hidden"); update(r); setStep(2); };
  S.img.src = r.plate;
}

// ---------------- state + render ----------------
function update(st) { if (st.items) S.items = st.items; S.state = st; if (S.sel && !S.items.find((i) => i.id === S.sel)) S.sel = null; renderAll(); }
function firstWhere(fn) { const a = S.items.filter((i) => i.status !== "rejected" && fn(i)); return a.length ? a[0].id : null; }
async function act(body) { body.id = body.id || S.sel; const r = await api(`/api/session/${S.sid}/action`, body); if (!r.error || r.items) update(r); return r; }

function renderAll() { draw(); renderBanner(); renderCard(); renderList(); renderIssues(); renderPhase(); }

function renderBanner() {
  const act = S.items.filter((i) => i.source === "ai");
  const c = act.filter((i) => i.band === "check").length, l = act.filter((i) => i.band === "low").length;
  document.querySelector(".legendBar").style.display = S.condition === "ai_bare" ? "none" : "";
  let h = S.condition === "manual" ? tx().manual : S.condition === "ai_bare" ? `${tx().bareFound(act.length)}<small>${tx().cannot}</small>` : tx().found(act.length, c, l) + `<small>${tx().cannot}</small>`;
  (S.lastResp?.issues || []).forEach((is) => (h += `<small class="${is.level}">⚠ ${is.msg}</small>`));
  $("#banner").innerHTML = h;
}
function renderPhase() {
  const review = S.phase === "review";
  $("#phaseReview").classList.toggle("hidden", !review); $("#phaseAssign").classList.toggle("hidden", review);
  $("#toAssignBtn").classList.toggle("hidden", !review); $("#backReviewBtn").classList.toggle("hidden", review);
  $("#confirmBtn").classList.toggle("hidden", review);
  const pending = S.items.filter((i) => i.status === "pending");
  const highPend = pending.filter((i) => i.band === "high" || i.band === "plain").length;
  $("#acceptHighBtn").textContent = highPend ? (S.condition === "ai_bare" ? (S.lang === "hi" ? `सभी ${highPend} AI बॉक्स रखें` : `Keep all ${highPend} AI boxes`) : tx().acceptHigh(highPend)) : tx().noneHigh;
  $("#acceptHighBtn").disabled = !highPend;
  $("#toAssignBtn").disabled = pending.length > 0 || !S.items.some((i) => i.status !== "rejected");
  $("#confirmBtn").disabled = !(S.state && S.state.can_confirm);
  setStep(review ? 2 : 3);
}
function statusChip(i) {
  if (i.status === "rejected") return `<span class="chip rej">${tx().rej}</span>`;
  if (i.status === "pending") return `<span class="chip pend">${tx().pending}</span>`;
  if (S.phase === "assign") return i.function ? `<span class="chip ok">${i.verified || i.function === "unused" ? "✓ " : ""}${vname(i.function)}</span>` : `<span class="chip pend">${tx().unassigned}</span>`;
  return `<span class="chip ok">${tx().ok}</span>`;
}
const vname = (f) => (S.vocab[f] ? (S.lang === "hi" ? S.vocab[f].name_hi : S.vocab[f].name_en) : f);
function renderList() {
  $("#list").innerHTML = S.items.map((i) => `<li data-id="${i.id}" class="${i.id === S.sel ? "sel" : ""} ${i.status === "rejected" ? "rejected" : ""}">
    <span class="n">${i.label}</span><span class="chip ${i.band}">${tx().sure[i.band] || ""}</span><span class="f">${i.name || ""}</span>${statusChip(i)}</li>`).join("");
  $("#list").querySelectorAll("li").forEach((li) => (li.onclick = () => { S.sel = li.dataset.id; renderAll(); }));
}
function renderCard() {
  const i = S.items.find((x) => x.id === S.sel);
  const c = $("#card");
  if (!i) { c.classList.add("hidden"); return; }
  c.classList.remove("hidden");
  let h = `<h3>${i.label} <span class="chip ${i.band}">${tx().sure[i.band]}</span></h3>`;
  if (i.source === "ai" && i.band !== "human" && i.reasons?.length) h += `<div class="muted">${tx().why}:</div><ul class="why">${i.reasons.map((r) => `<li>${r}</li>`).join("")}</ul>`;
  if (S.phase === "review" || i.status === "pending") {
    h += `<div class="row2"><button class="primary btnOk" id="kKeep">✓ ${tx().keep}</button><button class="primary btnNo" id="kRem">✕ ${tx().remove}</button></div>
          <button class="ghost wide" id="kRedraw">⬚ ${tx().redraw}</button>`;
  } else {
    h += `<div class="funcs">${["light", "fan", "socket", "other", "unused"].map((f) => `<button data-f="${f}" class="${i.function === f ? "sel" : ""}">${S.vocab[f].icon}${vname(f)}</button>`).join("")}</div>
          <input type="text" id="kName" placeholder="${tx().name}" value="${i.name || ""}">
          <label class="verify"><input type="checkbox" id="kVer" ${i.verified ? "checked" : ""} ${!i.function || i.function === "unused" ? "disabled" : ""}> ${tx().checked}</label>`;
  }
  c.innerHTML = h;
  if ($("#kKeep")) { $("#kKeep").onclick = async () => { await act({ type: "accept" }); next(); }; $("#kRem").onclick = async () => { await act({ type: "reject" }); next(); }; $("#kRedraw").onclick = () => toggleDraw(true, i.id); }
  c.querySelectorAll(".funcs button").forEach((b) => (b.onclick = () => act({ type: "assign", function: b.dataset.f, label: $("#kName").value })));
  if ($("#kName")) $("#kName").onchange = () => i.function && act({ type: "assign", function: i.function, label: $("#kName").value });
  if ($("#kVer")) $("#kVer").onchange = async (e) => { await act({ type: "verify", ok: e.target.checked }); if (e.target.checked) next(); };
}
function next() {
  const fn = S.phase === "review" ? (i) => i.status === "pending" : (i) => !i.function || (!i.verified && i.function !== "unused");
  const n = firstWhere(fn); if (n) { S.sel = n; renderAll(); }
}
function renderIssues() {
  if (S.phase === "review") { $("#issues").innerHTML = ""; return; }
  const v = (S.state?.validation || []).filter((x) => x.code !== "PENDING" || true);
  $("#issues").innerHTML = v.length ? `<h4>${tx().before}</h4>` + v.map((x) => `<div class="issue ${x.level}" data-id="${x.ids[0] || ""}">${x.level === "block" ? "●" : "▲"} ${x.msg}</div>`).join("") : "";
  $("#issues").querySelectorAll(".issue").forEach((d) => (d.onclick = () => { if (d.dataset.id) { S.sel = d.dataset.id; renderAll(); } }));
}

// ---------------- canvas ----------------
const cv = () => $("#cv");
function draw() {
  const c = cv(); if (!S.img) return;
  c.width = S.w; c.height = S.h;
  const g = c.getContext("2d"); g.drawImage(S.img, 0, 0);
  g.fillStyle = "rgba(20,24,36,.18)"; g.fillRect(0, 0, S.w, S.h);
  for (const i of S.items) {
    if (i.status === "rejected") continue;
    const [x0, y0, x1, y1] = i.box, col = COLORS[i.band] || COLORS.human, sel = i.id === S.sel;
    g.save(); g.lineWidth = sel ? 5 : 3; g.strokeStyle = col;
    if (i.band === "low") g.setLineDash([8, 6]);
    if (i.status === "pending") g.globalAlpha = 0.95;
    g.strokeRect(x0, y0, x1 - x0, y1 - y0); g.setLineDash([]);
    if (sel) { g.strokeStyle = "#fff"; g.lineWidth = 1.5; g.strokeRect(x0 - 5, y0 - 5, x1 - x0 + 10, y1 - y0 + 10); }
    const lab = i.label + (i.status === "pending" && i.band !== "high" && i.band !== "plain" ? " ?" : ""), tw = g.measureText(lab).width;
    g.font = "bold 18px Segoe UI, sans-serif"; const w = g.measureText(lab).width + 14;
    g.fillStyle = col; g.fillRect(x0, y0 - 26, w, 24); g.fillStyle = "#fff"; g.fillText(lab, x0 + 7, y0 - 8);
    if (i.function && i.function !== "unused" && S.vocab[i.function]) drawSym(g, S.vocab[i.function].symbol, (x0 + x1) / 2, (y0 + y1) / 2, Math.min(x1 - x0, y1 - y0) * 0.45, i.verified);
    g.restore();
  }
  if (S.dragBox) { const [a, b, c2, d] = S.dragBox; g.setLineDash([6, 4]); g.strokeStyle = COLORS.human; g.lineWidth = 3; g.strokeRect(a, b, c2 - a, d - b); }
}
function drawSym(g, sym, cx, cy, s, ver) {
  g.save(); g.fillStyle = ver ? "#f4b942" : "rgba(244,185,66,.65)"; g.strokeStyle = g.fillStyle; g.lineWidth = s * 0.16;
  g.beginPath(); g.arc(cx, cy, s * 0.62, 0, 7); g.fillStyle = "rgba(31,42,68,.85)"; g.fill(); g.fillStyle = ver ? "#f4b942" : "rgba(244,185,66,.7)";
  g.beginPath();
  if (sym === "dot") { g.arc(cx, cy, s * 0.2, 0, 7); g.fill(); }
  else if (sym === "line") g.fillRect(cx - s * 0.38, cy - s * 0.08, s * 0.76, s * 0.16);
  else if (sym === "triangle") { g.moveTo(cx, cy - s * 0.32); g.lineTo(cx + s * 0.34, cy + s * 0.26); g.lineTo(cx - s * 0.34, cy + s * 0.26); g.fill(); }
  else if (sym === "ring") { g.arc(cx, cy, s * 0.28, 0, 7); g.stroke(); }
  else if (sym === "cross") { g.fillRect(cx - s * 0.36, cy - s * 0.08, s * 0.72, s * 0.16); g.fillRect(cx - s * 0.08, cy - s * 0.36, s * 0.16, s * 0.72); }
  else if (sym === "square") g.fillRect(cx - s * 0.26, cy - s * 0.26, s * 0.52, s * 0.52);
  else if (sym === "bump1") { g.arc(cx, cy, s * 0.22, 0, 7); g.fill(); }
  else if (sym === "bump2") { g.arc(cx - s * 0.2, cy, s * 0.15, 0, 7); g.fill(); g.beginPath(); g.arc(cx + s * 0.2, cy, s * 0.15, 0, 7); g.fill(); }
  else if (sym === "bump3") { [[0, -0.2], [-0.2, 0.16], [0.2, 0.16]].forEach(([dx, dy]) => { g.beginPath(); g.arc(cx + s * dx, cy + s * dy, s * 0.13, 0, 7); g.fill(); }); }
  else if (sym === "texture") { g.fillRect(cx - s * 0.28, cy - s * 0.28, s * 0.56, s * 0.56); g.fillStyle = "rgba(31,42,68,.85)";
    for (let a = -2; a <= 2; a++) for (let b = -2; b <= 2; b++) g.fillRect(cx + a * s * 0.1 - s * 0.02, cy + b * s * 0.1 - s * 0.02, s * 0.04, s * 0.04); }
  g.restore();
}
function toCanvas(e) { const r = cv().getBoundingClientRect(); return [(e.clientX - r.left) * (S.w / r.width), (e.clientY - r.top) * (S.h / r.height)]; }
function toggleDraw(on, replaceId) { S.drawing = on; S.replaceId = replaceId || null; cv().classList.toggle("drawing", on); $("#drawHint").classList.toggle("hidden", !on); }
function setupCanvas() {
  const c = cv();
  c.addEventListener("pointerdown", (e) => {
    const [x, y] = toCanvas(e);
    if (S.drawing) { S.dragStart = [x, y]; S.dragBox = [x, y, x, y]; c.setPointerCapture(e.pointerId); return; }
    const hit = S.items.filter((i) => i.status !== "rejected" && x >= i.box[0] && x <= i.box[2] && y >= i.box[1] && y <= i.box[3]);
    S.sel = hit.length ? hit[0].id : null; renderAll();
  });
  c.addEventListener("pointermove", (e) => { if (!S.dragStart) return; const [x, y] = toCanvas(e); const [a, b] = S.dragStart; S.dragBox = [Math.min(a, x), Math.min(b, y), Math.max(a, x), Math.max(b, y)]; draw(); });
  c.addEventListener("pointerup", async () => {
    if (!S.dragStart) return; const b = S.dragBox.map(Math.round); S.dragStart = null; S.dragBox = null;
    if (b[2] - b[0] < 8 || b[3] - b[1] < 8) { draw(); return; }
    if (S.replaceId) { await act({ type: "move", id: S.replaceId, box: b }); await act({ type: "accept", id: S.replaceId }); }
    else { const r = await act({ type: "add", box: b }); const added = S.items.find((i) => i.source === "human" && i.box.join() === b.join()); if (added) S.sel = added.id; }
    toggleDraw(false); renderAll();
  });
  document.addEventListener("keydown", (e) => {
    if (!S.sid || e.target.tagName === "INPUT") return;
    if (e.key === "Escape") toggleDraw(false);
    if (e.key === "z" && (e.ctrlKey || e.metaKey)) act({ type: "undo" });
    if (S.phase === "review" && S.sel) { if (e.key === "a") act({ type: "accept" }).then(next); if (e.key === "r") act({ type: "reject" }).then(next); }
  });
}

// ---------------- confirm ----------------
async function confirmMap() {
  const r = await act({ type: "confirm" });
  if (!r.mapping) return;
  $("#work").classList.add("hidden"); $("#done").classList.remove("hidden"); setStep(4);
  $("#guideEn").href = `/api/session/${S.sid}/guide?lang=en`; $("#guideHi").href = `/api/session/${S.sid}/guide?lang=hi`;
  $("#expJson").href = `/api/session/${S.sid}/export.json`; $("#expCsv").href = `/api/session/${S.sid}/export.csv`;
  const sym = { "CAP-L": "light", "CAP-F": "fan", "CAP-S": "socket", "CAP-O": "other" };  // cap id -> function
  $("#capSummary").innerHTML = Object.entries(r.mapping.caps_needed).map(([k, n]) => `<div>${S.vocab[sym[k]].icon} ${k} × ${n}</div>`).join("");
  if ($("#studyChk").checked) { $("#studyOut").classList.remove("hidden"); $("#studyOut").textContent = JSON.stringify(r.summary, null, 2); }
}
init();
