"""M6 - Tactile mapping generator.

The tactile vocabulary is DATA, not code, so the team (and later, users) can
change it after the discrimination pilot without touching the app.
v1 (below) is the current vocabulary; v0 (the proposal's) is kept for the P1
pilot comparison. v1 stays provisional until Study P1 (tactile discrimination
pilot) confirms the four shapes are not confused by touch.
"""

import os

# v3: the DEFAULT kit is off-the-shelf self-adhesive tactile stickers (no 3D printing, no wiring).
# The 3D-printed caps remain as an optional upgrade kit: set SPARSH_KIT=cap.
KIT = os.environ.get("SPARSH_KIT", "sticker")
VOCABULARY_VERSION = ("sticker-v1 (pending pilot P1)" if KIT == "sticker" else "cap-v1-lit-revised (pending pilot P1)")

# v0 = proposal vocabulary (kept for the P1 pilot comparison).
VOCABULARY_V0 = {
    "light": "dot", "fan": "line", "socket": "triangle", "other": "ring",
}
# v1 = revised after the literature review (decision D-05):
#  * ISO 24503:2011 already gives a dot = ON/start and a bar = stop/cancel meaning on
#    product controls -> a 'line' meaning FAN could be read as 'OFF'. Dot/bar dropped.
#  * Filled-round vs hollow-round (dot vs ring) are a known confusion pair at small sizes;
#    circle/triangle confusions reported by Wabinski et al. 2022 -> all symbols >= 10.5 mm
#    and each symbol has a DIFFERENT relief height (redundant cue, same paper).
#  * Large dome for LIGHT (10.5 mm, not an ISO 'dot' of 0.8-2 mm), cross for FAN
#    (evokes blades), triangle for SOCKET (triangle = hazard cue in ISO 24508's own example),
#    square for OTHER.
CAP_VOCABULARY = {
    "light": {"symbol": "dot", "cap_id": "CAP-L", "name_en": "Light", "name_hi": "बत्ती (लाइट)",
              "touch_hint": "one big smooth dome (highest, 1.5 mm)"},
    "fan": {"symbol": "cross", "cap_id": "CAP-F", "name_en": "Fan", "name_hi": "पंखा",
            "touch_hint": "a plus/cross, like fan blades (1.1 mm)"},
    "socket": {"symbol": "triangle", "cap_id": "CAP-S", "name_en": "Socket / plug point", "name_hi": "सॉकेट / प्लग",
               "touch_hint": "a triangle with soft corners (1.25 mm)"},
    "other": {"symbol": "square", "cap_id": "CAP-O", "name_en": "Other appliance", "name_hi": "अन्य उपकरण",
              "touch_hint": "a flat square (lowest, 0.9 mm)"},
    "unused": {"symbol": None, "cap_id": None, "name_en": "Not used / unknown", "name_hi": "अप्रयुक्त",
               "touch_hint": "no cap - leave plain"},
}

# v3 sticker vocabulary (decision D-05b). Built only from off-the-shelf parts:
#  * clear hemispherical bump-on stickers (about 10-12 mm) and the hook side of self-adhesive
#    hook-and-loop squares. Code = NUMBER of bumps (1/2/3) + one TEXTURE, because
#    (a) a bar is avoided (ISO 24503 bar = stop/cancel), (b) counting distinct raised points
#    is a separate cue from shape, (c) texture vs smooth is a strong, fast tactile contrast.
#  * Provisional until pilot P1; tools/refine_vocabulary.py proposes swaps from P1 confusion data.
STICKER_VOCABULARY = {
    "light": {"symbol": "bump1", "cap_id": "CAP-L", "name_en": "Light", "name_hi": "बत्ती (लाइट)",
              "touch_hint": "ONE smooth bump"},
    "fan": {"symbol": "bump2", "cap_id": "CAP-F", "name_en": "Fan", "name_hi": "पंखा",
            "touch_hint": "TWO bumps side by side"},
    "socket": {"symbol": "bump3", "cap_id": "CAP-S", "name_en": "Socket / plug point", "name_hi": "सॉकेट / प्लग",
               "touch_hint": "THREE bumps in a triangle"},
    "other": {"symbol": "texture", "cap_id": "CAP-O", "name_en": "Other appliance", "name_hi": "अन्य उपकरण",
              "touch_hint": "a ROUGH square (hook-and-loop)"},
    "unused": {"symbol": None, "cap_id": None, "name_en": "Not used / unknown", "name_hi": "अप्रयुक्त",
               "touch_hint": "no sticker - leave plain"},
}
# Off-the-shelf candidates the P1 pilot can swap in (all buyable, no fabrication).
STICKER_CANDIDATES = ["bump1", "bump2", "bump3", "texture", "bump4_square", "big_bump", "ridge_pair"]

