"""
Evaluate switch detection (Module 3) - precision / recall / F1 / AP per condition.

Metric definitions (also in report section 'AI evaluation'):
  * A detection is a TRUE POSITIVE if IoU >= 0.5 with an unmatched ground-truth rocker.
  * Operating point = boxes the UI shows as switches (band High or Check, score >= 0.45).
  * Detection accuracy is NOT mapping accuracy: mapping accuracy can only be measured
    after the caregiver verifies which appliance each switch controls (Study B).

Usage:
  python tools/evaluate_detector.py --split test --mode heuristic
  python tools/evaluate_detector.py --split test --mode learned --model models/verifier.pkl
  python tools/evaluate_detector.py --real data/real            # real photos annotated via the app export
"""
import argparse
import json
import os
import sys
import time
from collections import defaultdict

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from sparsh.acquisition import load_image  # noqa: E402
from sparsh.preprocessing import preprocess  # noqa: E402
from sparsh.detection import detect, iou  # noqa: E402
from sparsh.verifier import Verifier  # noqa: E402

OP = 0.45


def gt_to_plate(gt_boxes, M, scale):
    out = []
    for b in gt_boxes:
        b = [v * scale for v in b]
        pts = np.float32([[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]]]).reshape(-1, 1, 2)
        tp = cv2.perspectiveTransform(pts, np.float32(M)).reshape(-1, 2)
        out.append([tp[:, 0].min(), tp[:, 1].min(), tp[:, 0].max(), tp[:, 1].max()])
    return out


def match(dets, gts, thr=0.5):
    """Greedy by score. Returns list of (score, is_tp) and n_gt."""
    used = set()
    res = []
    for d in sorted(dets, key=lambda d: -d["score"]):
        best, bi = 0, -1
        for i, g in enumerate(gts):
            if i in used:
                continue
            v = iou(d["box"], g)
            if v > best:
                best, bi = v, i
        if best >= thr:
            used.add(bi)
            res.append((d["score"], True))
        else:
            res.append((d["score"], False))
    return res, len(gts)


def average_precision(scored, n_gt):
    if n_gt == 0:
        return float("nan")
    scored = sorted(scored, key=lambda x: -x[0])
    tp = np.cumsum([s[1] for s in scored])
    fp = np.cumsum([not s[1] for s in scored])
    rec = tp / n_gt
    prec = tp / np.maximum(tp + fp, 1)
    # 101-point interpolation (COCO style)
    ap = 0
    for r in np.linspace(0, 1, 101):
        p = prec[rec >= r].max() if np.any(rec >= r) else 0
        ap += p / 101
    return float(ap)


def prf(scored, n_gt, thr=OP):
    tp = sum(1 for s, t in scored if t and s >= thr)
    fp = sum(1 for s, t in scored if (not t) and s >= thr)
    fn = n_gt - tp
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / n_gt if n_gt else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return dict(tp=tp, fp=fp, fn=fn, precision=p, recall=r, f1=f)


def run(data_dir, verifier=None, save_examples=None, limit=None):
    anns = json.load(open(os.path.join(data_dir, "annotations.json")))
    if limit:
        anns = anns[:limit]
    per = defaultdict(lambda: {"scored": [], "n_gt": 0, "imgs": 0, "plate_found": 0, "perfect": 0, "times": []})
    rows = []
    for k, a in enumerate(anns):
        path = os.path.join(data_dir, a["file"])
        raw = cv2.imread(path)
        t0 = time.perf_counter()
        img = load_image(path)
        scale = img.shape[1] / raw.shape[1]
        pp = preprocess(img)
        dets = detect(pp["plate_img"], verifier)
        dt = time.perf_counter() - t0
        gts = gt_to_plate(a["switch_boxes"], pp["M"], scale)
        scored, n = match(dets, gts)
        cond = a.get("condition", "real")
        for key in (cond, "ALL"):
            e = per[key]
            e["scored"] += scored
            e["n_gt"] += n
            e["imgs"] += 1
            e["plate_found"] += int(pp["plate_found"])
            e["times"].append(dt)
        m = prf(scored, n)
        perfect = m["fp"] == 0 and m["fn"] == 0
        per[cond]["perfect"] += perfect
        per["ALL"]["perfect"] += perfect
        rows.append({"file": a["file"], "condition": cond, **m, "n_gt": n, "plate_found": pp["plate_found"]})
        if save_examples and k < 24:
            vis = pp["plate_img"].copy()
            for g in gts:
                cv2.rectangle(vis, (int(g[0]), int(g[1])), (int(g[2]), int(g[3])), (255, 0, 0), 1)
            for d in dets:
                col = (0, 170, 0) if d["band"] == "high" else (0, 165, 255) if d["band"] == "check" else (0, 0, 220)
                b = d["box"]
                cv2.rectangle(vis, (b[0], b[1]), (b[2], b[3]), col, 2)
                cv2.putText(vis, f"{d['score']:.2f}", (b[0], b[1] - 3), 0, 0.45, col, 1)
            os.makedirs(save_examples, exist_ok=True)
            cv2.imwrite(os.path.join(save_examples, f"{cond}_{a['file']}"), vis)
    summary = {}
    for key, e in per.items():
        m = prf(e["scored"], e["n_gt"])
        summary[key] = {**{k: round(v, 4) if isinstance(v, float) else v for k, v in m.items()},
                        "AP50": round(average_precision(e["scored"], e["n_gt"]), 4),
                        "images": e["imgs"], "gt_switches": e["n_gt"],
                        "plate_found_rate": round(e["plate_found"] / e["imgs"], 3),
                        "images_fully_correct": round(e["perfect"] / e["imgs"], 3),
                        "mean_latency_s": round(float(np.mean(e["times"])), 3)}
    return summary, rows, per


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/synthetic")
    ap.add_argument("--split", default="test")
    ap.add_argument("--real", default=None, help="folder with real photos + annotations.json")
    ap.add_argument("--mode", default="heuristic", choices=["heuristic", "learned"])
    ap.add_argument("--model", default="models/verifier.pkl")
    ap.add_argument("--out", default="results")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    ver = Verifier.load(a.model) if a.mode == "learned" else None
    d = a.real or os.path.join(a.data, a.split)
    tag = ("real" if a.real else a.split) + "_" + a.mode
    summary, rows, per = run(d, ver, save_examples=os.path.join(a.out, "examples_" + tag), limit=a.limit)
    os.makedirs(a.out, exist_ok=True)
    json.dump(summary, open(os.path.join(a.out, f"detector_{tag}.json"), "w"), indent=2)
    import csv
    with open(os.path.join(a.out, f"detector_{tag}_per_image.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    # PR curve data
    pr = {}
    for key, e in per.items():
        sc = sorted(e["scored"], key=lambda x: -x[0])
        tp = np.cumsum([s[1] for s in sc]); fp = np.cumsum([not s[1] for s in sc])
        pr[key] = {"recall": (tp / max(e["n_gt"], 1)).tolist()[::3], "precision": (tp / np.maximum(tp + fp, 1)).tolist()[::3]}
    json.dump(pr, open(os.path.join(a.out, f"pr_{tag}.json"), "w"))
    print(f"== {tag} ==")
    for k in sorted(summary):
        s = summary[k]
        print(f"{k:13s} P={s['precision']:.3f} R={s['recall']:.3f} F1={s['f1']:.3f} AP50={s['AP50']:.3f} "
              f"plate={s['plate_found_rate']:.2f} perfect={s['images_fully_correct']:.2f} n={s['gt_switches']} t={s['mean_latency_s']}s")


if __name__ == "__main__":
    main()
