"""
SPARSH study analysis - runs on whatever REAL data is in study/data (copied from data_templates).

  python study/analysis.py --data study/data --out study/results
  python study/analysis.py --simulate     # pipeline self-test on SIMULATED data (watermarked, never report!)

Statistics plan (pre-registered in the protocol, section 9):
  Study A  within-subject (plain vs caps): per-participant median time + accuracy;
           Wilcoxon signed-rank (small n, non-normal times), effect size r = Z/sqrt(N),
           paired t-test + Cohen's dz reported alongside; bootstrap 95% CI of the median difference.
  Study B  (v3) within-subject, bare AI vs AI + confidence/reasons, ~25% seeded AI errors in both:
           over-reliance, under-reliance, residual wrong labels, time (same paired tests). Manual = descriptive only.
  Study C  accuracy on the unseen layout vs the learned layout; exact binomial CI per participant pool.
  P1       confusion matrix of presented vs perceived symbol; per-symbol recall.
Sighted blindfolded pilot rows are ALWAYS analysed separately from visually impaired participants.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

INK, ACC, GRN, RED = "#1f2a44", "#f4b942", "#1e8a5a", "#b54646"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#888"})


def watermark(fig, simulated):
    if simulated:
        fig.text(0.5, 0.5, "SIMULATED DATA\npipeline test – not results", ha="center", va="center", fontsize=26,
                 color="red", alpha=0.25, rotation=25, weight="bold")


def boot_ci(x, fn=np.median, n=4000, seed=1):
    rng = np.random.default_rng(seed)
    x = np.asarray(x)
    if len(x) < 2:
        return (float("nan"), float("nan"))
    b = [fn(rng.choice(x, len(x))) for _ in range(n)]
    return (float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5)))


def paired(a, b, label):
    """a, b: paired arrays (same participants). Returns dict of descriptive + inferential stats."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    out = {"measure": label, "n": int(len(a)), "median_A": float(np.median(a)), "median_B": float(np.median(b)),
           "mean_A": float(a.mean()), "mean_B": float(b.mean()), "sd_A": float(a.std(ddof=1)) if len(a) > 1 else None,
           "sd_B": float(b.std(ddof=1)) if len(b) > 1 else None, "median_diff": float(np.median(d)),
           "median_diff_CI95": boot_ci(d)}
    if len(a) >= 5 and np.any(d != 0):
        w = stats.wilcoxon(a, b, zero_method="wilcox", method="approx")
        z = stats.norm.isf(w.pvalue / 2)
        out.update({"wilcoxon_W": float(w.statistic), "wilcoxon_p": float(w.pvalue), "effect_r": float(z / np.sqrt(len(a)))})
        t = stats.ttest_rel(a, b)
        out.update({"paired_t": float(t.statistic), "paired_t_p": float(t.pvalue),
                    "cohens_dz": float(d.mean() / d.std(ddof=1)) if d.std(ddof=1) > 0 else None})
    else:
        out["note"] = "n < 5 or no differences: descriptive statistics only"
    return out


