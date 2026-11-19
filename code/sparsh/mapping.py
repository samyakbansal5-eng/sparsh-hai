"""M5 - Human confirmation logic (the heart of the Human-AI interaction).

Design rules enforced here (not just in the UI), see report section 'HAI design':
  R1  AI output is a SUGGESTION. Every AI box starts 'pending'.
  R2  High-confidence boxes may be accepted in bulk, but 'check' / 'low' boxes
      must each be looked at individually (cognitive forcing, Buçinca et al. 2021).
  R3  The AI never assigns an appliance. Function is always human-entered.
  R4  A switch counts as VERIFIED only when the caregiver confirms they physically
      toggled it and saw what it controls.
  R5  Every action is undoable; corrections never force a restart.
  R6  Final confirmation is blocked until validation passes (or the caregiver
      explicitly overrides a non-blocking warning).
"""
import copy
import random
import time
import uuid

from . import layout
from .tactile import FUNCTIONS, cap_for, bill_of_caps


class Session:
    # v3 conditions:
    #   'ai'      = AI boxes WITH confidence bands + reasons + forced review of unsure boxes (Study B, treatment)
    #   'ai_bare' = the SAME AI boxes shown WITHOUT any confidence or reason (Study B, control; Brief #14 design)
    #   'manual'  = no AI at all (optional baseline / fallback when detection fails)
    CONDITIONS = ("ai", "ai_bare", "manual")

    def __init__(self, condition="ai", participant_id="", inject_errors=False, seed=None, inject_rate=0.25):
        self.id = uuid.uuid4().hex[:8]
        if condition not in self.CONDITIONS:
            raise ValueError("unknown condition")
        self.condition = condition
        self.inject_rate = float(inject_rate)
        self.participant_id = participant_id
        self.inject_errors = inject_errors
        self.rng = random.Random(seed)
        self.items = []
        self.history = []
        self.injected = []  # ids of deliberately wrong AI outputs (Study B / RQ4 reliance probe)
        self.removed_true = []  # boxes deliberately hidden from AI output
        self.confirmed = False
        self.meta = {}
        self.t_created = time.time()

    # ---------------- helpers ----------------
    def _snap(self):
        self.history.append(copy.deepcopy(self.items))
        if len(self.history) > 50:
            self.history.pop(0)

    def get(self, iid):
        for it in self.items:
            if it["id"] == iid:
                return it
        raise KeyError(iid)

    def _new(self, box, source, score=None, band=None, reasons=None):
        return {"id": uuid.uuid4().hex[:6], "box": [int(v) for v in box], "source": source,
                "score": None if score is None else round(float(score), 3), "band": band or "human",
                "reasons": reasons or [], "status": "accepted" if source == "human" else "pending",
                "function": None, "name": "", "verified": False}

    def _renumber(self):
        act = layout.renumber([i for i in self.items if i["status"] != "rejected"])
        rej = [i for i in self.items if i["status"] == "rejected"]
        for i in rej:
            i["label"] = "✕"
        self.items = act + rej

    # ---------------- AI input ----------------
    def load_detections(self, dets, plate_shape):
        if self.condition == "manual":
            self.items = []
            return
        # 'ai' and 'ai_bare' receive identical AI output; only the DISPLAY differs (see to_dict)
        items = [self._new(d["box"], "ai", d["score"], d["band"], d.get("reasons")) for d in dets]
        if self.inject_errors and items:
            items = self._inject(items, plate_shape)
        self.items = layout.renumber(items)

    # Planted false positives alternate between an 'unsure' and a 'fairly sure' band, so the
    # confidence display is informative but NOT perfect (real detectors are imperfectly calibrated).
    _FP_BANDS = [(0.58, "check", ["outline only partly visible", "could be a switch or a gap"]),
                 (0.86, "high", ["shape matches a switch", "clear outline"])]

    def _inject(self, items, plate_shape):
        """Study-only seeded errors (v3, Brief #14 design): about `inject_rate` of the AI's output is wrong.
        k = max(1, round(rate * n_true)) errors, split between planted false switches and hidden true
        switches (at least one of each when k >= 2). Participants are debriefed afterwards (see protocol)."""
        n_true = len(items)
        k = max(1, round(self.inject_rate * n_true))
        n_fp = (k + 1) // 2
        n_hide = k - n_fp if n_true >= 3 else 0
        H, W = plate_shape[:2]
        ws = sorted(it["box"][2] - it["box"][0] for it in items)[len(items) // 2]
        hs = sorted(it["box"][3] - it["box"][1] for it in items)[len(items) // 2]
        for j in range(n_fp):
            for _ in range(300):
                x = self.rng.randint(5, max(6, W - ws - 5))
                y = self.rng.randint(5, max(6, H - hs - 5))
                b = [x, y, x + ws, y + hs]
                if all(_overlap(b, it["box"]) == 0 for it in items):
                    score, band, why = self._FP_BANDS[j % len(self._FP_BANDS)]
                    fake = self._new(b, "ai", score, band, list(why))
                    fake["injected"] = "false_positive"
                    items.append(fake)
                    self.injected.append(fake["id"])
                    break
        for _ in range(n_hide):
            pool = [it for it in items if not it.get("injected")]
            if len(pool) < 2:
                break
            victim = self.rng.choice(pool)
            items.remove(victim)
            self.removed_true.append(victim["box"])
        return items

    # ---------------- human actions ----------------
    def accept(self, iid):
        self._snap(); self.get(iid)["status"] = "accepted"

    def accept_all_high(self):
        """'ai': bulk-accept only high-confidence boxes (R2). 'ai_bare': the user sees no confidence,
        so 'accept all' accepts every pending AI box - this is the control condition of Study B."""
        self._snap()
        n = 0
        for it in self.items:
            if it["status"] == "pending" and (it["band"] == "high" or self.condition == "ai_bare"):
                it["status"] = "accepted"; n += 1
        return n

    def reject(self, iid):
        self._snap(); self.get(iid)["status"] = "rejected"
        self._renumber()

    def add(self, box):
        self._snap()
        it = self._new(box, "human")
        self.items.append(it)
        self._renumber()
        return it

    def move(self, iid, box):
        self._snap()
        it = self.get(iid)
        it["box"] = [int(v) for v in box]
        it["edited"] = True
        if it["source"] == "ai":
            it["ai_band"] = it.get("ai_band", it["band"])
            it["band"] = "human"  # the human now owns this box
        self._renumber()

    def assign(self, iid, function, label=""):
        if function not in FUNCTIONS:
            raise ValueError("unknown function")
        self._snap()
        it = self.get(iid)
        it["function"] = function
        it["name"] = label.strip()[:40]
        if it["status"] == "pending":
            it["status"] = "accepted"  # assigning implies the human looked at it

    def verify(self, iid, ok=True):
        self._snap(); self.get(iid)["verified"] = bool(ok)

    def undo(self):
        if self.history:
            self.items = self.history.pop()
            return True
        return False

    def view_items(self):
        """What the UI is allowed to show. In 'ai_bare' every AI box looks the same: no score, band or reason."""
        out = []
        for it in self.items:
            v = {k: val for k, val in it.items() if k not in ("injected",)}  # planted boxes are never revealed to the UI
            if self.condition == "ai_bare" and v["source"] == "ai" and v["band"] != "human":
                v.update(score=None, band="plain", reasons=[])
            out.append(v)
        return out

    def to_dict(self):
        return {"id": self.id, "condition": self.condition, "items": self.view_items(), "validation": self.validate(),
                "can_confirm": self.can_confirm(), "confirmed": self.confirmed}

    # ---------------- validation + confirmation ----------------
    def active(self):
        return [it for it in self.items if it["status"] != "rejected"]

    def validate(self):
        """Returns list of {level: block|warn, code, msg, ids}."""
        out = []
        act = self.active()
        if not act:
            out.append({"level": "block", "code": "EMPTY", "msg": "No switches marked yet. Draw a box on each switch.", "ids": []})
        pend = [it for it in act if it["status"] == "pending"]
        if pend:
            out.append({"level": "block", "code": "PENDING", "ids": [i["id"] for i in pend],
                        "msg": f"{len(pend)} AI suggestion(s) not reviewed yet: " + ", ".join(i["label"] for i in pend)})
        unassigned = [it for it in act if not it["function"]]
        if unassigned:
            out.append({"level": "block", "code": "UNASSIGNED", "ids": [i["id"] for i in unassigned],
                        "msg": "Choose what these switches control: " + ", ".join(i["label"] for i in unassigned)})
        unver = [it for it in act if it["function"] and it["function"] != "unused" and not it["verified"]]
        if unver:
            out.append({"level": "block", "code": "UNVERIFIED", "ids": [i["id"] for i in unver],
                        "msg": "Flip these switches once and tick 'checked' to confirm: " + ", ".join(i["label"] for i in unver)})
        labels = {}
        for it in act:
            if it.get("name"):
                labels.setdefault(it["name"].lower(), []).append(it)
        for lab, its in labels.items():
            if len(its) > 1:
                out.append({"level": "warn", "code": "DUPLICATE", "ids": [i["id"] for i in its],
                            "msg": f"Same name '{its[0]['name']}' used for " + ", ".join(i["label"] for i in its) + ". Is that intended (e.g. two-way switch)?"})
        if act and all(it["function"] == act[0]["function"] for it in act) and len(act) > 2 and act[0]["function"]:
            out.append({"level": "warn", "code": "ALL_SAME", "ids": [], "msg": "Every switch has the same function. Please double-check."})
        return out

    def can_confirm(self):
        return not any(v["level"] == "block" for v in self.validate())

    def confirm(self):
        if not self.can_confirm():
            raise ValueError("Mapping has blocking issues")
        self.confirmed = True
        return self.final_mapping()

    def final_mapping(self):
        act = layout.renumber(self.active())
        rows = []
        for it in act:
            v = cap_for(it["function"])
            rows.append({"switch": it["label"], "row": it["row"] + 1, "position_in_row": it["col"] + 1,
                         "function": it["function"], "custom_label": it.get("name", ""), "cap_id": v["cap_id"], "symbol": v["symbol"],
                         "source": it["source"], "ai_score": it["score"], "verified": it["verified"], "box": it["box"]})
        return {"session": self.id, "switches": rows, "caps_needed": bill_of_caps(act)}

    # ---------------- study metrics ----------------
    def reliance_summary(self):
        """How did the human treat AI suggestions? (RQ4)"""
        ai = [it for it in self.items if it["source"] == "ai"]
        inj = [it for it in ai if it.get("injected")]
        real = [it for it in ai if not it.get("injected")]
        human_added = [it for it in self.items if it["source"] == "human"]
        missed_found = sum(1 for b in self.removed_true for h in human_added if _iou(b, h["box"]) >= 0.3)
        wrong_total = len(inj) + len(self.removed_true)
        caught = sum(1 for it in inj if it["status"] == "rejected") + missed_found
        real_kept = sum(1 for it in real if it["status"] == "accepted")
        return {
            "condition": self.condition,
            "ai_suggestions": len(ai),
            "ai_accepted": sum(1 for it in real if it["status"] == "accepted"),
            "ai_rejected": sum(1 for it in real if it["status"] == "rejected"),
            "ai_edited": sum(1 for it in ai if it.get("edited")),
            "human_added": len(human_added),
            "injected_false_positives": len(inj),
            "injected_fp_caught": sum(1 for it in inj if it["status"] == "rejected"),
            "hidden_true_switches": len(self.removed_true),
            "hidden_true_found": missed_found,
            # v3 primary reliance metrics (RQ1)
            "seeded_errors": wrong_total,
            "seeded_errors_caught": caught,
            "over_reliance": round(1 - caught / wrong_total, 3) if wrong_total else None,
            "under_reliance": round(1 - real_kept / len(real), 3) if real else None,
            "residual_errors": wrong_total - caught,
        }


def _overlap(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def _iou(a, b):
    i = _overlap(a, b)
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / u if u else 0
