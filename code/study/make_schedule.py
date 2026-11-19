"""Generates the counterbalancing schedule + randomised trial lists for all studies.
python study/make_schedule.py --n 12 --out study/schedule.csv"""
import argparse
import csv
import random

FUNCS = ["light", "fan", "socket", "other"]
SHAPES = ["bump1", "bump2", "bump3", "texture", "bump4_square", "big_bump", "ridge_pair"]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=12); ap.add_argument("--out", default="study/schedule.csv")
    a = ap.parse_args()
    rows = []
    for i in range(1, a.n + 1):
        rng = random.Random(364 + i)
        a_order = ["plain", "stickers"] if i % 2 else ["stickers", "plain"]
        boards = ["L1", "L2"] if (i - 1) // 2 % 2 == 0 else ["L2", "L1"]
        b_order = ["ai_bare", "ai"] if i % 2 else ["ai", "ai_bare"]
        b_boards = ["photoset_S1", "photoset_S2"] if (i - 1) // 2 % 2 == 0 else ["photoset_S2", "photoset_S1"]
        trials = FUNCS * 2 + rng.sample(FUNCS, 2); rng.shuffle(trials)
        trials2 = FUNCS * 2 + rng.sample(FUNCS, 2); rng.shuffle(trials2)
        c_trials = FUNCS * 2; rng.shuffle(c_trials)
        lat = SHAPES[(i - 1) % 7:] + SHAPES[:(i - 1) % 7]
        p1 = []
        for blk in range(4):
            b = lat[:]; rng.shuffle(b); p1 += b
        rows.append({"participant": f"V{i:02d}", "A_order": "→".join(f"{c}@{bd}" for c, bd in zip(a_order, boards)),
                     "A_trials_cond1": " ".join(trials), "A_trials_cond2": " ".join(trials2), "C_trials_L5": " ".join(c_trials),
                     "caregiver": f"C{i:02d}", "B_order": "→".join(f"{c}@{bd}" for c, bd in zip(b_order, b_boards)),
                     "P1_order": " ".join(p1)})
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
