# Full-Stack Migration Plan (React + FastAPI)

You have selected **Option A**. This plan outlines how we will pull the application apart, detaching the AI/Business logic from Streamlit, and creating a pure modern web architecture consisting of a Python FastAPI backend and a Vite React frontend.

## Proposed Architecture

### 1. The Backend (Python / FastAPI)
We will create a new directory named `backend/` and move the core logic there.
- **API Construction (`main.py`)**: Initialize a FastAPI server with CORS middleware.
- **Routing Endpoints**: 
  - `GET /api/tickets`: Returns all active tickets.
  - `GET /api/bottlenecks`: Returns flagged bottlenecks.
  - `POST /api/match`: Calls the AI `synergy_scorer` to fetch candidates for a ticket.
  - `POST /api/account`: Interacts with a newly created SQLite database for user sessions.
- **Decoupling Streamlit**: We will strip out all `@st.cache_data` decorators from `bottleneck_engine.py`, `synergy_scorer.py`, and `roi_calculator.py`, replacing them with standard in-memory caches or lightweight local state so the FastAPI server can run completely independent of Streamlit.

### 2. The Frontend (React / TypeScript / Vite)
We will initialize a new directory named `frontend/` using Vite (`npx create-vite-app`).
- **Styling**: We will stick strictly to standard CSS modules, migrating all the high-end styles, colors, and layout tokens from your existing `assets/styles.css` directly into the React structure without relying on Tailwind.
- **Routing (`react-router-dom`)**:
  - `/`: The main Dashboard (KPIs and Critical Bottlenecks).
  - `/active-tickets`: The dedicated page for viewing all standard tickets.
  - `/talent-routing/:ticketId`: The dedicated view for AI dispatch matching.
- **Advanced Interactivity**:
  - We will use standard React states to properly position Pop-ups/Modals that blur the background dynamically without visual bugs.
  - The "Allocate Talent" button will trigger seamless page transitions instead of entire server reruns.

## Migration Steps

1.  **Initialize Folders & Dependencies:**
    - Spin up the React/TypeScript frontend.
    - Setup FastAPI and `uvicorn` in the Python environment, creating the SQLite DB file.
2.  **Migrate Logic:** Move Python scripts to the backend and rewrite them into REST API endpoints.
3.  **UI Component Building:** Re-build the Nav Bar, KPI cards, and Bottleneck cards in React components.
4.  **Integration:** Connect the React app via `fetch()` to `http://localhost:8000/api/...` to feed live AI data into the pristine UI.

## User Review Required

> [!WARNING]
> This is a complete rebuild of the interface layer. Meaning `app.py` and Streamlit will eventually be discarded in favor of running `npm run dev` for the frontend and `uvicorn backend.main:app` for the backend. 
> Because this is a major transition taking us off Streamlit completely, **do I have your final sign-off to begin structuring this Full-Stack migration?**
