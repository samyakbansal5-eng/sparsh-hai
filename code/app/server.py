"""
SPARSH onboarding app (Flask). Run:  python app/server.py   then open http://localhost:5000
On a phone in the same Wi-Fi: http://<laptop-ip>:5000  (camera capture works via the upload button).
"""
import base64
import csv
import io
import json
import os
import sys
import time

import cv2
from flask import Flask, Response, jsonify, request, send_from_directory

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from sparsh.acquisition import load_image, quality_report  # noqa: E402
from sparsh.preprocessing import preprocess  # noqa: E402
from sparsh.detection import detect  # noqa: E402
from sparsh.verifier import Verifier  # noqa: E402
from sparsh.mapping import Session  # noqa: E402
from sparsh.logger import EventLogger  # noqa: E402
from sparsh.guide import build_guide  # noqa: E402
from sparsh.tactile import VOCABULARY, svg_symbol, VOCABULARY_VERSION  # noqa: E402

app = Flask(__name__, static_folder="static", static_url_path="/static")
MODEL = os.path.join(ROOT, "models", "verifier.pkl")
VERIFIER = Verifier.load(MODEL) if os.path.exists(MODEL) else None
SAMPLES = os.path.join(os.path.dirname(__file__), "samples")
STATE = {}  # sid -> dict(session, logger, plate)


def _b64(img):
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()


def _state(sid):
    if sid not in STATE:
        raise KeyError("session not found - please start again")
    return STATE[sid]


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/vocabulary")
def vocabulary():
    return jsonify({"version": VOCABULARY_VERSION,
                    "items": {k: {**v, "icon": svg_symbol(v["symbol"], 28)} for k, v in VOCABULARY.items()}})


@app.route("/api/samples")
def samples():
    return jsonify(sorted(f for f in os.listdir(SAMPLES) if f.lower().endswith((".jpg", ".png")))) if os.path.isdir(SAMPLES) else jsonify([])


@app.route("/api/samples/<name>")
def sample_file(name):
    return send_from_directory(SAMPLES, name)


@app.route("/api/session", methods=["POST"])
def new_session():
    d = request.get_json(force=True) or {}
    s = Session(condition=d.get("condition", "ai"), participant_id=d.get("participant_id", ""),
                inject_errors=bool(d.get("inject_errors")), seed=d.get("seed"),
                inject_rate=float(d.get("inject_rate", 0.25)))
    lg = EventLogger(s.id, s.participant_id, s.condition, enabled=bool(d.get("study_mode")))
    lg.log("session_start", inject=s.inject_errors)
    STATE[s.id] = {"session": s, "logger": lg, "plate": None}
    return jsonify({"id": s.id, "condition": s.condition})


@app.route("/api/session/<sid>/photo", methods=["POST"])
def photo(sid):
    st = _state(sid)
    s, lg = st["session"], st["logger"]
    if "file" in request.files:
        data = request.files["file"].read()
    else:
        name = (request.get_json(force=True) or {}).get("sample")
        data = open(os.path.join(SAMPLES, os.path.basename(name)), "rb").read()
    lg.log("photo_uploaded")
    t0 = time.perf_counter()
    try:
        img = load_image(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    issues, q = quality_report(img)
    pp = preprocess(img)
    plate = pp["plate_img"]
    dets = detect(plate, VERIFIER) if s.condition in ("ai", "ai_bare") else []
    st["plate"] = plate
    s.load_detections(dets, plate.shape)
    dt = time.perf_counter() - t0
    lg.log("detection_done", n=len(dets), seconds=round(dt, 3), plate_found=pp["plate_found"])
    if not pp["plate_found"]:
        issues.append(("info", "I could not find the edges of the switch plate, so the photo was not straightened. "
                               "Detection may be less reliable - please check every box."))
    if s.condition in ("ai", "ai_bare") and not dets:
        issues.append(("warn", "The AI did not find any switches. You can mark them yourself with '+ Add switch', or retake the photo closer."))
    return jsonify({"plate": _b64(plate), "w": plate.shape[1], "h": plate.shape[0], "quality": q,
                    "issues": [{"level": a, "msg": b} for a, b in issues], "plate_found": pp["plate_found"],
                    "seconds": round(dt, 2), "model": "learned" if VERIFIER else "heuristic", **s.to_dict()})


@app.route("/api/session/<sid>/action", methods=["POST"])
def action(sid):
    st = _state(sid)
    s, lg = st["session"], st["logger"]
    d = request.get_json(force=True)
    t = d.get("type")
    iid = d.get("id")
    try:
        if t == "accept":
            s.accept(iid)
        elif t == "accept_all_high":
            n = s.accept_all_high(); d["n"] = n
        elif t == "reject":
            s.reject(iid)
        elif t == "add":
            it = s.add(d["box"]); d["id"] = it["id"]
        elif t == "move":
            s.move(iid, d["box"])
        elif t == "assign":
            s.assign(iid, d["function"], d.get("label", ""))
        elif t == "verify":
            s.verify(iid, d.get("ok", True))
        elif t == "undo":
            s.undo()
        elif t == "confirm":
            if not s.can_confirm():
                lg.log("confirm_blocked", issues=[v["code"] for v in s.validate() if v["level"] == "block"])
                return jsonify({**s.to_dict(), "error": "Please resolve the items listed under 'Before you confirm'."})
            s.confirm()
            lg.log("confirmed")
            row = lg.summary_row(s)
            return jsonify({**s.to_dict(), "summary": row, "mapping": s.final_mapping()})
        else:
            return jsonify({"error": "unknown action"}), 400
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    lg.log(t, **{k: v for k, v in d.items() if k in ("id", "function", "n", "ok")})
    return jsonify(s.to_dict())


@app.route("/api/session/<sid>/guide")
def guide(sid):
    st = _state(sid)
    s = st["session"]
    if not s.confirmed:
        return Response("Confirm the mapping first.", 400)
    st["logger"].log("guide_generated", lang=request.args.get("lang", "en"))
    return Response(build_guide(st["plate"], s.final_mapping(), request.args.get("lang", "en"),
                                request.args.get("household", "")), mimetype="text/html")


@app.route("/api/session/<sid>/export.<fmt>")
def export(sid, fmt):
    st = _state(sid)
    m = st["session"].final_mapping()
    if fmt == "json":
        return Response(json.dumps(m, indent=2), mimetype="application/json",
                        headers={"Content-Disposition": f"attachment; filename=sparsh_{sid}.json"})
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=["switch", "row", "position_in_row", "function", "custom_label", "cap_id", "symbol", "source", "ai_score", "verified"], extrasaction="ignore")
    w.writeheader()
    w.writerows(m["switches"])
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename=sparsh_{sid}.csv"})


@app.route("/api/session/<sid>/annotations")
def annotations(sid):
    """Confirmed boxes = free, human-verified labels to retrain/evaluate the detector on REAL photos."""
    st = _state(sid)
    boxes = [it["box"] for it in st["session"].active()]
    return jsonify({"plate_size": list(st["plate"].shape[:2]), "switch_boxes_plate_coords": boxes})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"SPARSH running on http://localhost:{port}  (verifier: {'learned' if VERIFIER else 'heuristic'})")
    app.run(host="0.0.0.0", port=port, debug=False)
