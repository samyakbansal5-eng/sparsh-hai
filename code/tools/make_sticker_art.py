"""Illustrations of the v3 sticker code (for deck, poster, video). python tools/make_sticker_art.py"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

OUT = os.path.join(os.path.dirname(__file__), "..", "media", "assets")
ROCKER, EDGE, BUMP = "#f4f1ea", "#c9c2b3", "#e8a917"


def bump(ax, x, y, r):
    for k in range(14, 0, -1):  # radial shading -> reads as a raised dome
        f = k / 14
        c = np.array(matplotlib.colors.to_rgb(BUMP)) * (0.72 + 0.28 * (1 - f)) + 0.0
        ax.add_patch(Circle((x - r * 0.18 * (1 - f), y + r * 0.18 * (1 - f)), r * f, color=np.clip(c, 0, 1), lw=0))
    ax.add_patch(Circle((x - r * 0.35, y + r * 0.35), r * 0.22, color="white", alpha=0.55, lw=0))


def texture(ax, x, y, s):
    ax.add_patch(FancyBboxPatch((x - s / 2, y - s / 2), s, s, boxstyle="round,pad=0,rounding_size=0.04", fc="#d9c08a", ec="#a8894a", lw=2))
    rng = np.random.default_rng(3)
    for i in range(9):
        for j in range(9):
            px, py = x - s / 2 + (i + 0.5) * s / 9, y - s / 2 + (j + 0.5) * s / 9
            ax.plot([px - 0.012, px + 0.012], [py - 0.012 + rng.normal(0, .004), py + 0.012], color="#7a5f2a", lw=1.6)


def draw(ax, kind):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.08, 0.08), 0.84, 0.84, boxstyle="round,pad=0,rounding_size=0.08", fc=ROCKER, ec=EDGE, lw=3))
    if kind == "light":
        bump(ax, 0.5, 0.5, 0.17)
    elif kind == "fan":
        bump(ax, 0.32, 0.5, 0.13); bump(ax, 0.68, 0.5, 0.13)
    elif kind == "socket":
        bump(ax, 0.5, 0.7, 0.12); bump(ax, 0.29, 0.33, 0.12); bump(ax, 0.71, 0.33, 0.12)
    elif kind == "other":
        texture(ax, 0.5, 0.5, 0.48)


KINDS = [("light", "Light", "one bump"), ("fan", "Fan", "two bumps"), ("socket", "Socket", "three bumps"), ("other", "Other", "rough square")]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for k, _, _ in KINDS:
        fig = plt.figure(figsize=(3, 3), dpi=150); ax = fig.add_axes([0, 0, 1, 1]); draw(ax, k)
        fig.savefig(os.path.join(OUT, f"stk_{k}.png"), transparent=True); plt.close(fig)
    fig, axs = plt.subplots(1, 4, figsize=(11, 3), dpi=170)
    for ax, (k, n, d) in zip(axs, KINDS):
        draw(ax, k); ax.set_title(f"{n}\n{d}", fontsize=15, color="#1f2a44", fontweight="bold", pad=4)
    fig.savefig(os.path.join(OUT, "stickers_row.png"), transparent=False, facecolor="white", bbox_inches="tight", pad_inches=0.15); plt.close(fig)
    print("written to", OUT)