VOCABULARY = STICKER_VOCABULARY if KIT == "sticker" else CAP_VOCABULARY
MARKER_WORD = {"en": "sticker" if KIT == "sticker" else "cap", "hi": "स्टिकर" if KIT == "sticker" else "कैप"}

# Shapes printed for the discrimination pilot (P1): the v1 four plus v0's line/ring
# and double_dot/square-type alternatives, so a confused v1 shape can be swapped.
# STL names keep geometric names (tile_dot = the light dome).
PILOT_CANDIDATES = ["dot", "line", "triangle", "ring", "cross", "double_dot", "square"]

FUNCTIONS = ["light", "fan", "socket", "other", "unused"]


def cap_for(function):
    return VOCABULARY.get(function, VOCABULARY["unused"])


def bill_of_caps(items):
    """Count caps needed for a confirmed mapping."""
    bom = {}
    for it in items:
        v = cap_for(it.get("function"))
        if v["cap_id"]:
            bom[v["cap_id"]] = bom.get(v["cap_id"], 0) + 1
    return bom


def svg_symbol(symbol, size=40, colour="#111"):
    """Small SVG icon of a tactile symbol for the screen / printed guide."""
    s, c = size, size / 2
    if symbol == "dot":
        body = f'<circle cx="{c}" cy="{c}" r="{s*0.18}" fill="{colour}"/>'
    elif symbol == "line":
        body = f'<rect x="{s*0.18}" y="{c - s*0.07}" width="{s*0.64}" height="{s*0.14}" rx="{s*0.05}" fill="{colour}"/>'
    elif symbol == "triangle":
        body = f'<polygon points="{c},{s*0.18} {s*0.82},{s*0.78} {s*0.18},{s*0.78}" fill="{colour}"/>'
    elif symbol == "ring":
        body = f'<circle cx="{c}" cy="{c}" r="{s*0.27}" fill="none" stroke="{colour}" stroke-width="{s*0.1}"/>'
    elif symbol == "cross":
        body = (f'<rect x="{s*0.2}" y="{c - s*0.06}" width="{s*0.6}" height="{s*0.12}" fill="{colour}"/>'
                f'<rect x="{c - s*0.06}" y="{s*0.2}" width="{s*0.12}" height="{s*0.6}" fill="{colour}"/>')
    elif symbol == "double_dot":
        body = (f'<circle cx="{s*0.32}" cy="{c}" r="{s*0.12}" fill="{colour}"/>'
                f'<circle cx="{s*0.68}" cy="{c}" r="{s*0.12}" fill="{colour}"/>')
    elif symbol in ("bump1", "big_bump"):
        r = s * (0.2 if symbol == "bump1" else 0.28)
        body = f'<circle cx="{c}" cy="{c}" r="{r}" fill="{colour}"/>'
    elif symbol == "bump2":
        body = (f'<circle cx="{s*0.3}" cy="{c}" r="{s*0.14}" fill="{colour}"/>'
                f'<circle cx="{s*0.7}" cy="{c}" r="{s*0.14}" fill="{colour}"/>')
    elif symbol == "bump3":
        body = (f'<circle cx="{c}" cy="{s*0.28}" r="{s*0.13}" fill="{colour}"/>'
                f'<circle cx="{s*0.28}" cy="{s*0.7}" r="{s*0.13}" fill="{colour}"/>'
                f'<circle cx="{s*0.72}" cy="{s*0.7}" r="{s*0.13}" fill="{colour}"/>')
    elif symbol == "bump4_square":
        body = "".join(f'<circle cx="{s*x}" cy="{s*y}" r="{s*0.11}" fill="{colour}"/>' for x in (0.3, 0.7) for y in (0.3, 0.7))
    elif symbol == "texture":
        dots = "".join(f'<circle cx="{s*(0.26+0.12*i)}" cy="{s*(0.26+0.12*j)}" r="{s*0.035}" fill="{colour}"/>' for i in range(5) for j in range(5))
        body = f'<rect x="{s*0.2}" y="{s*0.2}" width="{s*0.6}" height="{s*0.6}" rx="{s*0.05}" fill="none" stroke="{colour}" stroke-width="{s*0.04}"/>' + dots
    elif symbol == "ridge_pair":
        body = (f'<rect x="{s*0.22}" y="{s*0.3}" width="{s*0.12}" height="{s*0.4}" rx="{s*0.05}" fill="{colour}"/>'
                f'<rect x="{s*0.66}" y="{s*0.3}" width="{s*0.12}" height="{s*0.4}" rx="{s*0.05}" fill="{colour}"/>')
    elif symbol == "square":
        body = f'<rect x="{s*0.25}" y="{s*0.25}" width="{s*0.5}" height="{s*0.5}" fill="{colour}"/>'
    else:
        body = f'<text x="{c}" y="{c+4}" font-size="{s*0.3}" text-anchor="middle" fill="#888">—</text>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 {s} {s}">{body}</svg>'