def study_A(df, out, sim):
    res = {}
    df = df.copy()
    df["condition"] = df["condition"].replace({"stickers": "caps", "refined": "caps"})
    for grp, g in df.groupby("group"):
        per = g.groupby(["participant_id", "condition"]).agg(time=("time_s", "median"), acc=("correct", "mean"),
                                                            conf=("confidence_1to7", "mean"),
                                                            help=("assistance_requested", "mean")).reset_index()
        wide = per.pivot(index="participant_id", columns="condition")
        if not {"plain", "caps"} <= set(per.condition):
            continue
        wide = wide.dropna()
        res[grp] = [paired(wide["time"]["plain"], wide["time"]["caps"], "median identification time (s)"),
                    paired(wide["acc"]["plain"], wide["acc"]["caps"], "accuracy (proportion correct)"),
                    paired(wide["conf"]["plain"], wide["conf"]["caps"], "confidence (1-7)")]
        fig, ax = plt.subplots(1, 2, figsize=(8, 3.4))
        for k, (col, lab) in enumerate([("time", "Median time to correct switch (s)"), ("acc", "Accuracy")]):
            for pid in wide.index:
                ax[k].plot([0, 1], [wide[col]["plain"][pid], wide[col]["caps"][pid]], color="#bbb", lw=1, zorder=1)
            ax[k].boxplot([wide[col]["plain"], wide[col]["caps"]], positions=[0, 1], widths=0.35, patch_artist=True,
                          boxprops=dict(facecolor="#eef0f6", color=INK), medianprops=dict(color=ACC, lw=2.5))
            ax[k].set_xticks([0, 1], ["Plain board", "Tactile code"]); ax[k].set_ylabel(lab)
        fig.suptitle(f"Study A – {grp} (n={len(wide)})", color=INK)
        watermark(fig, sim); fig.tight_layout(); fig.savefig(os.path.join(out, f"studyA_{grp}.png"), dpi=170); plt.close(fig)
    return res


def study_B(manual, app, out, sim):
    """v3 Study B (RQ1, core HAI): within-subject, 'ai' (confidence + reasons + forced review) vs
    'ai_bare' (same AI output, no confidence), both with ~25% seeded AI errors.
    Primary outcome: over-reliance = share of seeded errors NOT caught. Secondary: under-reliance,
    residual wrong labels, onboarding time. 'manual' rows (optional baseline) are summarised descriptively."""
    if app.empty:
        return {"note": "no app sessions yet"}
    res = {}
    a = app.copy()
    if "condition" not in a.columns:
        return {"note": "sessions need a condition column"}
    per = a.groupby(["participant", "condition"]).agg(
        over=("over_reliance", "mean"), under=("under_reliance", "mean"),
        resid=("residual_errors", "mean"), time=("onboarding_time_s", "median")).reset_index()
    wide = per.pivot(index="participant", columns="condition")
    if {"ai", "ai_bare"} <= set(per.condition):
        w = wide.dropna(subset=[("over", "ai"), ("over", "ai_bare")])
        res["n_paired"] = int(len(w))
        res["over_reliance"] = paired(w["over"]["ai_bare"], w["over"]["ai"], "over-reliance (share of seeded errors missed): bare vs confidence")
        res["under_reliance"] = paired(w["under"]["ai_bare"], w["under"]["ai"], "under-reliance (share of correct AI boxes rejected): bare vs confidence")
        res["residual_errors"] = paired(w["resid"]["ai_bare"], w["resid"]["ai"], "wrong labels left after review: bare vs confidence")
        res["time"] = paired(w["time"]["ai_bare"], w["time"]["ai"], "onboarding time (s): bare vs confidence")
        fig, ax = plt.subplots(1, 2, figsize=(8, 3.4))
        for k, (col, lab) in enumerate([("over", "Seeded AI errors missed (share)"), ("time", "Onboarding time (s)")]):
            for pid in w.index:
                ax[k].plot([0, 1], [w[col]["ai_bare"][pid], w[col]["ai"][pid]], color="#bbb", lw=1, zorder=1)
            ax[k].boxplot([w[col]["ai_bare"], w[col]["ai"]], positions=[0, 1], widths=0.35, patch_artist=True,
                          boxprops=dict(facecolor="#eef0f6", color=INK), medianprops=dict(color=ACC, lw=2.5))
            ax[k].set_xticks([0, 1], ["Bare AI", "AI + confidence"]); ax[k].set_ylabel(lab)
        fig.suptitle(f"Study B – installers (n={len(w)})", color=INK)
        watermark(fig, sim); fig.tight_layout(); fig.savefig(os.path.join(out, "studyB_reliance.png"), dpi=170); plt.close(fig)
    else:
        res["note"] = "need both 'ai' and 'ai_bare' sessions per participant"
    if not manual.empty:
        res["manual_baseline"] = {"n": int(len(manual)), "median_time_s": float(manual["onboarding_time_s"].median()),
                                  "mean_errors": float((manual["position_errors"] + manual["function_errors"]).mean())}
    return res


