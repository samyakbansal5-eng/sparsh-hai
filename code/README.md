# SPARSH (स्पर्श) – AI-assisted switchboard mapping + tactile caps

BITS F364 Human-AI Interaction · Team SPARSH · BITS Pilani

A caregiver takes **one photo** of a switchboard. Computer vision **finds and numbers** the switches and shows how sure it is.
The caregiver **checks, corrects, and assigns** what each switch controls (the camera cannot see wiring), physically **verifies**
each switch, and gets a printable **installation guide** that says which 3D-printed tactile cap goes on which switch.
After that, the visually impaired user identifies switches **by touch alone**: no phone, no internet, no AI.

## Quick start (laptop, Python 3.10+)
```bash
pip install -r requirements.txt
python app/server.py                 # open http://localhost:5000 (phone on same Wi-Fi: http://<laptop-ip>:5000)
python -m pytest -q tests            # 12 tests: rules R1–R6, seeded errors, bare condition, reliance metric, pipeline
```

## Reproduce every number in the report
```bash
python tools/generate_synthetic.py --out data/synthetic                   # 360 train / 120 val / 240 test photos
python tools/generate_synthetic.py --out data/synthetic --stress 90 --seed 2026   # held-out stress conditions
python tools/train_verifier.py                                            # trains models/verifier.pkl on TRAIN, tunes C on VAL
python tools/evaluate_detector.py --split test   --mode heuristic
python tools/evaluate_detector.py --split test   --mode learned
python tools/evaluate_detector.py --split stress --mode learned
python tools/make_figures.py                                              # figures/*.png
python hardware/make_caps.py                                              # hardware/stl/*.stl + renders + PRINT_REPORT.csv
python study/analysis.py --data study/data                                # real study data (after the sessions)
python study/analysis.py --simulate                                       # pipeline self-test ONLY (watermarked, never report)
```
Evaluate on **real photos**: put photos + `annotations.json` (same format as `data/synthetic/test`) in `data/real/` and run
`python tools/evaluate_detector.py --real data/real --mode learned`. The app's `/api/session/<id>/annotations` endpoint exports
caregiver-confirmed boxes, so every real onboarding session can become a labelled test image (with consent).

## Layout
| Path | What | Architecture module |
|---|---|---|
| `sparsh/acquisition.py` | load photo, quality checks (dark / blurry / glare) | M1 |
| `sparsh/preprocessing.py` | plate localisation, perspective correction, CLAHE | M2 |
| `sparsh/detection.py`, `sparsh/verifier.py` | 2-stage switch detector + confidence bands | M3 |
| `sparsh/layout.py` | rows + S1..Sn numbering | M4 |
| `sparsh/mapping.py` | human confirmation rules R1–R6, validation, reliance probe | M5 |
| `sparsh/tactile.py` | tactile vocabulary (data, versioned) | M6 |
| `sparsh/guide.py` | printable installation guide EN + हिंदी | M7 |
| `sparsh/logger.py` | consented study logging | M8 |
| `app/` | Flask server + accessible web UI | M1–M8 |
| `hardware/` | parametric caps (Python + OpenSCAD), STLs, renders | tactile hardware |
| `study/` | data templates, analysis pipeline, results | evaluation |
| `tools/` | dataset generator, training, evaluation, figures, demo recorder | |

## Honesty notes (read before presenting)
* Detection numbers come from a **synthetic benchmark** (rendered Indian modular plates). They show the pipeline works and where it breaks; they are **not** real-world accuracy. Real-photo evaluation is `--real`.
* The tactile vocabulary v1 is **pending the P1 discrimination pilot**.
* User-study results exist only after the team runs the studies; `study/SIMULATED_*` folders are pipeline tests and must never be reported.
