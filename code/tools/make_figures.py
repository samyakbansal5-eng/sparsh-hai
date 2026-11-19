"""Builds every technical figure used in the reports / poster / slides from results/*.json.
Run after evaluate_detector.py. Output: figures/*.png"""
import json
import os
import sys

import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
R, F = os.path.join(ROOT, "results"), os.path.join(ROOT, "figures")
os.makedirs(F, exist_ok=True)
INK, MUTED, GRID = "#1f2a44", "#5b6478", "#e6e3dc"
C_H, C_L = "#3b5bdb", "#e8590c"  # heuristic, learned (validated palette: CVD ΔE 30)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#9a9a9a", "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True})
load = lambda n: json.load(open(os.path.join(R, n)))


def per_condition():
    th, tl = load("detector_test_heuristic.json"), load("detector_test_learned.json")
    sh, sl = load("detector_stress_heuristic.json"), load("detector_stress_learned.json")
    conds = ["normal", "dim", "uneven_light", "angled", "blur", "dark_plate"]
    stress = ["glare", "combined", "far_small"]
    labels = [c.replace("_", " ") for c in conds] + [f"{c.replace('_', ' ')}*" for c in stress]
    h = [th[c]["f1"] for c in conds] + [sh[c]["f1"] for c in stress]
    l = [tl[c]["f1"] for c in conds] + [sl[c]["f1"] for c in stress]
    x = np.arange(len(labels)); w = 0.38
    fig, ax = plt.subplots(figsize=(9.6, 3.9))
    b1 = ax.bar(x - w / 2 - 0.01, h, w, color=C_H, label="Stage-2 heuristic (hand-tuned)")
    b2 = ax.bar(x + w / 2 + 0.01, l, w, color=C_L, label="Stage-2 learned verifier (HOG + LR)")
    ax.axvspan(len(conds) - 0.5, len(labels) - 0.5, color="#f6f2ea", zorder=0)
    ax.text(len(conds) + 1, 1.05, "held-out stress conditions*", ha="center", color=MUTED, fontsize=9.5)
    for bars in (b1, b2):
        for r in bars:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.012, f"{r.get_height():.2f}", ha="center", fontsize=7.6, color=INK)
    ax.set_xticks(x, labels, rotation=0, fontsize=9); ax.set_ylim(0, 1.12); ax.set_ylabel("F1 at operating point (score ≥ 0.45)")
    ax.set_title("Switch detection F1 by photo condition (synthetic benchmark, IoU ≥ 0.5)", color=INK, loc="left", fontsize=12)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(F, "detector_f1_by_condition.png"), dpi=200); plt.close(fig)


def pr_curves():
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.7))
    for k, split in enumerate(["test", "stress"]):
        for mode, col in [("heuristic", C_H), ("learned", C_L)]:
            pr = load(f"pr_{split}_{mode}.json")["ALL"]
            s = load(f"detector_{split}_{mode}.json")["ALL"]
            ax[k].plot(pr["recall"], pr["precision"], color=col, lw=2, label=f"{mode} (AP50 {s['AP50']:.2f})")
        ax[k].set_xlim(0, 1.01); ax[k].set_ylim(0, 1.03); ax[k].set_xlabel("Recall"); ax[k].set_ylabel("Precision")
        ax[k].set_title(("Test split (6 conditions, 240 photos)" if split == "test" else "Stress split (unseen conditions, 90 photos)"), fontsize=10.5, color=INK)
        ax[k].legend(frameon=False, loc="lower left", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(F, "detector_pr_curves.png"), dpi=200); plt.close(fig)


