"""
SPARSH tactile caps - parametric generator (STL + preview renders).

Two mounting variants (decision D-11):
  TILE   15 x 15 mm adhesive tile, stuck on the upper half of the rocker with a
         removable gel/foam pad. Works on any rocker >= 15 mm wide. Default.
  SLEEVE friction-fit sleeve that slips over the whole rocker. Needs the rocker
         size measured with calipers (ROCKER_W/H below). No adhesive residue.

Symbol geometry follows the numeric guidance collected in our literature review
(ISO 24508:2019 summaries + 3D-printed tactile symbol studies):
  * symbol footprint >= 10 mm, line width 1.5-2.5 mm, relief 0.8-1.5 mm
  * each symbol gets a DIFFERENT relief height (redundant height cue)
  * rounded / domed profiles, no sharp edges (comfort, repeated use)
All dimensions in millimetres. Run:  python hardware/make_caps.py
"""
import os

import numpy as np
import trimesh
from shapely.geometry import Point, Polygon, box as sbox
from shapely.ops import unary_union

OUT = os.path.join(os.path.dirname(__file__), "stl")
RENDER = os.path.join(os.path.dirname(__file__), "renders")

# ---- parameters ----
TILE = 15.0          # tile side
BASE_T = 1.2         # base thickness
CORNER_R = 2.0
SYMBOL = 10.5        # nominal symbol footprint
ROCKER_W, ROCKER_H = 16.5, 27.0   # measure on the real board! (calipers)
FIT = 0.15           # friction-fit clearance per side
WALL = 1.0
SLEEVE_DEPTH = 3.2

V1 = ["dot", "cross", "triangle", "square"]   # light, fan, socket, other (decision D-05)
LEGEND = V1
HEIGHTS = {"dot": 1.5, "line": 1.0, "triangle": 1.25, "ring": 0.8,
           "cross": 1.1, "double_dot": 1.3, "square": 0.9}


def rounded_rect(w, h, r):
    return sbox(-w / 2 + r, -h / 2 + r, w / 2 - r, h / 2 - r).buffer(r, resolution=16)


def extrude(poly, height, z0=0.0):
    m = trimesh.creation.extrude_polygon(poly, height)
    m.apply_translation([0, 0, z0])
    return m


def dome(radius, height, z0):
    R = (radius ** 2 + height ** 2) / (2 * height)
    sph = trimesh.creation.icosphere(subdivisions=4, radius=R)
    sph.apply_translation([0, 0, z0 + height - R])
    slab = trimesh.creation.box(extents=[2 * R + 2, 2 * R + 2, height + 0.01])
    slab.apply_translation([0, 0, z0 + height / 2])
    return trimesh.boolean.intersection([sph, slab], engine="manifold")


def symbol_mesh(name, z0):
    h = HEIGHTS[name]
    s = SYMBOL
    if name == "dot":
        return dome(s * 0.5, h, z0)  # 10.5 mm footprint (ISO 24508: symbols >= 10 mm)
    if name == "double_dot":
        a, b = dome(s * 0.24, h, z0), dome(s * 0.24, h, z0)
        a.apply_translation([-s * 0.27, 0, 0]); b.apply_translation([s * 0.27, 0, 0])
        return trimesh.util.concatenate([a, b])
    if name == "line":
        p = sbox(-s / 2 + 1.25, -1.25, s / 2 - 1.25, 1.25).buffer(1.25, resolution=12)
    elif name == "triangle":
        r = s * 0.58
        pts = [(r * np.cos(a), r * np.sin(a)) for a in np.deg2rad([90, 210, 330])]
        p = Polygon(pts).buffer(-0.5).buffer(0.5, resolution=8)  # softened corners
    elif name == "ring":
        p = Point(0, 0).buffer(s / 2, resolution=48).difference(Point(0, 0).buffer(s / 2 - 1.8, resolution=48))
    elif name == "cross":
        w = 2.2
        p = unary_union([sbox(-s / 2, -w / 2, s / 2, w / 2), sbox(-w / 2, -s / 2, w / 2, s / 2)]).buffer(0.3)
    elif name == "square":
        p = rounded_rect(s * 0.95, s * 0.95, 1.0)  # ~10 mm square
    else:
        raise ValueError(name)
    return extrude(p, h, z0)


def tile(name):
    base = extrude(rounded_rect(TILE, TILE, CORNER_R), BASE_T)
    # orientation tick: small raised notch on the TOP edge so the cap is always mounted the same way up
    tick = extrude(sbox(-1.5, TILE / 2 - 1.4, 1.5, TILE / 2 - 0.6), 0.4, BASE_T)
    m = trimesh.boolean.union([base, symbol_mesh(name, BASE_T)], engine="manifold")
    if name != "triangle":
        m = trimesh.boolean.union([m, tick], engine="manifold")
    return m


def sleeve(name):
    iw, ih = ROCKER_W + 2 * FIT, ROCKER_H + 2 * FIT
    ow, oh = iw + 2 * WALL, ih + 2 * WALL
    outer = extrude(rounded_rect(ow, oh, 1.5), SLEEVE_DEPTH + BASE_T)
    cavity = extrude(rounded_rect(iw, ih, 1.0), SLEEVE_DEPTH + 0.01, -0.01)
    shell = trimesh.boolean.difference([outer, cavity], engine="manifold")
    sym = symbol_mesh(name, SLEEVE_DEPTH + BASE_T)
    sym.apply_translation([0, ih * 0.22, 0])  # symbol on the upper half of the rocker
    return trimesh.boolean.union([shell, sym], engine="manifold")


