# HireSense AI — Find Fast. Hire Smart.

HireSense AI is an AI-assisted job discovery demo (Phase-1) that:
- extracts skills from resume text, and
- matches them with a curated dummy job list,
- returns a % match score and matched skills.

This scaffold is production-ready for growth: clean services, API blueprints, env config, tests, and deploy files.

---

## Tech Stack
- **Backend:** Python 3.11, Flask, Flask-CORS
- **Frontend:** Server-rendered HTML + JS (templates/static)
- **Prod:** Gunicorn (via `wsgi.py`, `Procfile`)
- **Tests:** Pytest

---

## Project Structure
app/
init.py          # app factory + CORS + routes
config.py            # dev/prod config
routes/api.py        # /api endpoints
services/            # business logic (resume parsing + matcher)
resume.py
matcher.py
templates/index.html # demo UI
static/style.css     # UI styles
app.py                 # dev entry (python app.py)
wsgi.py                # prod entry (gunicorn)
tests/test_matcher.py  # sample test
requirements.txt       # Python deps
Procfile               # for Render/Railway/Heroku
.env.example           # sample env
.gitignore             # Python ignores
runtime.txt            # Python version (optional)
---

## Local Development

### 1) Create & activate virtual env
**macOS/Linux**
```bash
python -m venv .venv && source .venv/bin/activate
Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
2) Install deps
pip install -r requirements.txt
3) Env vars
cp .env.example .env
# (optional) edit .env and set ENV=dev or prod
4) Run dev server
python app.py
Open: http://localhost:5000
