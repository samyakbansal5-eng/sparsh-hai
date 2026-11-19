"""
Train the Stage-2 patch verifier on the TRAIN split, tune C on VAL, never touch TEST.

A candidate (from Stage-1 proposals) is labelled positive if IoU >= 0.5 with a
ground-truth rocker. Output: models/verifier.pkl + results/verifier_training.json
"""
import json
import os
import sys

import cv2
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from sparsh.acquisition import load_image  # noqa
from sparsh.preprocessing import preprocess  # noqa
from sparsh.detection import propose, features, iou, FEATURE_NAMES  # noqa
from sparsh.verifier import Verifier, patch_vector  # noqa
from tools.evaluate_detector import gt_to_plate  # noqa


def collect(split_dir):
    anns = json.load(open(os.path.join(split_dir, "annotations.json")))
    X, F, y = [], [], []
    for a in anns:
        path = os.path.join(split_dir, a["file"])
        raw = cv2.imread(path)
        img = load_image(path)
        pp = preprocess(img)
        plate = pp["plate_img"]
        gts = gt_to_plate(a["switch_boxes"], pp["M"], img.shape[1] / raw.shape[1])
        for b in propose(plate):
            f = features(plate, b)
            best = max([iou(b, g) for g in gts] or [0])
            if 0.3 <= best < 0.5:
                continue  # ambiguous - skip
            X.append(patch_vector(plate, b, f))
            F.append(f)
            y.append(int(best >= 0.5))
    return np.array(X), np.array(F), np.array(y)


def main(data="data/synthetic"):
    Xtr, Ftr, ytr = collect(os.path.join(data, "train"))
    Xva, Fva, yva = collect(os.path.join(data, "val"))
    print("train candidates", len(ytr), "pos", ytr.sum(), "| val", len(yva), "pos", yva.sum())
    # feature means (used to sanity-check the hand-tuned heuristic)
    print("feature means  pos | neg")
    for i, n in enumerate(FEATURE_NAMES):
        print(f"  {n:20s} {Ftr[ytr == 1, i].mean():8.3f} | {Ftr[ytr == 0, i].mean():8.3f}")
    sc = StandardScaler().fit(Xtr)
    best = None
    log = []
    for C in [0.001, 0.003, 0.01, 0.03, 0.1, 0.3]:
        m = LogisticRegression(C=C, max_iter=3000, class_weight="balanced").fit(sc.transform(Xtr), ytr)
        p = m.predict_proba(sc.transform(Xva))[:, 1]
        ap = average_precision_score(yva, p)
        log.append({"C": C, "val_AP": round(ap, 4), "val_AUC": round(roc_auc_score(yva, p), 4)})
        print(log[-1])
        if best is None or ap > best[0]:
            best = (ap, C, m)
    os.makedirs("models", exist_ok=True)
    Verifier(best[2], sc).save("models/verifier.pkl")
    os.makedirs("results", exist_ok=True)
    json.dump({"train_candidates": int(len(ytr)), "train_pos": int(ytr.sum()), "val_candidates": int(len(yva)),
               "val_pos": int(yva.sum()), "C_search": log, "chosen_C": best[1],
               "feature_means_pos": dict(zip(FEATURE_NAMES, Ftr[ytr == 1].mean(0).round(3).tolist())),
               "feature_means_neg": dict(zip(FEATURE_NAMES, Ftr[ytr == 0].mean(0).round(3).tolist()))},
              open("results/verifier_training.json", "w"), indent=2)
    print("saved models/verifier.pkl with C =", best[1])


if __name__ == "__main__":
    main()
