<div align="center">

# ⚡ SkillRoute — Proactive Capacity Engine

**Stop firefighting. Start routing.**  
SkillRoute automatically detects project bottlenecks, finds the best internal expert using AI-powered semantic search, and quantifies the financial ROI of every match — before a stalled ticket becomes a missed deadline.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-blue?style=flat-square)](https://github.com/facebookresearch/faiss)
[![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-AI-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev)

</div>

---

## What it does

Most engineering teams only discover a project is bottlenecked after a deadline slips. SkillRoute flips that — it continuously monitors your active tickets, flags the ones meeting bottleneck thresholds, and uses semantic vector search over your employee index to surface the highest-scoring expert to resolve it. Every match comes with a three-component **Synergy Score** and a full **ROI breakdown** so managers can make a justified allocation decision in seconds.

| Feature | Description |
|---|---|
| 🚨 **Proactive Bottleneck Detection** | Heuristic engine flags tickets stalled >3 days with >5 reassignment bounces, blocked tickets, or stalled critical-priority work |
| 🧠 **Synergy Score Algorithm** | Weighted match across semantic skill fit (60%), calendar availability (25%), and historical project success rate (15%) |
| 💰 **ROI & Cost-of-Delay Calculator** | Calculates sunk delay cost, projected loss if unresolved, cost-to-hire, net ROI, and break-even day |
| 📧 **AI-Generated Dossier & Email** | Gemini 2.5 Flash drafts a match dossier and intro email enriched with financial context |
| 🎨 **Modern Glass UI** | React + TypeScript frontend with frosted-glass components, spring-physics animations, and JetBrains Mono data display |
| 🔒 **Production-hardened API** | API key auth, explicit CORS origins, per-IP rate limiting, security response headers, input validation on all routes |

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│               Browser  (React 19 + TypeScript)            │
│   Dashboard · Bottlenecks · Active Tickets · TalentModal  │
└────────────────────────┬─────────────────────────────────┘
                         │  HTTPS  ·  X-API-Key header
┌────────────────────────▼─────────────────────────────────┐
│              nginx  (TLS termination + reverse proxy)     │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│             FastAPI backend  (uvicorn)                    │
│                                                          │
│  /api/tickets   ──►  bottleneck_engine.py                │
│  /api/match     ──►  synergy_scorer.py                   │
│  /api/roi       ──►  roi_calculator.py                   │
│  /api/account   ──►  backend/database.py  (SQLite)       │
│                                                          │
│  ┌───────────────────────────────────────────────────┐   │
│  │  dataset/                                         │   │
│  │  ├── employee_index.faiss   (vector embeddings)   │   │
│  │  └── employee_metadata.pkl  (employee profiles)   │   │
│  └───────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### Module breakdown

| File | Responsibility |
|---|---|
| `bottleneck_engine.py` | `ProjectTicket` data model + three-rule heuristic flagging engine + mock ticket dataset |
| `synergy_scorer.py` | FAISS index loader · `all-MiniLM-L6-v2` embedding · three-component Synergy Score calculator |
| `roi_calculator.py` | Cost-of-delay · cost-to-hire · net ROI · break-even maths · auto recommendation |
| `backend/main.py` | FastAPI app — API key auth, CORS, rate limiting, security headers, all routes |
| `backend/database.py` | SQLite audit log for user action history |
| `app.py` | Legacy Streamlit entry point (superseded by the React + FastAPI stack) |
| `frontend/src/api.ts` | Typed API client — auth header injection, safe HTTP error mapping |
| `frontend/src/pages/` | `Dashboard`, `Bottlenecks`, `ActiveTickets` page components |
| `frontend/src/components/` | `TalentModal`, `TicketCard`, `TopNav` shared components |

---

## Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |
| Gemini API key | [Get one free →](https://aistudio.google.com/app/apikey) |

---

## Local setup

### 1 — Clone

```bash
git clone https://github.com/Harshitshyamsukha/Skill-Route.git
cd Skill-Route
```

### 2 — Backend

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Edit `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
ALLOWED_ORIGINS=http://localhost:5173
API_SECRET_KEY=<generate below>
```

Generate a secure API key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Start the API:

```bash
uvicorn backend.main:app --reload --port 8000
```

API is live at `http://localhost:8000`.  
Set `ENABLE_DOCS=true` in `.env` to enable interactive docs at `/api/docs`.

### 3 — Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
```

Edit `frontend/.env.local`:

```env
VITE_API_BASE_URL=
VITE_API_KEY=<same value as API_SECRET_KEY above>
```

Start the dev server:

```bash
npm run dev
```

App is live at `http://localhost:5173`.

### 4 — Dataset files

The FAISS index and employee metadata are not included in this repo. Place them at:

```
dataset/
├── employee_index.faiss       # FAISS vector index (all-MiniLM-L6-v2 embeddings)
└── employee_metadata.pkl      # List[dict] — each entry: {"id": "...", "text_for_llm": "..."}
```

---

## How the Synergy Score works

When a bottleneck ticket is selected, SkillRoute extracts required skills using Gemini, embeds them with `all-MiniLM-L6-v2`, and queries the FAISS index. Each candidate is then scored across three components:

```
Synergy Score (0 – 100) =

  Semantic Match   × 0.60   ← FAISS L2 distance → exponential decay → 0–100
  Availability     × 0.25   ← available hrs/week, normalised to 0–100
  Past Success     × 0.15   ← historical project success rate, 0–100
```

Candidates are ranked by Synergy Score and presented with a per-component breakdown.

---

## Bottleneck detection rules

A ticket is flagged as a **Critical Bottleneck** when any of these conditions are met:

| Rule | Condition |
|---|---|
| Stalled in progress | Status = `In Progress` **and** days stalled > 3 **and** reassignment bounces > 5 |
| Blocked | Status = `Blocked` **and** days stalled > 2 |
| Critical priority stall | Priority = `Critical` **and** days stalled > 5 (any bounce count) |

Severity is ranked by `days × bounces` — highest first.

---

## ROI calculator

For every matched expert, SkillRoute calculates:

| Output | Formula |
|---|---|
| **Sunk cost of delay** | `days_stalled × daily_burn_rate` |
| **Projected delay cost** | `sunk_cost × 2` (assumes delay doubles if unresolved) |
| **Cost to hire** | `estimated_hours × expert_hourly_rate × 1.25` (overhead multiplier) |
| **Net ROI** | `projected_delay_cost − cost_to_hire` |
| **Break-even** | `cost_to_hire ÷ daily_burn_rate` days |
| **Recommendation** | ✅ APPROVE (ROI ≥ 50%) · 🟡 EVALUATE (0–50%) · 🔴 DEFER (negative) |

---

## API reference

All routes except `/api/health` require:

```
X-API-Key: <your API_SECRET_KEY>
```

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check — no auth required |
| `GET` | `/api/tickets` | All active tickets with bottleneck flags |
| `GET` | `/api/bottlenecks` | Flagged bottleneck tickets, sorted by severity |
| `GET` | `/api/tickets/{id}` | Single ticket by ID |
| `POST` | `/api/match` | Run FAISS synergy search for a ticket |
| `POST` | `/api/roi` | Calculate ROI for an expert ↔ ticket match |
| `POST` | `/api/account` | Write an entry to the audit log |
| `GET` | `/api/account/actions` | Read recent audit log entries |

**POST `/api/match`**
```json
{
  "ticket_id": "PROJ-104",
  "skills_text": "Machine Learning, Python, scikit-learn, MLflow"
}
```

**POST `/api/roi`**
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

## Production deployment

### Build the frontend

```bash
cd frontend && npm run build
# Output: frontend/dist/
```

### Run the backend

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 2
```

### nginx + TLS

Use `nginx.conf.example` as your template. Replace `YOUR_DOMAIN`, then:

```bash
sudo ln -s /etc/nginx/sites-available/skillroute /etc/nginx/sites-enabled/
sudo certbot --nginx -d yourdomain.com
sudo nginx -t && sudo systemctl reload nginx
```

---

## Security

See [`SECURITY.md`](SECURITY.md) for the full security audit. Key hardening applied:

- **API key authentication** on all protected routes via `X-API-Key` header
- **CORS locked** to an explicit allowlist (`ALLOWED_ORIGINS` env var) — no wildcard
- **Rate limiting** via SlowAPI — 100 req/min general, tighter on expensive endpoints
- **Security headers** on every response: `X-Frame-Options`, `X-Content-Type-Options`, `CSP`, `Referrer-Policy`, `HSTS`
- **Input validation** — length limits and format constraints on all request fields
- **Error sanitisation** — internal errors logged server-side, generic messages returned to clients
- **API docs disabled** by default in production (`ENABLE_DOCS=true` to re-enable locally)

---

## Project structure

```
Skill-Route/
├── backend/
│   ├── main.py                  # FastAPI app — auth, CORS, rate limiting, all routes
│   └── database.py              # SQLite audit log
├── frontend/
│   ├── src/
│   │   ├── api.ts               # Typed API client with auth + safe error handling
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx    # KPI overview + bottleneck summary
│   │   │   ├── Bottlenecks.tsx  # Critical bottleneck list + talent routing trigger
│   │   │   └── ActiveTickets.tsx
│   │   └── components/
│   │       ├── TalentModal.tsx  # Synergy scores + ROI panel + candidate selection
│   │       ├── TicketCard.tsx
│   │       └── TopNav.tsx
│   ├── .env.example
│   └── vite.config.ts
├── dataset/                     # ⚠ Not in repo — add your own files
│   ├── employee_index.faiss
│   └── employee_metadata.pkl
├── bottleneck_engine.py         # Heuristic flagging engine + ticket data model
├── synergy_scorer.py            # FAISS search + three-component scorer
├── roi_calculator.py            # Cost-of-delay + ROI maths
├── app.py                       # Legacy Streamlit entry point
├── requirements.txt
├── .env.example                 # Copy to .env and fill in values
├── nginx.conf.example           # Reference config for production TLS
└── SECURITY.md                  # Full security audit notes
```

---

## Tech stack

**Backend** — Python 3.11+, FastAPI, Uvicorn, FAISS, sentence-transformers (`all-MiniLM-L6-v2`), Google Gemini 2.5 Flash, SlowAPI, Pydantic v2, SQLite, python-dotenv

**Frontend** — React 19, TypeScript, React Router v7, Vite 8, Manrope + JetBrains Mono (Google Fonts)

---

## License

MIT © 2025 [Harshit Shyamsukha](https://github.com/Harshitshyamsukha)
