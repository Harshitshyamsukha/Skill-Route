<div align="center">

# ⚡ SkillRoute — Proactive Capacity Engine

**Detect project bottlenecks before they escalate. Route the right expert. Quantify the ROI.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

![SkillRoute Dashboard](frontend/src/assets/hero.png)

</div>

---

## What it does

SkillRoute monitors your active project tickets, automatically flags the ones that are turning into costly bottlenecks, and uses semantic AI search to surface the best internal expert to resolve them — complete with a financial ROI calculation to justify the match.

| Feature | Description |
|---|---|
| 🚨 **Proactive Bottleneck Detection** | Heuristic engine flags tickets stalled >3 days with >5 reassignment bounces |
| 🧠 **Synergy Score** | Three-component weighted match: Semantic skill fit (60%) + Calendar availability (25%) + Past success rate (15%) |
| 💰 **ROI & Cost-of-Delay Calculator** | Quantifies sunk delay cost, projected loss, cost-to-hire, net ROI, and break-even day |
| 📧 **AI Dossier & Intro Email** | Gemini 2.5 Flash drafts a match dossier and intro email enriched with financial context |
| 🔒 **Production-hardened API** | API key auth, CORS lockdown, rate limiting, security headers, input validation |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (React + TS)                  │
│  Dashboard · Bottlenecks · Active Tickets · TalentModal  │
└───────────────────┬─────────────────────────────────────┘
                    │  HTTPS  ·  X-API-Key header
┌───────────────────▼─────────────────────────────────────┐
│              nginx (TLS termination + proxy)             │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│           FastAPI backend  (uvicorn)                     │
│                                                         │
│  /api/tickets        bottleneck_engine.py               │
│  /api/bottlenecks    ├─ Heuristic flagging              │
│  /api/match    ──►   synergy_scorer.py                  │
│  /api/roi      ──►   roi_calculator.py                  │
│  /api/account  ──►   backend/database.py (SQLite)       │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  dataset/                                        │   │
│  │  ├── employee_index.faiss   (vector embeddings)  │   │
│  │  └── employee_metadata.pkl  (employee profiles)  │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Module responsibilities

