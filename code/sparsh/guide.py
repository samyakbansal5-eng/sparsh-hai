"""M7 - Installation guide generator (printable HTML, English + Hindi).
The guide is for the caregiver/installer; the legend card at the end is printed
large so it can be read with low vision and shown to the visually impaired user
while explaining the vocabulary."""
import base64
import datetime
import html

import cv2

from .tactile import cap_for, svg_symbol, VOCABULARY, VOCABULARY_VERSION

T = {
    "en": {"title": "SPARSH installation guide", "board": "Your switchboard (straightened photo)",
           "sw": "Switch", "where": "Where on the board", "ctrl": "Controls", "cap": "Sticker to fix", "feel": "How it feels",
           "row": "Row", "from_left": "from left", "steps": "How to install", "legend": "Tactile legend",
           "check": "Final check with the user", "caps": "Stickers needed",
           "s1": "Clean each switch face with a dry cloth. Do not use water or open the switch plate.",
           "s2": "Clean the switch with a dry cloth. Peel the backing of the sticker and press it on the UPPER half of the rocker for 10 seconds.",
           "s3": "Fix stickers in the order of the table below (S1 first). Tick each one.",
           "s4": "Flip every switch once: the sticker must not stop the rocker from moving fully.",
           "s5": "Ask the user to find each switch by touch while you call out the function.",
           "c1": "Every sticker is firmly attached and does not wobble.", "c2": "Every switch still turns fully ON and OFF.",
           "c3": "The user found each requested switch by touch without help.",
           "c4": "The user knows that switches without a sticker are unused or unknown.",
           "note": "AI only found the positions of the switches. What each switch controls was entered and checked by a person."},
    "hi": {"title": "स्पर्श – इंस्टॉलेशन गाइड", "board": "आपका स्विचबोर्ड (सीधी की गई फ़ोटो)",
           "sw": "स्विच", "where": "बोर्ड पर कहाँ", "ctrl": "क्या चलाता है", "cap": "कौन सा स्टिकर", "feel": "छूने पर कैसा",
           "row": "पंक्ति", "from_left": "बाएँ से", "steps": "कैसे लगाएँ", "legend": "स्पर्श संकेत सूची",
           "check": "उपयोगकर्ता के साथ अंतिम जाँच", "caps": "ज़रूरी स्टिकर",
           "s1": "हर स्विच को सूखे कपड़े से साफ़ करें। पानी न लगाएँ, स्विच प्लेट न खोलें।",
           "s2": "स्विच को सूखे कपड़े से साफ़ करें। स्टिकर का कागज़ हटाकर उसे रॉकर के ऊपरी हिस्से पर 10 सेकंड दबाएँ।",
           "s3": "नीचे दी गई तालिका के क्रम में स्टिकर लगाएँ (पहले S1) और हर एक पर टिक करें।",
           "s4": "हर स्विच एक बार दबाएँ: स्टिकर से स्विच का चलना नहीं रुकना चाहिए।",
           "s5": "उपयोगकर्ता से कहें कि आप जो नाम बोलें, वह स्विच छूकर ढूँढें।",
           "c1": "हर स्टिकर मज़बूती से लगा है।", "c2": "हर स्विच पूरी तरह ON/OFF होता है।",
           "c3": "उपयोगकर्ता ने हर स्विच बिना मदद के छूकर ढूँढा।", "c4": "बिना स्टिकर वाले स्विच अप्रयुक्त/अज्ञात हैं – यह उपयोगकर्ता जानते हैं।",
           "note": "AI ने केवल स्विच की जगह पहचानी। कौन सा स्विच क्या चलाता है – यह एक व्यक्ति ने भरा और जाँचा।"},
}


