"""Builds the SPARSH scientific poster markup once and writes:
  poster/poster_local.html   (local file paths, rendered to A1 PDF by Chrome)
  poster/project/Main.dc.html (Design-canvas artboard, image urls from uploaded assets)
Design frame: A-series aspect 794 x 1123 px (A4 at 96 px/in); prints losslessly at A1/A0 (same aspect)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
W, H = 794, 1123
INK, INK2, ACC, TINT, LINE = "#1f2a44", "#4a5572", "#f4b942", "#f3f1ec", "#e2dccf"


def body(img):
    card = f"background:#ffffff;border:1px solid {LINE};border-radius:8px;padding:9px 10px;box-sizing:border-box"
    h = f"margin:0 0 5px 0;font-size:14.5px;font-weight:800;color:{INK};letter-spacing:.01em;display:flex;align-items:center;gap:6px"
    num = f"display:inline-flex;width:17px;height:17px;border-radius:50%;background:{ACC};color:{INK};font-size:10px;font-weight:800;align-items:center;justify-content:center"
    p = f"margin:0;font-size:9.9px;line-height:1.42;color:{INK2}"
    li = f"margin:0 0 2px 0;font-size:9.9px;line-height:1.4;color:{INK2}"
    b = f"color:{INK};font-weight:700"
    stat = lambda n, l: f'<div style="flex:1;background:{TINT};border-radius:6px;padding:6px 7px"><div style="font-size:15px;font-weight:800;color:{INK};white-space:nowrap">{n}</div><div style="font-size:8.6px;line-height:1.3;color:{INK2};margin-top:2px">{l}</div></div>'
    th = f"text-align:left;font-size:9px;color:{INK};padding:3px 4px;border-bottom:1px solid {LINE};background:{TINT}"
    td = f"font-size:9px;color:{INK2};padding:3px 4px;border-bottom:1px solid {LINE};vertical-align:top"

    def sec(n, title, inner, extra=""):  # extra: e.g. flex-grow on the last card
        return f'<section style="{card};{extra}"><h2 style="{h}"><span style="{num}">{n}</span>{title}</h2>{inner}</section>'

    col1 = "".join([
        sec(1, "Problem", f'''<p style="{p}">On an <b style="{b}">unfamiliar</b> Indian modular switchboard, 6–8 identical rockers feel the same. Blind people guess or ask for help. Which switch runs the fan is <b style="{b}">hidden in the wiring</b>: no photo can show it.</p>
<div style="display:flex;gap:5px;margin-top:6px">{stat("≈4.8 M", "blind people in India")}{stat("16/16", "blind users mark controls by touch")}{stat("None", "found in MoHUA 2021 §4.15 on feeling function")}</div>'''),
        sec(2, "Users &amp; needs", f'''<ul style="margin:0;padding-left:13px">
<li style="{li}"><b style="{b}">VI adults</b>: find a switch by touch on any board · no phone · no braille</li>
<li style="{li}"><b style="{b}">Caregivers / wardens</b>: quick, correct setup · stay in control · Hindi</li>
<li style="{li}"><b style="{b}">NGOs, admins, electricians</b>: no rewiring · cheap · private</li></ul>
<p style="{p};margin-top:3px">12 needs → 22 requirements, each traced to a feature + evidence.</p>'''),
        sec(3, "Research questions", f'''<table style="width:100%;border-collapse:collapse"><tr><th style="{th}">RQ</th><th style="{th}">Question</th><th style="{th}">Study</th></tr>
<tr><td style="{td}"><b style="{b}">RQ1</b></td><td style="{td}">Do AI confidence + reasons (vs bare boxes) make installers catch seeded AI errors?</td><td style="{td}">B (core)</td></tr>
<tr><td style="{td}"><b style="{b}">RQ2</b></td><td style="{td}">Sticker code vs plain board: faster, more accurate?</td><td style="{td}">A</td></tr>
<tr><td style="{td}"><b style="{b}">RQ3</b></td><td style="{td}">Does the code transfer to an unseen layout?</td><td style="{td}">C</td></tr>
<tr><td style="{td}"><b style="{b}">RQ4</b></td><td style="{td}">Which stickers are confused by touch; does refined code v2 fix it?</td><td style="{td}">P1</td></tr></table>'''),
        sec(4, "Closest work &amp; gap", inner=f'''<p style="{p}"><b style="{b}">Facade</b> (CHI'17) prints overlays for appliance panels with <i>visible</i> labels; <b style="{b}">VizLens</b> (UIST'16) needs a phone at every use. On switchboards the function is <b style="{b}">invisible</b>. <b style="{b}">Our gap:</b> caregiver-in-the-loop with confidence + verification, and a braille-free, height-coded vocabulary (54 sources).</p>'''),
        sec(5, "Key design decisions", extra="flex:1", inner=f'''<ul style="margin:0;padding-left:13px">
<li style="{li}"><b style="{b}">AI never infers function</b>: a wrong sticker is a silent error</li>
<li style="{li}"><b style="{b}">"I flipped it"</b> turns assigned into tested</li>
<li style="{li}"><b style="{b}">Bands, not %</b>: no fake precision</li>
<li style="{li}"><b style="{b}">25% seeded AI errors</b>, bare vs confidence, measure reliance</li></ul>'''),
    ])
    col2 = "".join([
        sec(6, "Solution: one photo, then touch forever", f'''<div style="display:grid;grid-template-columns:repeat(2, minmax(0, 1fr));gap:4px;margin-bottom:6px">
{''.join(f'<div style="background:{TINT};border-radius:6px;padding:5px 6px"><div style="font-size:10px;font-weight:800;color:{INK}">{a}</div><div style="font-size:8.6px;line-height:1.3;color:{INK2};margin-top:2px">{c}</div></div>' for a, c in [("1 Photo", "helper snaps the board"), ("2 AI finds where", "switches numbered S1…Sn with confidence"), ("3 People decide what", "check, flip, assign, verify"), ("4 Stickers + guide", "EN/हिंदी: which sticker goes where")])}</div>
<img src="{img['caps']}" alt="Four tactile stickers: one bump, two bumps, three bumps, rough square" style="width:100%;display:block;border-radius:6px">
<p style="{p};margin-top:3px"><b style="{b}">Sticker code v1</b>, all off the shelf: light = one bump · fan = two bumps · socket = three bumps · other = rough hook-and-loop square. No bar, because ISO 24503 reads bar = stop. P1 measures confusions; <code>refine_vocabulary.py</code> swaps any sticker under 90% recall. 3D-printed caps = optional upgrade.</p>'''),
        sec(7, "AI pipeline", f'''<img src="{img['detect']}" alt="Straightened switchboard with detected switches" style="width:100%;display:block;border-radius:6px">
<p style="{p};margin-top:4px">M1 photo checks → M2 find &amp; straighten plate → M3 proposals + <b style="{b}">learned verifier</b> (HOG + logistic regression) → bands: <b style="color:#1e8a5a">sure</b> / <b style="color:#d98a00">check</b> / <b style="color:#b54646">guess</b> → M4 S1…Sn → M5 human confirmation → M6 sticker map → M7 guide → M8 consented logs. ≈ 0.2 s on a CPU, offline.</p>'''),
        sec(8, "Human–AI hand-over", extra="flex:1", inner=f'''<img src="{img['card']}" alt="App screen: why the AI marked this box, keep or remove" style="width:100%;display:block;border-radius:6px;border:1px solid {LINE}">
<ul style="margin:4px 0 0 0;padding-left:13px">
<li style="{li}">AI output starts <b style="{b}">pending</b>; bulk-keep only for green, amber/red one by one</li>
<li style="{li}">AI <b style="{b}">never</b> assigns a function; each switch must be flipped and ticked "I checked"</li>
<li style="{li}">Redraw / add / undo, no restart; confirm blocked until valid (12/12 tests)</li>
<li style="{li}">Grounded in Kay 2016, Bansal 2021, Buçinca 2021, Zhang 2020</li></ul>'''),
    ])
    col3 = "".join([
        sec(9, "Technical results (synthetic benchmark)", f'''<img src="{img['f1']}" alt="F1 by photo condition, heuristic vs learned" style="width:100%;display:block">
<div style="display:flex;gap:5px;margin-top:4px">{stat("0.995", "F1, test: 240 photos, 1,020 switches")}{stat("0.909", "F1 on unseen stress conditions")}{stat("0.35→.75", "far-board recall after fix")}</div>
<p style="{p};margin-top:4px">Glare still hides rockers (recall 0.80), so a human check is always required. Synthetic numbers are an upper bound; real-photo results: [fill].</p>'''),
        sec(10, "User studies", f'''<table style="width:100%;border-collapse:collapse"><tr><th style="{th}">Study</th><th style="{th}">Who</th><th style="{th}">Compare</th></tr>
<tr><td style="{td}">P1</td><td style="{td}">≥ 8 VI adults</td><td style="{td}">7 stickers: confusion → code v2</td></tr>
<tr><td style="{td}">A</td><td style="{td}">5–8 VI / low-vision elderly</td><td style="{td}">plain vs stickers (AB/BA)</td></tr>
<tr><td style="{td}">B</td><td style="{td}">20–24 installers</td><td style="{td}">bare AI vs AI + confidence, 25% seeded errors</td></tr>
<tr><td style="{td}">C</td><td style="{td}">Study A group</td><td style="{td}">unseen layout vs 25% chance</td></tr></table>
<p style="{p};margin-top:4px">Wilcoxon + effect sizes + bootstrap CIs; mock boards (no mains); consent read aloud; blindfolded students only for apparatus pilots.</p>
<div style="margin-top:5px;background:#fff6df;border-radius:6px;padding:6px 7px;font-size:9.6px;line-height:1.45;color:{INK}"><b>Results:</b> seeded errors missed: bare [ ]% → confidence [ ]% · correct boxes rejected [ ]% → [ ]% · stickers vs plain time [ ] → [ ] s · unseen-layout accuracy [ ]%</div>'''),
        sec(11, "Feasibility &amp; ethics", inner=f'''<div style="display:flex;gap:5px">{stat("₹ [ ]", "stickers per board (receipt)")}{stat("₹1,429", "one smart retrofit module")}</div>
<p style="{p};margin-top:4px">No rewiring, removable, non-conductive. Board photos only, processed on the laptop; IDs-only logs. The code is data, so new stickers need no code changes.</p>'''),
        sec(12, "Conclusion", extra="flex:1", inner=f'''<p style="{p}"><b style="{b}">The AI sees where; people decide what.</b> Daily use stays low-tech: four stickers you can buy, no phone, no power, no rewiring. The human-AI test: does showing the AI's confidence stop its mistakes reaching the wall? Next: real photos → YOLO comparison, week-long recall.</p>
<p style="font-size:8.2px;line-height:1.4;color:#5b6478;margin:4px 0 0 0">Guo et al. CHI'17, UIST'16 · ISO 24503:2011, 24508:2019 · Wabiński et al. PLoS ONE'22 · Zhang et al. FAT*'20 · Buçinca et al. CSCW'21 · Kay et al. CHI'16 · Turkstra et al. Sci Rep'25 · Vashist et al. PLOS ONE'22 · Brulé et al. CHI'20</p>'''),
    ])
    gap = 7
    colstyle = f"display:flex;flex-direction:column;gap:{gap}px;min-width:0"
    return f'''<div style="width:{W}px;height:{H}px;box-sizing:border-box;background:#f7f4ee;font-family:Inter,'Noto Sans Devanagari',system-ui,sans-serif;display:flex;flex-direction:column;overflow:hidden">
<header style="background:{INK};color:#ffffff;padding:20px 40px 16px 40px;display:flex;align-items:center;gap:18px">
<div style="width:72px;height:72px;border:1.5px dashed #8f99b5;border-radius:8px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:7.5px;line-height:1.2;color:#c9d0e2;flex:none">BITS Pilani logo<br>(official file)</div>
<div style="flex:1;min-width:0">
<div style="font-size:9px;font-weight:700;letter-spacing:.16em;color:{ACC}">BITS F364 · HUMAN-AI INTERACTION · GROUP [GROUP ID]</div>
<h1 style="margin:3px 0 2px 0;font-size:31px;line-height:1.05;font-weight:800;letter-spacing:.02em">SPARSH <span style="color:{ACC};font-weight:700">स्पर्श</span></h1>
<div style="font-size:12.5px;line-height:1.3;color:#e2e6f0">AI-assisted tactile labelling of switchboards for visually impaired and elderly users</div>
<div style="font-size:8.6px;color:#aeb7cf;margin-top:5px">Deepansh Saha · [Member 2] · [Member 3] · [Member 4] · Instructor: [name] · BITS Pilani, Pilani Campus</div>
</div>
<div style="width:72px;height:72px;border:1.5px dashed #8f99b5;border-radius:8px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:7.5px;line-height:1.2;color:#c9d0e2;flex:none">Partner logo<br>(only with permission)</div>
</header>
<main style="flex:1;display:grid;grid-template-columns:repeat(3, minmax(0, 1fr));gap:{gap}px;padding:{gap+3}px 40px 6px 40px;min-height:0">
<div style="{colstyle}">{col1}</div><div style="{colstyle}">{col2}</div><div style="{colstyle}">{col3}</div>
</main>
<footer style="padding:4px 40px 14px 40px;font-size:7.6px;color:#5b6478;display:flex;justify-content:space-between"><span>Team SPARSH · code, CAD (STL/OpenSCAD), data and analysis pipeline included in our submission package</span><span>Contact: [team e-mail]</span></footer>
</div>'''


def main(mode):
    if mode == "local":
        img = {"caps": f"file://{ROOT}/media/assets/stickers_row.png", "detect": f"file://{ROOT}/media/assets/pipe_4_detect.jpg",
               "card": f"file://{ROOT}/media/screens/03_low_conf_card.png", "f1": f"file://{ROOT}/figures/detector_f1_by_condition.png"}
        html = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>SPARSH poster</title><style>@page{{size:594mm 841mm;margin:0}}body{{margin:0}}#z{{zoom:2.8277;}}</style></head><body><div id="z">{body(img)}</div></body></html>'
        open(os.path.join(HERE, "poster_local.html"), "w").write(html)
        open(os.path.join(HERE, "poster_preview.html"), "w").write(f'<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0">{body(img)}</body></html>')
    else:
        img = json.load(open(os.path.join(HERE, "asset_urls.json")))
        os.makedirs(os.path.join(HERE, "project"), exist_ok=True)
        dc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SPARSH scientific poster</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&amp;family=Noto+Sans+Devanagari:wght@600;700&amp;display=swap" rel="stylesheet">
<style>
body{{margin:0}}
a{{color:#2b62c9}}a:hover{{color:#1f2a44}}
</style>
</helmet>
{body(img)}
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":{W},"height":{H}}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
'''
        open(os.path.join(HERE, "project", "Main.dc.html"), "w").write(dc)
        canvas = {"v": 3, "createdOnFiles": {"v": 1, "at": "2026-11-14T12:00:00Z"}, "title": "SPARSH scientific poster",
                  "launch": {"view": "focused", "file": "Main.dc.html"}, "pages": [],
                  "boards": {"Main.dc.html": {"x": 0, "y": 0, "w": W, "h": H, "title": "Poster (A-series; print at A1)"}},
                  "order": ["Main.dc.html"], "notes": {}, "designSystems": []}
        json.dump(canvas, open(os.path.join(HERE, "project", "canvas.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "local")