def legend_card():
    """60 x 90 mm card showing the four v1 symbols, used to teach the vocabulary."""
    base = extrude(rounded_rect(60, 90, 4), 1.6)
    parts = [base]
    for k, name in enumerate(LEGEND):
        m = symbol_mesh(name, 1.6)
        m.apply_translation([-14, 30 - k * 20, 0])
        parts.append(m)
        # raised index bars (1..4) next to each symbol so the card can be read without sight
        for j in range(k + 1):
            bar = extrude(sbox(6 + j * 4, -3, 8 + j * 4, 3), 0.8, 1.6)
            bar.apply_translation([0, 30 - k * 20, 0])
            parts.append(bar)
    return trimesh.boolean.union(parts, engine="manifold")


def raster(m, size=520, elev=38, azim=-62):
    """Tiny z-buffer renderer (orthographic, Lambert + rim light) - no GPU/display needed."""
    v = m.vertices - m.bounds.mean(axis=0)
    a, e = np.deg2rad(azim), np.deg2rad(elev)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.cos(np.pi / 2 - e), -np.sin(np.pi / 2 - e)], [0, np.sin(np.pi / 2 - e), np.cos(np.pi / 2 - e)]])
    v = v @ Rz.T @ Rx.T
    n = m.face_normals @ Rz.T @ Rx.T
    sc = 0.86 * size / (np.ptp(v[:, :2], axis=0).max())
    xy = v[:, :2] * sc + size / 2
    xy[:, 1] = size - xy[:, 1]
    z = v[:, 2]
    img = np.ones((size, size, 3)); zb = np.full((size, size), -1e9)
    L = np.array([-0.35, -0.55, 0.76]); L /= np.linalg.norm(L)
    fz = m.vertices[m.faces][:, :, 2].mean(1); fz = (fz - fz.min()) / (np.ptp(fz) + 1e-9)
    base = np.array([0.96, 0.72, 0.25])
    for f, nn, hz in zip(m.faces, n, fz):
        if nn[2] <= 0:
            continue
        p = xy[f]; zz = z[f]
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        (ax_, ay), (bx, by), (cx, cy) = p
        den = (by - cy) * (ax_ - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9:
            continue
        w0 = ((by - cy) * (X - cx) + (cx - bx) * (Y - cy)) / den
        w1 = ((cy - ay) * (X - cx) + (ax_ - cx) * (Y - cy)) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        Z = w0 * zz[0] + w1 * zz[1] + w2 * zz[2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        upd = inside & (Z > sub)
        sub[upd] = Z[upd]
        shade = (0.25 + 0.6 * max(nn @ L, 0)) * (0.78 + 0.32 * hz)
        img[y0:y1 + 1, x0:x1 + 1][upd] = np.clip(base * shade, 0, 1)
    return img


def render(meshes, titles, path, cols=4):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = int(np.ceil(len(meshes) / cols))
    fig, axs = plt.subplots(rows, cols, figsize=(3.0 * cols, 3.25 * rows), dpi=160)
    axs = np.atleast_1d(axs).ravel()
    for ax in axs:
        ax.axis("off")
    for ax, m, t in zip(axs, meshes, titles):
        ax.imshow(raster(m)); ax.set_title(t, fontsize=10.5, color="#1f2a44")
    plt.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True); os.makedirs(RENDER, exist_ok=True)
    report = []
    tiles, titles = [], []
    for name in HEIGHTS:
        m = tile(name)
        f = os.path.join(OUT, f"tile_{name}.stl"); m.export(f)
        report.append((f"tile_{name}", m.is_watertight, m.volume, m.bounds[1] - m.bounds[0]))
        tiles.append(m); titles.append(f"{name}  (relief {HEIGHTS[name]} mm)")
    for name in V1:
        m = sleeve(name)
        f = os.path.join(OUT, f"sleeve_{name}.stl"); m.export(f)
        report.append((f"sleeve_{name}", m.is_watertight, m.volume, m.bounds[1] - m.bounds[0]))
    lc = legend_card(); lc.export(os.path.join(OUT, "legend_card.stl"))
    report.append(("legend_card", lc.is_watertight, lc.volume, lc.bounds[1] - lc.bounds[0]))
    by = dict(zip(HEIGHTS, tiles))
    render([by[n] for n in ["dot", "line", "triangle", "ring"]], ["LIGHT – dot", "FAN – line", "SOCKET – triangle", "OTHER – ring"], os.path.join(RENDER, "caps_v0_proposal.png"))
    render([by[n] for n in V1], ["LIGHT – dome 1.5 mm", "FAN – cross 1.1 mm", "SOCKET – triangle 1.25 mm", "OTHER – square 0.9 mm"], os.path.join(RENDER, "caps_v1.png"))
    render(tiles, titles, os.path.join(RENDER, "pilot_candidates.png"))
    render([sleeve("dot"), sleeve("cross")], ["Sleeve variant – light", "Sleeve variant – fan"], os.path.join(RENDER, "sleeves.png"), cols=2)
    render([lc], ["Legend / learning card"], os.path.join(RENDER, "legend_card.png"), cols=1)
    # PLA density ~1.24 g/cm3; cost at INR 1,300/kg (Robu/Robocraze listing, Nov 2026)
    with open(os.path.join(OUT, "PRINT_REPORT.csv"), "w") as fh:
        fh.write("part,watertight,volume_mm3,size_x_mm,size_y_mm,size_z_mm,pla_grams,filament_cost_inr\n")
        for n, w, v, e in report:
            g = v / 1000 * 1.24
            fh.write(f"{n},{w},{v:.1f},{e[0]:.2f},{e[1]:.2f},{e[2]:.2f},{g:.2f},{g * 1.3:.2f}\n")
    for r in report:
        print(r[0], "watertight" if r[1] else "NOT WATERTIGHT", f"{r[2]:.0f} mm3", np.round(r[3], 2))


if __name__ == "__main__":
    main()
