"""Error-driven refinement of the tactile code (v3, RQ2 support).

Reads P1 tactile-discrimination trials (presented_symbol, response_symbol), builds the confusion
matrix, and proposes the next vocabulary:
  1. a symbol is ACCEPTED if recall >= 0.90 and no single confusion > 0.10 (rule fixed in the protocol);
  2. each failing symbol is replaced by the tested candidate that is not yet used, has the best recall,
     and is least confused with the symbols being kept (lowest max pairwise confusion, both directions);
  3. output: ranked confusable pairs, the proposed v(n+1) mapping, and a short rationale per change.

  python tools/refine_vocabulary.py --data study/data/P1_tactile_discrimination.csv --out study/results
Simulated input (study/SIMULATED_data) is only a self-test; never report it.
"""
import argparse
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sparsh.tactile import VOCABULARY, VOCABULARY_VERSION  # noqa: E402

RECALL_MIN, CONF_MAX = 0.90, 0.10


def confusion(df):
    syms = sorted(set(df["presented_symbol"]) | set(df["response_symbol"]))
    cm = pd.crosstab(df["presented_symbol"], df["response_symbol"]).reindex(index=syms, columns=syms, fill_value=0)
    norm = cm.div(cm.sum(axis=1).replace(0, 1), axis=0)
    return cm, norm


def refine(df):
    cm, norm = confusion(df)
    syms = list(norm.index)
    recall = {s: float(norm.loc[s, s]) for s in syms}
    pairs = sorted(((float(norm.loc[a, b] + norm.loc[b, a]), a, b) for i, a in enumerate(syms) for b in syms[i + 1:]), reverse=True)
    current = {f: v["symbol"] for f, v in VOCABULARY.items() if v["symbol"]}
    used = set(current.values())

    def ok(s):
        if s not in norm.index:
            return False
        worst = max((norm.loc[s, o] for o in syms if o != s), default=0)
        return recall[s] >= RECALL_MIN and worst <= CONF_MAX

    proposal, notes = dict(current), []
    for func, sym in current.items():
        if ok(sym):
            continue
        keep = [v for f, v in proposal.items() if f != func]
        cands = [c for c in syms if c not in used and c not in keep]

        def cost(c):
            cross = max((norm.loc[c, k] + norm.loc[k, c] for k in keep if k in norm.index), default=0)
            return (cross, -recall[c])
        if cands:
            best = min(cands, key=cost)
            notes.append(f"{func}: '{sym}' failed (recall {recall.get(sym, 0):.2f}); replace with '{best}' "
                         f"(recall {recall[best]:.2f}, max confusion with kept symbols {cost(best)[0]:.2f})")
            proposal[func] = best; used.add(best)
        else:
            notes.append(f"{func}: '{sym}' failed but no untested candidate is left - test more candidates")
    return {"from_version": VOCABULARY_VERSION, "recall": recall,
            "top_confusable_pairs": [{"pair": [a, b], "two_way_confusion": round(c, 3)} for c, a, b in pairs[:5]],
            "current": current, "proposed": proposal, "changes": notes or ["all symbols pass - keep the current code"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="study/data/P1_tactile_discrimination.csv")
    ap.add_argument("--out", default="study/results")
    a = ap.parse_args()
    df = pd.read_csv(a.data)
    r = refine(df)
    r["SIMULATED"] = "SIMULATED" in a.data
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "vocabulary_refinement.json"), "w", encoding="utf-8") as f:
        json.dump(r, f, indent=2, ensure_ascii=False)
    print(json.dumps(r, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
