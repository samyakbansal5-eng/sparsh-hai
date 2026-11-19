"""M8 - Evaluation & data collection.
Only logs what the study needs: timestamps, actions, counts. No photos of people,
no names (participant IDs like P07 only). Logging is OFF unless the operator
starts a session in Study Mode after consent has been recorded on paper."""
import csv
import json
import os
import time

LOG_DIR = os.environ.get("SPARSH_LOG_DIR", os.path.join(os.path.dirname(__file__), "..", "study", "logs"))


class EventLogger:
    def __init__(self, session_id, participant_id="", condition="", enabled=False):
        self.enabled = enabled
        self.sid, self.pid, self.cond = session_id, participant_id, condition
        self.t0 = time.time()
        self.events = []
        if enabled:
            os.makedirs(LOG_DIR, exist_ok=True)

    def log(self, event, **kw):
        e = {"t": round(time.time() - self.t0, 3), "event": event, **kw}
        self.events.append(e)
        if self.enabled:
            with open(os.path.join(LOG_DIR, f"{self.pid or 'anon'}_{self.sid}.jsonl"), "a") as f:
                f.write(json.dumps(e) + "\n")

    def first(self, name):
        for e in self.events:
            if e["event"] == name:
                return e["t"]
        return None

    def count(self, name):
        return sum(1 for e in self.events if e["event"] == name)

    def summary_row(self, session):
        r = session.reliance_summary()
        row = {"session": self.sid, "participant": self.pid, "condition": self.cond,
               "t_photo": self.first("photo_uploaded"), "t_detect_done": self.first("detection_done"),
               "t_confirm": self.first("confirmed"),
               "onboarding_time_s": (self.first("confirmed") or 0) - (self.first("photo_uploaded") or 0),
               "n_accept": self.count("accept") + self.count("accept_all_high"), "n_reject": self.count("reject"),
               "n_add": self.count("add"), "n_move": self.count("move"), "n_undo": self.count("undo"),
               "n_assign": self.count("assign"), "n_validation_blocked": self.count("confirm_blocked"),
               "final_switches": len(session.active()), **r}
        if self.enabled:
            path = os.path.join(LOG_DIR, "study_B_sessions.csv")
            new = not os.path.exists(path)
            with open(path, "a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(row.keys()))
                if new:
                    w.writeheader()
                w.writerow(row)
        return row
