"""Learned verifier (Stage 2, 'learned' mode).

HOG descriptor of the candidate patch + the 10 explainable features from
detection.features -> standardised -> logistic regression.

We deliberately chose a small, inspectable model over a deep detector
(YOLO etc.) for the first iteration because (a) we had no real labelled data
at the start, (b) it trains in seconds on a laptop, (c) its failure modes are
easy to explain to a caregiver. See decision D-07/D-08 in the report.
"""
import pickle

import cv2
import numpy as np

PATCH = (32, 48)  # w, h
_hog = cv2.HOGDescriptor(_winSize=PATCH, _blockSize=(16, 16), _blockStride=(8, 8), _cellSize=(8, 8), _nbins=9)


def patch_vector(plate, box, f):
    g = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
    x0, y0, x1, y1 = [int(v) for v in box]
    p = cv2.resize(g[y0:y1, x0:x1], PATCH, interpolation=cv2.INTER_AREA)
    p = cv2.equalizeHist(p)
    h = _hog.compute(p).ravel()
    return np.concatenate([h, f])


class Verifier:
    def __init__(self, model=None, scaler=None):
        self.model, self.scaler = model, scaler

    def score(self, plate, box, f):
        v = patch_vector(plate, box, f).reshape(1, -1)
        return float(self.model.predict_proba(self.scaler.transform(v))[0, 1])

    def save(self, path):
        with open(path, "wb") as fh:
            pickle.dump({"model": self.model, "scaler": self.scaler}, fh)

    @staticmethod
    def load(path):
        with open(path, "rb") as fh:
            d = pickle.load(fh)
        return Verifier(d["model"], d["scaler"])