def study_C(df, out, sim):
    res = {}
    for grp, g in df.groupby("group"):
        k, n = int(g["correct"].sum()), len(g)
        ci = stats.binomtest(k, n).proportion_ci(confidence_level=0.95) if n else None
        res[grp] = {"trials": n, "correct": k, "accuracy": k / n if n else None,
                    "CI95": [ci.low, ci.high] if ci else None, "median_time_s": float(g["time_s"].median()) if n else None}
    return res


def pilot_P1(df, out, sim):
    syms = sorted(set(df["presented_symbol"]) | set(df["response_symbol"]))
    cm = pd.crosstab(df["presented_symbol"], df["response_symbol"]).reindex(index=syms, columns=syms, fill_value=0)
    rec = {s: float(cm.loc[s, s] / cm.loc[s].sum()) if cm.loc[s].sum() else None for s in syms}
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    norm = cm.div(cm.sum(axis=1).replace(0, 1), axis=0)
    ax.imshow(norm.values, cmap="YlOrBr", vmin=0, vmax=1)
    ax.set_xticks(range(len(syms)), syms, rotation=40, ha="right"); ax.set_yticks(range(len(syms)), syms)
    for i in range(len(syms)):
        for j in range(len(syms)):
            ax.text(j, i, int(cm.values[i, j]), ha="center", va="center", fontsize=8)
    ax.set_xlabel("Perceived by touch"); ax.set_ylabel("Presented"); ax.set_title("P1 – tactile confusion matrix", color=INK)
    watermark(fig, sim); fig.tight_layout(); fig.savefig(os.path.join(out, "P1_confusion.png"), dpi=170); plt.close(fig)
    return {"per_symbol_recall": rec, "overall_accuracy": float(np.trace(cm.values) / cm.values.sum()) if cm.values.sum() else None}


def questionnaires(df):
    out = {}
    sus = df[df.instrument == "SUS"]
    if not sus.empty:
        def sus_score(g):
            s = 0
            for _, r in g.iterrows():
                s += (r.score - 1) if int(r["item"]) % 2 == 1 else (5 - r.score)
            return s * 2.5
        per = sus.groupby(["participant_id", "condition"]).apply(sus_score, include_groups=False)
        out["SUS"] = {c: {"mean": float(v.mean()), "sd": float(v.std(ddof=1)) if len(v) > 1 else None, "n": int(len(v))}
                      for c, v in per.groupby(level=1)}
    tlx = df[df.instrument == "NASA-TLX"]
    if not tlx.empty:
        per = tlx.groupby(["participant_id", "condition"]).score.mean()
        out["NASA-TLX raw"] = {c: {"mean": float(v.mean()), "n": int(len(v))} for c, v in per.groupby(level=1)}
    return out