def _ordinal(n):
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def annotated_board(plate_img, mapping):
    vis = plate_img.copy()
    for s in mapping["switches"]:
        b = s["box"]
        cv2.rectangle(vis, (b[0], b[1]), (b[2], b[3]), (40, 40, 40), 3)
        cv2.rectangle(vis, (b[0], b[1] - 26), (b[0] + 44, b[1]), (40, 40, 40), -1)
        cv2.putText(vis, s["switch"], (b[0] + 4, b[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    ok, buf = cv2.imencode(".png", vis)
    return base64.b64encode(buf.tobytes()).decode()


def build_guide(plate_img, mapping, lang="en", household=""):
    t = T.get(lang, T["en"])
    img64 = annotated_board(plate_img, mapping)
    rows = []
    for s in mapping["switches"]:
        v = cap_for(s["function"])
        fname = v["name_hi"] if lang == "hi" else v["name_en"]
        if s.get("custom_label"):
            fname += f" — {html.escape(s['custom_label'])}"
        where = (f"{t['row']} {s['row']}, {s['position_in_row']} {t['from_left']}" if lang == "hi"
                 else f"{t['row']} {s['row']}, {_ordinal(s['position_in_row'])} {t['from_left']}")
        rows.append(f"<tr><td class='sw'>{s['switch']}</td><td>{where}</td><td>{fname}</td>"
                    f"<td>{v['cap_id'] or '—'}</td><td class='ic'>{svg_symbol(v['symbol'], 34)}</td>"
                    f"<td>{v['touch_hint'] if lang == 'en' else ''}</td><td class='tick'>☐</td></tr>")
    legend = "".join(
        f"<div class='lg'>{svg_symbol(v['symbol'], 90)}<div><b>{v['name_hi'] if lang == 'hi' else v['name_en']}</b><br>"
        f"<span>{v['touch_hint'] if lang == 'en' else ''}</span></div></div>"
        for k, v in VOCABULARY.items() if v["symbol"])
    caps = ", ".join(f"{k} × {n}" for k, n in mapping["caps_needed"].items()) or "—"
    today = datetime.date.today().isoformat()
    return f"""<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8"><title>{t['title']}</title>
<style>
body{{font-family:'Segoe UI',Roboto,'Noto Sans Devanagari',sans-serif;max-width:900px;margin:24px auto;color:#111;padding:0 16px}}
h1{{font-size:26px;margin:0}} h2{{font-size:19px;border-bottom:2px solid #111;padding-bottom:4px;margin-top:28px}}
.meta{{color:#444;font-size:13px}} img.board{{width:100%;border:1px solid #999;border-radius:6px}}
table{{border-collapse:collapse;width:100%;font-size:15px}} td,th{{border:1px solid #888;padding:6px 8px;text-align:left;vertical-align:middle}}
th{{background:#eee}} td.sw{{font-weight:700;font-size:18px}} td.tick{{font-size:22px;text-align:center}}
ol li,ul li{{margin:6px 0;font-size:15px}} .note{{background:#fff7e0;border-left:4px solid #e0a800;padding:8px 12px;font-size:14px}}
.legend{{page-break-before:always}} .lg{{display:flex;align-items:center;gap:22px;border:2px solid #111;border-radius:10px;padding:12px 18px;margin:12px 0;font-size:24px}}
.lg span{{font-size:16px;color:#333}} @media print{{button{{display:none}}}}
</style></head><body>
<h1>{t['title']}</h1><div class="meta">{html.escape(household)} · {today} · session {mapping['session']} · vocabulary {VOCABULARY_VERSION}</div>
<p class="note">{t['note']}</p>
<h2>{t['board']}</h2><img class="board" src="data:image/png;base64,{img64}" alt="Numbered switchboard">
<h2>{t['caps']}: {caps}</h2>
<table><tr><th>{t['sw']}</th><th>{t['where']}</th><th>{t['ctrl']}</th><th>{t['cap']}</th><th></th><th>{t['feel']}</th><th>✓</th></tr>{''.join(rows)}</table>
<h2>{t['steps']}</h2><ol><li>{t['s1']}</li><li>{t['s2']}</li><li>{t['s3']}</li><li>{t['s4']}</li><li>{t['s5']}</li></ol>
<h2>{t['check']}</h2><ul><li>☐ {t['c1']}</li><li>☐ {t['c2']}</li><li>☐ {t['c3']}</li><li>☐ {t['c4']}</li></ul>
<div class="legend"><h2>{t['legend']}</h2>{legend}</div>
<button onclick="window.print()">Print</button></body></html>"""
