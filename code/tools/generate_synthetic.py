"""
SPARSH - synthetic switchboard image generator.

Why this exists: before we had enough real photos of hostel/home switchboards,
we needed a labelled dataset with *known* ground truth to (a) develop the
detector, (b) stress-test it under controlled lighting / angle / blur
conditions and (c) train the small patch verifier.

IMPORTANT: synthetic results are NOT a substitute for real-photo evaluation.
Every number produced from this data is reported as "synthetic benchmark".
Real photos are evaluated separately with tools/evaluate_detector.py --real.

Each image models an Indian modular plate: a row (or two rows) of 1-module
rocker switches mixed with distractors that a detector must NOT call a switch:
2-module 3-pin sockets, fan-regulator knobs, indicator modules, and blank
cover modules (the hardest distractor - same size and shape as a switch).

Output: <out>/<split>/img_XXXX.jpg + <out>/<split>/annotations.json
"""
import argparse
import json
import os
import random

import cv2
import numpy as np

CONDITIONS = ["normal", "dim", "uneven_light", "angled", "blur", "dark_plate"]
# held-out STRESS conditions: never seen in training, used only to probe failure modes
STRESS = ["glare", "combined", "far_small"]

PLATE_COLOURS = {
    "white": (238, 240, 242),
    "ivory": (215, 230, 238),
    "grey": (175, 178, 180),
    "dark": (55, 55, 60),  # black/graphite plates (premium ranges)
}


