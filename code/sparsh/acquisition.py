"""M1 - Image acquisition: load a photo from disk/bytes and run basic quality checks
so the caregiver gets *actionable* feedback ("too dark, switch on the room light")
instead of a silent bad detection."""
import cv2
import numpy as np

MAX_SIDE = 1024


def load_image(data):
    """data: file path or raw bytes. Returns BGR image resized so max side <= MAX_SIDE."""
    if isinstance(data, (bytes, bytearray)):
        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    else:
        img = cv2.imread(str(data), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not read the image. Please upload a JPG or PNG photo.")
    h, w = img.shape[:2]
    s = MAX_SIDE / max(h, w)
    if s < 1:
        img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return img


def quality_report(img):
    """Cheap, explainable checks. Returns list of (level, message)."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    issues = []
    mean = float(g.mean())
    sharp = float(cv2.Laplacian(g, cv2.CV_64F).var())
    if mean < 60:
        issues.append(("warn", "Photo looks dark. Turning on the room light or phone flash usually helps."))
    if mean > 225:
        issues.append(("warn", "Photo looks over-exposed. Avoid pointing the flash straight at a glossy plate."))
    if sharp < 8:
        issues.append(("warn", "Photo looks blurry. Hold the phone steady and tap to focus on the board."))
    return issues, {"brightness": round(mean, 1), "sharpness": round(sharp, 1)}