def simulate(path, seed=7):
    """Generates SIMULATED rows ONLY to test this script end to end. Folder is named SIMULATED_*."""
    rng = np.random.default_rng(seed)
    os.makedirs(path, exist_ok=True)
    rows = []
    for p in range(12):
        pid = f"SIM{p:02d}"
        for cond in ("plain", "caps"):
            for t in range(10):
                ok = rng.random() < (0.7 if cond == "plain" else 0.93)
                rows.append(dict(participant_id=pid, group="VI_blind", order=p % 2, condition=cond, board_layout="L1", trial=t,
                                 target_function="light", target_switch="S1", first_touched_switch="S1", selected_switch="S1",
                                 correct=int(ok), time_s=float(rng.gamma(4, 2.2 if cond == "plain" else 1.3)),
                                 assistance_requested=int(rng.random() < (0.2 if cond == "plain" else 0.05)),
                                 confidence_1to7=int(rng.integers(2, 6) if cond == "plain" else rng.integers(4, 8)), notes=""))
    pd.DataFrame(rows).to_csv(os.path.join(path, "A_identification_trials.csv"), index=False)
    man = [dict(participant_id=f"C{p:02d}", order=p % 2, board_layout="L2", start_time="", end_time="",
                onboarding_time_s=float(rng.normal(420, 80)), switches_recorded=7, switches_correct=7 - int(rng.integers(0, 3)),
                position_errors=int(rng.integers(0, 2)), function_errors=int(rng.integers(0, 2)), confidence_1to7=4, notes="") for p in range(10)]
    pd.DataFrame(man).to_csv(os.path.join(path, "B_onboarding_manual.csv"), index=False)
    app = []
    for p in range(22):
        for cond, p_catch in (("ai_bare", 0.45), ("ai", 0.75)):
            seeded = 2
            caught = int(rng.binomial(seeded, p_catch))
            real = 7
            rejected_real = int(rng.binomial(real, 0.03 if cond == "ai_bare" else 0.07))
            app.append(dict(session=f"s{p}{cond}", participant=f"C{p:02d}", condition=cond,
                            onboarding_time_s=float(rng.normal(150 if cond == "ai_bare" else 175, 30)),
                            ai_accepted=real - rejected_real, ai_rejected=rejected_real, seeded_errors=seeded,
                            seeded_errors_caught=caught, over_reliance=1 - caught / seeded,
                            under_reliance=rejected_real / real, residual_errors=seeded - caught))
    pd.DataFrame(app).to_csv(os.path.join(path, "study_B_sessions.csv"), index=False)
    syms = ["bump1", "bump2", "bump3", "texture", "bump4_square", "big_bump", "ridge_pair"]
    p1 = []
    for p in range(8):
        for s in syms:
            for r in range(4):
                resp = s if rng.random() < 0.85 else rng.choice(syms)
                p1.append(dict(participant_id=f"SIM{p}", group="VI_blind", session=1, trial=r, presented_symbol=s, response_symbol=resp,
                               correct=int(resp == s), time_s=float(rng.gamma(3, 1)), height_variant="v0", notes=""))
    pd.DataFrame(p1).to_csv(os.path.join(path, "P1_tactile_discrimination.csv"), index=False)
    print("SIMULATED data written to", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="study/data")
    ap.add_argument("--out", default="study/results")
    ap.add_argument("--simulate", action="store_true")
    a = ap.parse_args()
    sim = a.simulate
    if sim:
        a.data, a.out = "study/SIMULATED_data", "study/SIMULATED_results"
        simulate(a.data)
    os.makedirs(a.out, exist_ok=True)
    rd = lambda f: pd.read_csv(os.path.join(a.data, f)) if os.path.exists(os.path.join(a.data, f)) else pd.DataFrame()
    R = {"SIMULATED": sim}
    A = rd("A_identification_trials.csv")
    if not A.empty:
        R["study_A"] = study_A(A, a.out, sim)
    B1, B2 = rd("B_onboarding_manual.csv"), rd("study_B_sessions.csv")
    if not (B1.empty and B2.empty):
        R["study_B"] = study_B(B1, B2, a.out, sim)
    C = rd("C_generalisation_trials.csv")
    if not C.empty:
        R["study_C"] = study_C(C, a.out, sim)
    P = rd("P1_tactile_discrimination.csv")
    if not P.empty:
        R["pilot_P1"] = pilot_P1(P, a.out, sim)
    Q = rd("questionnaires.csv")
    if not Q.empty:
        R["questionnaires"] = questionnaires(Q)
    json.dump(R, open(os.path.join(a.out, "results.json"), "w"), indent=2, default=str)
    print(json.dumps(R, indent=1, default=str)[:3000])
    if len(R) == 1:
        print("No data found in", a.data, "- copy the templates to study/data and fill them during the sessions.")


if __name__ == "__main__":
    main()
