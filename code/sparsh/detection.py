"""M3 - Switch detection.

Two-stage design (decision D-07 in the decision log):
  Stage 1  Proposal: classical CV (multi-threshold edges + contours) finds every
           rectangle that *could* be a rocker. Tuned for recall - it is cheap
           for a human to reject a wrong box, expensive to notice a missing one.
  Stage 2  Scoring: each candidate gets a confidence in [0,1].
             - "heuristic" mode: hand-designed, explainable features
             - "learned" mode: HOG + feature vector -> logistic regression
               (sparsh/verifier.py), trained on the training split only.
The confidence is shown to the caregiver as High / Check / Low bands - never as
a fake-precise percentage (see HAI design rationale in the report).
"""
import cv2
import numpy as np

TARGET_ASPECT = 1.55  # rocker height / width on common Indian 1M switches (measured on our synthetic + reference boards)


def iou(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x1 - x0) * max(0, y1 - y0)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def _contain(a, b):
    """fraction of b inside a"""
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x1 - x0) * max(0, y1 - y0)
    return inter / max(1e-6, (b[2] - b[0]) * (b[3] - b[1]))


def propose(plate):
    """Stage 1: return list of candidate boxes (x0,y0,x1,y1) in plate coords."""
    H, W = plate.shape[:2]
    g = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
    g = cv2.GaussianBlur(g, (3, 3), 0)
    maps = []
    med = float(np.median(g))
    for lo, hi in [(0.33 * med, 0.66 * med), (15, 45), (30, 90), (60, 150)]:
        e = cv2.Canny(g, max(5, lo), max(15, hi))
        maps.append(cv2.morphologyEx(e, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)))
    at = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 4)
    maps.append(cv2.morphologyEx(at, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)))
    plate_area = H * W
    boxes = []
    for m in maps:
        cnts, _ = cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            x, y, w, h = cv2.boundingRect(c)
            if w < 8 or h < 12:
                continue
            frac = (w * h) / plate_area
            if frac < 0.004 or frac > 0.20:
                continue
            asp = h / w
            if asp < 1.05 or asp > 2.6:
                continue
            boxes.append((x, y, x + w, y + h))
    # de-duplicate near-identical boxes
    boxes = sorted(set(boxes), key=lambda b: -(b[2] - b[0]) * (b[3] - b[1]))
    keep = []
    for b in boxes:
        if all(iou(b, k) < 0.85 for k in keep):
            keep.append(b)
    return keep


_cache = {}


def _gray_cache(plate):
    key = id(plate)
    if key not in _cache:
        _cache.clear()
        g = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
        g = cv2.bilateralFilter(g, 7, 30, 7)  # suppress sensor noise amplified by CLAHE in dim photos
        _cache[key] = g.astype(np.float32)
    return _cache[key]


def features(plate, box):
    """Explainable features for one candidate. Order matters (used by verifier)."""
    g = _gray_cache(plate)
    x0, y0, x1, y1 = [int(v) for v in box]
    patch = g[y0:y1, x0:x1]
    h, w = patch.shape
    asp = h / max(w, 1)
    # edge strength along the border (rockers have a clear outline / recess shadow)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)
    # contrast normalisation: dim photos have weak absolute gradients, so express edge
    # strength relative to this plate's own gradient distribution
    norm = 100.0 / (float(np.percentile(mag, 90)) + 1.0)
    mag = mag * norm
    gy = gy * norm
    t = 2
    border = np.concatenate([mag[y0:y0 + t, x0:x1].ravel(), mag[y1 - t:y1, x0:x1].ravel(),
                             mag[y0:y1, x0:x0 + t].ravel(), mag[y0:y1, x1 - t:x1].ravel()])
    inner = mag[y0 + 3:y1 - 3, x0 + 3:x1 - 3]
    border_strength = float(border.mean()) if border.size else 0.0
    inner_strength = float(inner.mean()) if inner.size else 0.0
    # rocker cue: the two halves differ in brightness and there's a horizontal pivot edge mid-way
    top, bot = patch[: h // 2], patch[h // 2:]
    half_contrast = abs(float(top.mean()) - float(bot.mean())) / (float(patch.std()) + 1.0)
    band = gy[y0 + int(0.4 * h): y0 + int(0.6 * h), x0 + 2: x1 - 2]
    mid_edge = float(np.abs(band).mean()) if band.size else 0.0
    # uniformity: blank covers are flat
    flat = float(patch.std())
    plate_mean = float(g.mean())
    rel_size = (w * h) / (g.shape[0] * g.shape[1])
    return np.array([asp, abs(np.log(asp / TARGET_ASPECT)), border_strength, inner_strength,
                     half_contrast, mid_edge, flat, rel_size, border_strength / (inner_strength + 1),
                     float(patch.mean()) / (plate_mean + 1)], np.float32)


FEATURE_NAMES = ["aspect", "aspect_dev", "border_edge", "inner_edge", "half_contrast", "mid_edge",
                 "texture", "rel_size", "border_inner_ratio", "rel_brightness"]


def heuristic_score(f):
    """Hand-tuned, fully explainable confidence (baseline)."""
    asp_dev, border, half, mid, ratio = f[1], f[2], f[4], f[5], f[8]
    z = (-4.0 * asp_dev + 0.02 * min(border, 250) + 1.5 * min(half, 2.0) + 0.03 * min(mid, 80) + 0.3 * min(ratio, 6) - 4.2)
    return float(1 / (1 + np.exp(-z)))


def nms(dets, thr=0.35):
    dets = sorted(dets, key=lambda d: -d["score"])
    keep = []
    for d in dets:
        ok = True
        for k in keep:
            if iou(d["box"], k["box"]) > thr or _contain(d["box"], k["box"]) > 0.7 or _contain(k["box"], d["box"]) > 0.7:
                ok = False
                break
        if ok:
            keep.append(d)
    return keep


def size_consistency(dets):
    """Switches on one board share a size; candidates far from the dominant size are down-weighted."""
    strong = [d for d in dets if d["score"] >= 0.5]
    if len(strong) < 2:
        return dets
    hs = np.median([d["box"][3] - d["box"][1] for d in strong])
    ws = np.median([d["box"][2] - d["box"][0] for d in strong])
    for d in dets:
        h = d["box"][3] - d["box"][1]
        w = d["box"][2] - d["box"][0]
        dev = abs(np.log(h / hs)) + abs(np.log(w / ws))
        d["score"] = float(d["score"] * np.exp(-1.6 * max(0, dev - 0.12)))
    return dets


def detect(plate, verifier=None, min_score=0.15):
    """Run both stages. Returns list of dicts: box, score, band, reasons."""
    cands = propose(plate)
    dets = []
    for b in cands:
        f = features(plate, b)
        s = verifier.score(plate, b, f) if verifier is not None else heuristic_score(f)
        dets.append({"box": [int(v) for v in b], "score": s, "feat": f})
    dets = nms(dets)
    dets = size_consistency(dets)
    dets = [d for d in dets if d["score"] >= min_score]
    for d in dets:
        d["band"] = band(d["score"])
        d["reasons"] = explain(d["feat"])
        del d["feat"]
    return dets


def band(score):
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "check"
    return "low"


def explain(f):
    """Plain-language cues shown on hover. Honest: these are what the AI 'looked at'."""
    r = []
    r.append("shape matches a switch" if f[1] < 0.25 else "shape is unusual for a switch")
    r.append("clear outline" if f[2] > 90 else "faint outline")
    r.append("rocker split visible" if f[4] > 0.5 or f[5] > 24 else "no rocker split seen (could be a blank cover)")
    return r