def far_small_iteration():
    v10 = load("detector_stress_learned_v1.0.json")["far_small"]; v11 = load("detector_stress_learned.json")["far_small"]
    fig, ax = plt.subplots(figsize=(5.2, 3.3))
    names = ["Recall", "Plate found", "Images fully\ncorrect"]
    a = [v10["recall"], v10["plate_found_rate"], v10["images_fully_correct"]]
    b = [v11["recall"], v11["plate_found_rate"], v11["images_fully_correct"]]
    x = np.arange(3)
    ax.bar(x - 0.2, a, 0.38, color="#adb5c7", label="v1.0 (plate ≥ 5% of photo)")
    ax.bar(x + 0.2, b, 0.38, color=C_L, label="v1.1 (plate ≥ 1.5% of photo)")
    for i in range(3):
        ax.text(i - 0.2, a[i] + 0.02, f"{a[i]:.2f}", ha="center", fontsize=8.5); ax.text(i + 0.2, b[i] + 0.02, f"{b[i]:.2f}", ha="center", fontsize=8.5)
    ax.set_xticks(x, names); ax.set_ylim(0, 1.1); ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    ax.set_title("Fixing the 'far-away board' failure", color=INK, loc="left", fontsize=11.5)
    fig.tight_layout(); fig.savefig(os.path.join(F, "iteration_far_small.png"), dpi=200); plt.close(fig)


def example_strip():
    ex = os.path.join(R, "examples_test_learned")
    files = sorted(os.listdir(ex))
    pick = []
    for c in ["normal", "dim", "uneven_light", "angled", "blur", "dark_plate"]:
        fs = [f for f in files if f.startswith(c)]
        if fs:
            pick.append((c, fs[1] if len(fs) > 1 else fs[0]))
    tiles = []
    for c, f in pick:
        im = cv2.imread(os.path.join(ex, f)); h = 260; im = cv2.resize(im, (int(im.shape[1] * h / im.shape[0]), h))
        im = cv2.copyMakeBorder(im, 34, 6, 6, 6, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        cv2.putText(im, c.replace("_", " "), (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (68, 42, 31), 2)
        tiles.append(im)
    W = 1800
    rows, cur, cw = [], [], 0
    for t in tiles:
        if cw + t.shape[1] > W and cur:
            rows.append(cur); cur, cw = [], 0
        cur.append(t); cw += t.shape[1]
    rows.append(cur)
    out = []
    for r in rows:
        line = np.hstack(r); line = cv2.copyMakeBorder(line, 0, 0, 0, max(0, W - line.shape[1]), cv2.BORDER_CONSTANT, value=(255, 255, 255))
        out.append(line[:, :W])
    cv2.imwrite(os.path.join(F, "detection_examples.png"), np.vstack(out))


def synthetic_samples():
    d = os.path.join(ROOT, "data", "synthetic", "train")
    a = json.load(open(os.path.join(d, "annotations.json")))
    seen, tiles = set(), []
    for e in a:
        if e["condition"] in seen:
            continue
        seen.add(e["condition"])
        im = cv2.imread(os.path.join(d, e["file"]))
        for b in e["switch_boxes"]:
            cv2.rectangle(im, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (60, 170, 30), 2)
        im = cv2.resize(im, (480, 360))
        cv2.rectangle(im, (0, 0), (480, 34), (255, 255, 255), -1)
        cv2.putText(im, e["condition"].replace("_", " "), (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (68, 42, 31), 2)
        tiles.append(im)
    cv2.imwrite(os.path.join(F, "synthetic_dataset_samples.png"), np.vstack([np.hstack(tiles[:3]), np.hstack(tiles[3:6])]))


def summary_table():
    rows = []
    for split in ["test", "stress"]:
        for mode in ["heuristic", "learned"]:
            s = load(f"detector_{split}_{mode}.json")["ALL"]
            rows.append({"split": split, "mode": mode, **{k: s[k] for k in ["precision", "recall", "f1", "AP50", "images_fully_correct", "plate_found_rate", "mean_latency_s", "images", "gt_switches"]}})
    json.dump(rows, open(os.path.join(R, "detector_summary_table.json"), "w"), indent=2)
    for r in rows:
        print(r)


if __name__ == "__main__":
    per_condition(); pr_curves(); far_small_iteration(); example_strip(); synthetic_samples(); summary_table()
    print("figures ->", F)