def _rand_wall(h, w, rng):
    # typical Indian interior wall paints (BGR): off-white, cream, light yellow,
    # pista green, sky blue, beige, light pink, grey, light peach
    palette = [(235, 238, 240), (200, 228, 240), (170, 225, 240), (190, 225, 200), (235, 215, 180),
               (175, 200, 215), (205, 200, 240), (190, 190, 190), (180, 205, 235), (150, 160, 170)]
    base = np.array(rng.choice(palette), dtype=np.float32) + rng.uniform(-15, 10)
    wall = np.ones((h, w, 3), np.float32) * base
    noise = rng_normal(rng, (h // 16 + 1, w // 16 + 1, 1), 5)
    noise = cv2.resize(noise, (w, h), interpolation=cv2.INTER_CUBIC)[..., None]
    wall += noise + rng_normal(rng, (h, w, 1), 2.5)
    return np.clip(wall, 0, 255)


def rng_normal(rng, shape, sigma):
    return np.random.default_rng(rng.randint(0, 10**9)).normal(0, sigma, shape).astype(np.float32)


def _shade(colour, delta):
    return tuple(int(np.clip(c + delta, 0, 255)) for c in colour)


def draw_switch(img, x, y, mw, mh, colour, rng):
    """1-module rocker switch. Returns rocker bbox (x0,y0,x1,y1)."""
    rw, rh = int(mw * 0.72), int(mh * 0.62)
    rx, ry = x + (mw - rw) // 2, y + int(mh * 0.16)
    dark = sum(colour) < 300
    edge = _shade(colour, 60 if dark else -70)
    # recess shadow around rocker
    cv2.rectangle(img, (rx - 2, ry - 2), (rx + rw + 2, ry + rh + 2), _shade(colour, -35 if not dark else 25), -1)
    up = rng.random() < 0.5  # which half is pressed
    top_c = _shade(colour, 8 if up else -14)
    bot_c = _shade(colour, -14 if up else 8)
    cv2.rectangle(img, (rx, ry), (rx + rw, ry + rh // 2), top_c, -1)
    cv2.rectangle(img, (rx, ry + rh // 2), (rx + rw, ry + rh), bot_c, -1)
    cv2.rectangle(img, (rx, ry), (rx + rw, ry + rh), edge, 2)
    cv2.line(img, (rx + 3, ry + rh // 2), (rx + rw - 3, ry + rh // 2), _shade(colour, -45 if not dark else 45), 1)
    # ON marker: small red line or dot on many Indian switches
    if rng.random() < 0.7:
        mx = rx + rw // 2
        cv2.line(img, (mx - 4, ry + 8), (mx + 4, ry + 8), (40, 40, 200), 2)
    # tiny indicator window below rocker on some brands
    if rng.random() < 0.4:
        cv2.circle(img, (x + mw // 2, y + int(mh * 0.87)), 3, (60, 60, 190) if rng.random() < .5 else _shade(colour, -40), -1)
    return (rx, ry, rx + rw, ry + rh)


def draw_blank(img, x, y, mw, mh, colour, rng):
    rw, rh = int(mw * 0.72), int(mh * 0.62)
    rx, ry = x + (mw - rw) // 2, y + int(mh * 0.16)
    # blank cover: flat, same footprint as a rocker, only a faint outline
    cv2.rectangle(img, (rx, ry), (rx + rw, ry + rh), _shade(colour, -18 if sum(colour) > 300 else 18), 1)


def draw_indicator(img, x, y, mw, mh, colour, rng):
    cx, cy = x + mw // 2, y + mh // 2
    cv2.circle(img, (cx, cy), int(mw * 0.18), _shade(colour, -50), 2)
    cv2.circle(img, (cx, cy), int(mw * 0.10), (50, 50, 210), -1)


def draw_socket(img, x, y, mw, mh, colour, rng):
    """2-module 3-pin (6A) socket."""
    w = 2 * mw
    cx, cy = x + w // 2, y + mh // 2
    r = int(min(w, mh) * 0.36)
    dark = sum(colour) < 300
    cv2.circle(img, (cx, cy), r, _shade(colour, -30 if not dark else 30), 2)
    hole = (25, 25, 25) if not dark else (10, 10, 10)
    cv2.circle(img, (cx, cy - int(r * 0.45)), max(3, r // 7), hole, -1)
    cv2.circle(img, (cx - int(r * 0.45), cy + int(r * 0.35)), max(3, r // 9), hole, -1)
    cv2.circle(img, (cx + int(r * 0.45), cy + int(r * 0.35)), max(3, r // 9), hole, -1)


def draw_regulator(img, x, y, mw, mh, colour, rng):
    w = 2 * mw
    cx, cy = x + w // 2, y + mh // 2
    r = int(min(w, mh) * 0.30)
    cv2.circle(img, (cx, cy), r + 4, _shade(colour, -40), -1)
    cv2.circle(img, (cx, cy), r, _shade(colour, -10), -1)
    ang = rng.uniform(0, 2 * np.pi)
    cv2.line(img, (cx, cy), (int(cx + r * 0.8 * np.cos(ang)), int(cy + r * 0.8 * np.sin(ang))), _shade(colour, -80), 3)
    for k in range(5):
        a = -np.pi * 0.75 + k * np.pi * 0.375
        cv2.circle(img, (int(cx + (r + 10) * np.cos(a)), int(cy + (r + 10) * np.sin(a))), 2, _shade(colour, -60), -1)


def random_layout(rng):
    """Returns list of rows; each row a list of component names. 1M=switch,blank,indicator; 2M=socket,regulator."""
    n_rows = 1 if rng.random() < 0.7 else 2
    modules = rng.choice([4, 6, 8, 8, 12]) if n_rows == 1 else rng.choice([4, 6, 8])
    rows = []
    for _ in range(n_rows):
        row, used = [], 0
        while used < modules:
            left = modules - used
            r = rng.random()
            if left >= 2 and r < 0.18:
                comp = "socket"
            elif left >= 2 and r < 0.28:
                comp = "regulator"
            elif r < 0.36:
                comp = "blank"
            elif r < 0.41:
                comp = "indicator"
            else:
                comp = "switch"
            row.append(comp)
            used += 2 if comp in ("socket", "regulator") else 1
        if "switch" not in row:
            row[0] = "switch"
        rows.append(row)
    return rows, modules


def render_board(rng, condition):
    mw = rng.randint(46, 64)  # module width in px (scale)
    mh = int(mw * rng.uniform(1.85, 2.05))
    rows, modules = random_layout(rng)
    margin_x, margin_y = int(mw * 0.6), int(mw * 0.5)
    pw = modules * mw + 2 * margin_x
    ph = len(rows) * mh + 2 * margin_y + (len(rows) - 1) * int(mh * 0.08)
    pname = "dark" if condition == "dark_plate" else rng.choice(["white", "white", "white", "ivory", "grey"])
    pcol = PLATE_COLOURS[pname]
    plate = np.ones((ph, pw, 3), np.uint8)
    plate[:] = pcol
    cv2.rectangle(plate, (0, 0), (pw - 1, ph - 1), _shade(pcol, -40 if pname != "dark" else 40), 3)
    # inner frame (decorative bezel)
    cv2.rectangle(plate, (margin_x // 2, margin_y // 2), (pw - margin_x // 2, ph - margin_y // 2), _shade(pcol, -12 if pname != "dark" else 12), 1)
    boxes, labels = [], []
    for ri, row in enumerate(rows):
        x = margin_x
        y = margin_y + ri * (mh + int(mh * 0.08))
        for comp in row:
            if comp == "switch":
                boxes.append(draw_switch(plate, x, y, mw, mh, pcol, rng)); labels.append("switch")
                x += mw
            elif comp == "blank":
                draw_blank(plate, x, y, mw, mh, pcol, rng); x += mw
            elif comp == "indicator":
                draw_indicator(plate, x, y, mw, mh, pcol, rng); x += mw
            elif comp == "socket":
                draw_socket(plate, x, y, mw, mh, pcol, rng); x += 2 * mw
            elif comp == "regulator":
                draw_regulator(plate, x, y, mw, mh, pcol, rng); x += 2 * mw
    meta = {"rows": rows, "modules": modules, "plate_colour": pname, "module_px": mw}
    return plate, boxes, meta


def compose(rng, condition, out_w=960, out_h=720):
    plate, boxes, meta = render_board(rng, condition)
    ph, pw = plate.shape[:2]
    fill = (0.22, 0.32) if condition == "far_small" else (0.62, 0.85)
    scale = min(out_w * rng.uniform(*fill) / pw, out_h * rng.uniform(fill[0] * 0.9, fill[1] * 0.95) / ph)
    plate = cv2.resize(plate, (int(pw * scale), int(ph * scale)), interpolation=cv2.INTER_AREA)
    boxes = [tuple(int(v * scale) for v in b) for b in boxes]
    ph, pw = plate.shape[:2]
    wall = _rand_wall(out_h, out_w, rng)
    # plate corners in output
    ox = rng.randint(int(0.05 * out_w), max(int(0.05 * out_w) + 1, out_w - pw - int(0.05 * out_w)))
    oy = rng.randint(int(0.05 * out_h), max(int(0.05 * out_h) + 1, out_h - ph - int(0.05 * out_h)))
    src = np.float32([[0, 0], [pw, 0], [pw, ph], [0, ph]])
    dst = src + np.float32([ox, oy])
    angled = condition in ("angled", "combined")
    jitter = 0.02 if not angled else 0.06
    rot = np.deg2rad(rng.uniform(-4, 4) if not angled else rng.uniform(-7, 7))
    c = dst.mean(axis=0)
    R = np.array([[np.cos(rot), -np.sin(rot)], [np.sin(rot), np.cos(rot)]], np.float32)
    dst = (dst - c) @ R.T + c
    dst += np.float32([[rng.uniform(-1, 1) * jitter * pw, rng.uniform(-1, 1) * jitter * ph] for _ in range(4)])
    if angled:  # keystone: one side shorter
        side = rng.choice([0, 1])
        k = rng.uniform(0.05, 0.11) * ph
        if side == 0:
            dst[1, 1] += k; dst[2, 1] -= k
        else:
            dst[0, 1] += k; dst[3, 1] -= k
    H = cv2.getPerspectiveTransform(src, dst.astype(np.float32))
    warped = cv2.warpPerspective(plate, H, (out_w, out_h))
    mask = cv2.warpPerspective(np.ones((ph, pw), np.uint8) * 255, H, (out_w, out_h))
    # soft drop shadow
    sh = cv2.GaussianBlur(mask, (31, 31), 0).astype(np.float32) / 255.0
    sh = np.roll(np.roll(sh, 6, 0), 6, 1)
    img = wall * (1 - 0.25 * sh[..., None])
    m = (mask > 0)[..., None]
    img = np.where(m, warped.astype(np.float32), img)
    # GT boxes -> axis-aligned bbox of transformed rocker polygon
    gt = []
    for (x0, y0, x1, y1) in boxes:
        pts = np.float32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]).reshape(-1, 1, 2)
        tp = cv2.perspectiveTransform(pts, H).reshape(-1, 2)
        gt.append([float(tp[:, 0].min()), float(tp[:, 1].min()), float(tp[:, 0].max()), float(tp[:, 1].max())])
    # photometric conditions
    yy, xx = np.mgrid[0:out_h, 0:out_w].astype(np.float32)
    if condition in ("dim", "combined"):
        img = img * rng.uniform(0.30, 0.45)
        img += rng_normal(rng, img.shape, 7)
    if condition == "uneven_light":
        ang = rng.uniform(0, 2 * np.pi)
        g = (np.cos(ang) * xx / out_w + np.sin(ang) * yy / out_h)
        g = (g - g.min()) / (g.max() - g.min() + 1e-6)
        img = img * (0.35 + 0.85 * g)[..., None]
        # hard shadow blob (hand / door frame)
        cx, cy = rng.randint(0, out_w), rng.randint(0, out_h)
        blob = np.exp(-(((xx - cx) / (out_w * 0.25)) ** 2 + ((yy - cy) / (out_h * 0.35)) ** 2))
        img = img * (1 - 0.45 * blob)[..., None]
    if condition in ("blur", "combined"):
        k = rng.choice([7, 9, 11]) if condition == "blur" else 5
        img = cv2.GaussianBlur(img, (k, k), 0)
    if condition == "glare":  # flash reflection on a glossy plate
        pc = np.mean(dst, axis=0)
        cx, cy = pc[0] + rng.uniform(-0.3, 0.3) * pw, pc[1] + rng.uniform(-0.3, 0.3) * ph
        blob = np.exp(-(((xx - cx) / (pw * 0.18)) ** 2 + ((yy - cy) / (ph * 0.22)) ** 2))
        img = img + (255 * 0.95 * blob)[..., None]
    # every image: sensor noise + slight blur + jpeg
    img = img + rng_normal(rng, img.shape, 3.0)
    img = np.clip(img, 0, 255).astype(np.uint8)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    ok, enc = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, rng.randint(70, 92)])
    img = cv2.imdecode(enc, cv2.IMREAD_COLOR)
    meta.update({"condition": condition, "plate_corners": dst.tolist()})
    return img, gt, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/synthetic")
    ap.add_argument("--train", type=int, default=360)
    ap.add_argument("--val", type=int, default=120)
    ap.add_argument("--test", type=int, default=240)
    ap.add_argument("--seed", type=int, default=364)  # BITS F364 :)
    ap.add_argument("--stress", type=int, default=0, help="generate a held-out stress split instead")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    if a.stress:
        d = os.path.join(a.out, "stress"); os.makedirs(d, exist_ok=True); anns = []
        for i in range(a.stress):
            cond = STRESS[i % len(STRESS)]
            img, gt, meta = compose(rng, cond)
            fn = f"img_{i:04d}.jpg"; cv2.imwrite(os.path.join(d, fn), img)
            anns.append({"file": fn, "switch_boxes": gt, **meta})
        json.dump(anns, open(os.path.join(d, "annotations.json"), "w"))
        print("stress", a.stress, "->", d); return
    for split, n in [("train", a.train), ("val", a.val), ("test", a.test)]:
        d = os.path.join(a.out, split)
        os.makedirs(d, exist_ok=True)
        anns = []
        for i in range(n):
            cond = CONDITIONS[i % len(CONDITIONS)]  # balanced conditions
            img, gt, meta = compose(rng, cond)
            fn = f"img_{i:04d}.jpg"
            cv2.imwrite(os.path.join(d, fn), img)
            anns.append({"file": fn, "switch_boxes": gt, **meta})
        with open(os.path.join(d, "annotations.json"), "w") as f:
            json.dump(anns, f)
        print(split, n, "images ->", d)


if __name__ == "__main__":
    main()