| File | Role |
|---|---|
| `bottleneck_engine.py` | Ticket data model + three-rule heuristic flagging engine |
| `synergy_scorer.py` | FAISS index loader + three-component Synergy Score calculator |
| `roi_calculator.py` | Cost-of-delay, cost-to-hire, net ROI, break-even maths |
| `backend/main.py` | FastAPI app — auth, CORS, rate limiting, routes, security headers |
| `backend/database.py` | SQLite audit log (user action history) |
| `frontend/src/api.ts` | Typed API client — auth header injection, safe error mapping |

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |
| A Gemini API key | [Get one free](https://aistudio.google.com/app/apikey) |

---

## Local development setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/skillroute.git
cd skillroute
```

### 2. Backend

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up your environment variables
cp .env.example .env
```

Edit `.env` and fill in:

```env
GEMINI_API_KEY=your_gemini_api_key_here
ALLOWED_ORIGINS=http://localhost:5173
API_SECRET_KEY=<generate with the command below>
```

Generate a secure API key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Start the API server:

```bash
uvicorn backend.main:app --reload --port 8000
```

The API will be live at `http://localhost:8000`.  
With `ENABLE_DOCS=true` in `.env`, interactive docs are at `http://localhost:8000/api/docs`.

### 3. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
```

Edit `frontend/.env.local`:

```env
VITE_API_BASE_URL=          # leave empty — Vite proxy handles /api/* in dev
VITE_API_KEY=<same value as API_SECRET_KEY in the backend .env>
```

Start the dev server:

```bash
npm run dev
```

The app will be live at `http://localhost:5173`.

### 4. Dataset files

Place the following files in `dataset/` (not included in this repo — see note below):

```
dataset/
├── employee_index.faiss       # FAISS vector index
└── employee_metadata.pkl      # List of employee profile dicts
```

Each metadata entry is expected to have the shape:

```python
{"id": "1234", "text_for_llm": "Full profile text used for matching..."}
```

---

## Production deployment

### 1. Build the frontend

```bash
cd frontend
npm run build          # outputs to frontend/dist/
```

### 2. Configure environment variables

On your server, set the following (via systemd `EnvironmentFile`, Docker env, etc.):

```env
GEMINI_API_KEY=your_live_key
ALLOWED_ORIGINS=https://yourdomain.com
API_SECRET_KEY=your_64_char_hex_secret
ENABLE_DOCS=false
```

### 3. Run the API server

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 2
```

For process management, use [systemd](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html) or [Supervisor](http://supervisord.org/).

### 4. Set up nginx + TLS

Copy `nginx.conf.example` to `/etc/nginx/sites-available/skillroute`, replace `YOUR_DOMAIN`, then:

```bash
sudo ln -s /etc/nginx/sites-available/skillroute /etc/nginx/sites-enabled/
sudo certbot --nginx -d yourdomain.com
sudo nginx -t && sudo systemctl reload nginx
```

---

## API reference

All routes except `/api/health` require the header:

```
X-API-Key: <your API_SECRET_KEY>
```

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/health` | Health check (no auth) |
| `GET` | `/api/tickets` | All active project tickets |
| `GET` | `/api/bottlenecks` | Flagged bottleneck tickets, sorted by severity |
| `GET` | `/api/tickets/{id}` | Single ticket by ID |
| `POST` | `/api/match` | Run FAISS synergy search for a ticket |
| `POST` | `/api/roi` | Calculate ROI for an expert↔ticket match |
| `POST` | `/api/account` | Write to audit log |
| `GET` | `/api/account/actions` | Read recent audit log entries |

**POST `/api/match` body:**

```json
{
  "ticket_id": "PROJ-104",
  "skills_text": "Machine Learning, Python, scikit-learn, MLflow"
}
```

**POST `/api/roi` body:**

```json
{
  "ticket_id": "PROJ-104",
  "expert_id": "4821",
  "days_already_delayed": 9.0,
  "estimated_fix_hours": 80,
  "daily_burn_rate": 1500.00,
  "expert_hourly_rate": 120.00
}
```

---

## Synergy Score breakdown

```
Synergy Score (0–100) =
    FAISS Semantic Match  × 0.60   (L2 distance → exponential decay → 0–100)
  + Calendar Availability × 0.25   (available hours/week, normalised to 0–100)
  + Past Project Success  × 0.15   (historical success rate, 0–100)
```

---

## Bottleneck detection rules

A ticket is flagged as a **Critical Bottleneck** if any of the following are true:

| Rule | Condition |
|---|---|
| Stalled in progress | Status = `In Progress` **AND** days in status > 3 **AND** reassignment bounces > 5 |
| Blocked too long | Status = `Blocked` **AND** days in status > 2 |
| Critical priority stall | Priority = `Critical` **AND** days in status > 5 |

---

## Project structure

```
skillroute/
├── backend/
│   ├── main.py                # FastAPI app (auth, CORS, routes, rate limiting)
│   └── database.py            # SQLite audit log
├── frontend/
│   ├── src/
│   │   ├── api.ts             # Typed API client
│   │   ├── pages/             # Dashboard, Bottlenecks, ActiveTickets
│   │   └── components/        # TopNav, TicketCard, TalentModal
│   ├── .env.example
│   └── vite.config.ts
├── dataset/                   # ⚠ Not in repo — add your own files
│   ├── employee_index.faiss
│   └── employee_metadata.pkl
├── bottleneck_engine.py
├── synergy_scorer.py
├── roi_calculator.py
├── requirements.txt
├── .env.example               # Copy to .env and fill in values
├── nginx.conf.example         # Reference nginx config for production
├── SECURITY.md                # Full security audit notes
└── .gitignore
```

---

## Security

This project has been audited for common web security issues. See [`SECURITY.md`](SECURITY.md) for the full report.

**Highlights:**
- API key authentication on all protected routes (`X-API-Key` header)
- CORS locked to explicit origin list from environment variable
- Per-IP rate limiting via SlowAPI
- Security response headers: `X-Frame-Options`, `X-Content-Type-Options`, `CSP`, `HSTS`
- Input length + format validation on all request models
- Internal errors logged server-side, never forwarded to clients
- Interactive API docs disabled by default in production

**Found a vulnerability?** Please open a private GitHub Security Advisory rather than a public issue.

---

## Tech stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com) — async Python API framework
- [FAISS](https://github.com/facebookresearch/faiss) — vector similarity search
- [sentence-transformers](https://www.sbert.net) — `all-MiniLM-L6-v2` embeddings
- [Google Gemini 2.5 Flash](https://ai.google.dev) — dossier and email generation
- [SlowAPI](https://github.com/laurentS/slowapi) — rate limiting
- SQLite — lightweight audit log

**Frontend**
- [React 19](https://react.dev) + [TypeScript](https://www.typescriptlang.org)
- [React Router v7](https://reactrouter.com)
- [Vite 8](https://vite.dev) — build tooling
- [Manrope](https://fonts.google.com/specimen/Manrope) + [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono) typefaces

---

## License

MIT © 2025 — see [LICENSE](LICENSE) for details.
