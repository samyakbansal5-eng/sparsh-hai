"""M2 - Image processing: find the switch plate, straighten it (perspective
correction) and normalise lighting (CLAHE). If the plate can't be found we fall
back to the whole photo and SAY SO in the UI - we never fail silently."""
import cv2
import numpy as np


def _order(pts):
    pts = pts.reshape(4, 2).astype(np.float32)
    s, d = pts.sum(1), np.diff(pts, axis=1).ravel()
    return np.float32([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]])


def _edge_support(mag, quad, n=40):
    """Mean gradient magnitude sampled along the quad's sides (how 'real' its outline is)."""
    vals = []
    for i in range(4):
        p, q = quad[i], quad[(i + 1) % 4]
        for t in np.linspace(0.05, 0.95, n):
            x, y = p + t * (q - p)
            xi, yi = int(np.clip(x, 0, mag.shape[1] - 1)), int(np.clip(y, 0, mag.shape[0] - 1))
            vals.append(mag[max(0, yi - 2):yi + 3, max(0, xi - 2):xi + 3].max())
    return float(np.mean(vals))


def find_plate(img):
    """Return 4 ordered corners of the most plausible switch plate, or None.
    Candidate quadrilaterals come from contours at several adaptive edge thresholds;
    each is scored by size x rectangularity x how strongly its outline is supported
    by image gradients (a plate edge + its shadow is a strong, straight edge)."""
    h, w = img.shape[:2]
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(2, 2)).apply(g)
    g = cv2.bilateralFilter(g, 9, 40, 40)
    g = cv2.GaussianBlur(g, (5, 5), 0)
    mag = cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    ref = float(np.percentile(mag, 75)) + 1e-6
    best, best_score = None, 0
    for pct in (85, 92, 97):
        hi = float(np.percentile(mag, pct))
        e = cv2.Canny(g, 0.4 * hi, hi)
        e = cv2.dilate(e, np.ones((3, 3), np.uint8), 1)
        cnts, _ = cv2.findContours(e, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            hull = cv2.convexHull(c)
            a = cv2.contourArea(hull)
            if a < 0.015 * h * w or a > 0.85 * h * w:  # v1.1: was 0.05 - far-away boards were missed (stress test)
                continue
            approx = cv2.approxPolyDP(hull, 0.02 * cv2.arcLength(hull, True), True)
            if len(approx) != 4:
                approx = cv2.boxPoints(cv2.minAreaRect(hull))
            quad = _order(np.asarray(approx, np.float32))
            fill = a / (cv2.contourArea(quad) + 1e-6)
            if fill < 0.8 or not cv2.isContourConvex(quad.astype(np.int32)):
                continue
            support = _edge_support(mag, quad) / ref
            score = (a / (h * w)) ** 0.5 * min(fill, 1.0) * min(support, 4.0)
            if score > best_score:
                best, best_score = quad, score
    return best if best_score > 0.6 else None


def rectify(img, corners, target_h=420):
    tl, tr, br, bl = corners
    wpx = max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl))
    hpx = max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr))
    scale = target_h / max(hpx, 1)
    W, Hh = int(wpx * scale), int(hpx * scale)
    if W > 1400:  # very long plates
        s = 1400 / W
        W, Hh = 1400, int(Hh * s)
    dst = np.float32([[0, 0], [W, 0], [W, Hh], [0, Hh]])
    M = cv2.getPerspectiveTransform(corners, dst)
    return cv2.warpPerspective(img, M, (W, Hh)), M


def normalise_lighting(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(l)
    return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)


def preprocess(img):
    """Returns dict(plate_img, M (orig->plate), Minv, plate_found, corners)."""
    corners = find_plate(img)
    if corners is not None:
        plate, M = rectify(img, corners)
        found = True
    else:
        plate, M = img.copy(), np.eye(3, dtype=np.float32)
        found = False
    plate = normalise_lighting(plate)
    return {"plate_img": plate, "M": M, "Minv": np.linalg.inv(M), "plate_found": found,
            "corners": None if corners is None else corners.tolist()}
