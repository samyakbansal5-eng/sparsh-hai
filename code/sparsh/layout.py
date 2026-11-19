"""M4 - Layout generation: group detections into rows and number them the way a
person reads a board (top row first, left to right): S1, S2, ...
Numbering is stable after corrections: renumber() is called after every add/delete
so the caregiver never sees gaps like S1, S2, S4."""
import numpy as np


def assign_rows(boxes):
    if not boxes:
        return []
    cy = np.array([(b[1] + b[3]) / 2 for b in boxes])
    hs = np.array([b[3] - b[1] for b in boxes])
    order = np.argsort(cy)
    rows, cur, ref = [], [order[0]], cy[order[0]]
    thr = 0.5 * float(np.median(hs))
    for i in order[1:]:
        if abs(cy[i] - ref) > thr:
            rows.append(cur)
            cur = [i]
        else:
            cur.append(i)
        ref = float(np.mean(cy[cur]))
    rows.append(cur)
    row_of = [0] * len(boxes)
    for r, idxs in enumerate(rows):
        for i in idxs:
            row_of[i] = r
    return row_of


def renumber(items):
    """items: list of dicts with 'box'. Adds 'row', 'col', 'number', 'label' (S1..). Returns sorted list."""
    if not items:
        return items
    rows = assign_rows([it["box"] for it in items])
    for it, r in zip(items, rows):
        it["row"] = r
    items.sort(key=lambda it: (it["row"], (it["box"][0] + it["box"][2]) / 2))
    col = {}
    for n, it in enumerate(items, 1):
        it["col"] = col.get(it["row"], 0)
        col[it["row"]] = it["col"] + 1
        it["number"] = n
        it["label"] = f"S{n}"
    return items
