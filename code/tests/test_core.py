"""Unit tests for the human-in-the-loop rules (R1-R6) and the pipeline. Run: python -m pytest -q"""
import os
import sys

import cv2
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from sparsh.mapping import Session  # noqa: E402
from sparsh.acquisition import load_image  # noqa: E402
from sparsh.preprocessing import preprocess  # noqa: E402
from sparsh.detection import detect  # noqa: E402
from sparsh.guide import build_guide  # noqa: E402

DETS = [{"box": [10 + 60 * i, 20, 50 + 60 * i, 90], "score": s, "band": b, "reasons": []}
        for i, (s, b) in enumerate([(0.95, "high"), (0.9, "high"), (0.6, "check"), (0.3, "low")])]


def fresh():
    s = Session()
    s.load_detections(DETS, (120, 300, 3))
    return s


def test_R1_ai_boxes_start_pending():
    s = fresh()
    assert all(i["status"] == "pending" for i in s.items)
    assert [i["label"] for i in s.items] == ["S1", "S2", "S3", "S4"]


def test_R2_bulk_accept_only_high():
    s = fresh()
    assert s.accept_all_high() == 2
    assert sum(i["status"] == "pending" for i in s.items) == 2
    assert any(v["code"] == "PENDING" for v in s.validate())


def test_R3_ai_never_assigns_function():
    s = fresh()
    assert all(i["function"] is None for i in s.items)


def test_R4_unverified_blocks_confirmation():
    s = fresh()
    for i in list(s.items):
        s.accept(i["id"])
        s.assign(i["id"], "light")
    assert not s.can_confirm()
    for i in s.items:
        s.verify(i["id"])
    assert s.can_confirm()
    m = s.confirm()
    assert m["caps_needed"] == {"CAP-L": 4}


def test_R5_undo_and_renumber_after_reject_and_add():
    s = fresh()
    first = s.items[0]["id"]
    s.reject(first)
    assert [i["label"] for i in s.active()] == ["S1", "S2", "S3"]
    s.add([2, 20, 8, 90])  # new left-most switch becomes S1
    assert s.active()[0]["source"] == "human"
    s.undo(); s.undo()
    assert len(s.active()) == 4


def test_R6_duplicate_name_is_warning_not_block():
    s = fresh()
    for i in s.items:
        s.assign(i["id"], "light", "Hall")
        s.verify(i["id"])
    v = s.validate()
    assert any(x["code"] == "DUPLICATE" and x["level"] == "warn" for x in v)
    assert s.can_confirm()


def test_manual_condition_has_no_ai():
    s = Session(condition="manual")
    s.load_detections(DETS, (120, 300, 3))
    assert s.items == []


DETS8 = [{"box": [10 + 60 * i, 20, 50 + 60 * i, 90], "score": 0.9, "band": "high", "reasons": []} for i in range(8)]


def test_seeded_errors_about_25_percent():
    """v3: 8 true switches at rate 0.25 -> 2 seeded errors: 1 planted false switch + 1 hidden true switch."""
    s = Session(inject_errors=True, seed=1)
    s.load_detections(DETS8, (300, 520, 3))
    r = s.reliance_summary()
    assert r["injected_false_positives"] == 1 and r["hidden_true_switches"] == 1 and r["seeded_errors"] == 2


def test_small_board_still_gets_one_seeded_error():
    s = Session(inject_errors=True, seed=1)
    s.load_detections(DETS, (120, 400, 3))
    assert s.reliance_summary()["seeded_errors"] == 1


def test_bare_condition_hides_confidence_but_keeps_it_for_analysis():
    s = Session(condition="ai_bare", inject_errors=True, seed=2)
    s.load_detections(DETS8, (300, 520, 3))
    shown = s.to_dict()["items"]
    assert all(i["band"] == "plain" and i["score"] is None and not i["reasons"] for i in shown if i["source"] == "ai")
    assert not any("injected" in i for i in shown)          # the UI can never tell which boxes are planted
    assert any(i.get("injected") for i in s.items)          # ...but the log still knows
    assert s.accept_all_high() == len(s.items)              # control: 'keep all' keeps every AI box


def test_over_reliance_metric():
    s = Session(condition="ai", inject_errors=True, seed=3)
    s.load_detections(DETS8, (300, 520, 3))
    fp = [i for i in s.items if i.get("injected")][0]
    s.reject(fp["id"])                                      # caught the planted switch, missed the hidden one
    r = s.reliance_summary()
    assert r["seeded_errors_caught"] == 1 and r["over_reliance"] == 0.5 and r["residual_errors"] == 1


@pytest.mark.skipif(not os.path.isdir(os.path.join(ROOT, "app", "samples")), reason="no samples")
def test_pipeline_end_to_end_on_sample():
    p = os.path.join(ROOT, "app", "samples", "normal_img_0006.jpg")
    img = load_image(p)
    pp = preprocess(img)
    d = detect(pp["plate_img"])
    assert pp["plate_found"] and len(d) >= 1
    s = Session(); s.load_detections(d, pp["plate_img"].shape)
    for i in s.items:
        s.accept(i["id"]); s.assign(i["id"], "fan"); s.verify(i["id"])
    s.confirm()
    html = build_guide(pp["plate_img"], s.final_mapping(), "hi")
    assert "स्पर्श" in html and "CAP-F" in html
