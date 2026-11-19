# SPARSH (स्पर्श) – AI-Assisted Tactile Labelling of Switchboards

BITS F364 Human-AI Interaction · Team SPARSH · BITS Pilani

An AI helps a caregiver label a switchboard with off-the-shelf tactile stickers; Study B tests whether showing the
AI's confidence (vs bare suggestions, with ~25% seeded errors) helps installers catch its mistakes.

## Repository layout
| Path | What | Hosted on |
|---|---|---|
| `index.html`, `assets/` | Project website (videos, poster, slides, report) | **Vercel** (static, no build) |
| `code/` | Working Flask app + research code (detector, study analysis, refinement tool) | **Render** (`render.yaml`) |

## Deploy
**Website (Vercel):** vercel.com → Add New → Project → import this repo → Framework preset *Other*, no build command, output = root → Deploy.
`.vercelignore` keeps `code/` out of the website.

**App (Render):** render.com → New → Blueprint → select this repo → Apply. It reads `render.yaml`
(free plan, one worker, because sessions live in memory). The free server sleeps when idle; the first request takes up to a minute.

After both are live, set `APP_URL` and `REPO_URL` at the bottom of `index.html` and push; Vercel redeploys automatically.

## Run locally
```bash
cd code
pip install -r requirements.txt
python app/server.py            # http://localhost:5000
python -m pytest -q tests       # 12 passed
```

User-study results are not included yet; the detector figures come from a synthetic benchmark.
