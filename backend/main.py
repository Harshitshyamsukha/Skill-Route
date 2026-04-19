from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# Add parent directory to path so we can import root modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bottleneck_engine
import synergy_scorer
import roi_calculator
from backend import database

app = FastAPI(title="SkillRoute Proactive API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class SynergyRequest(BaseModel):
    ticket_id: str
    skills_text: str

class ROIRequest(BaseModel):
    ticket_id: str
    expert_id: str
    days_already_delayed: float
    estimated_fix_hours: int
    daily_burn_rate: float
    expert_hourly_rate: float

class AccountAction(BaseModel):
    user_id: str
    action_type: str
    details: str


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def startup_event():
    database.init_db()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "SkillRoute Proactive Engine"}


# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------

@app.get("/api/tickets")
def get_tickets():
    """Return all active tickets with bottleneck flags evaluated."""
    return bottleneck_engine.get_all_tickets()


@app.get("/api/bottlenecks")
def get_bottlenecks():
    """Return only flagged bottleneck tickets, sorted by severity."""
    return bottleneck_engine.get_critical_bottlenecks()


@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    """Return a single ticket by ID."""
    ticket = bottleneck_engine.get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found")
    return ticket


# ---------------------------------------------------------------------------
# AI Matching
# ---------------------------------------------------------------------------

@app.post("/api/match")
def match_candidates(req: SynergyRequest):
    """
    Run FAISS-based synergy search for a ticket's required skills.
    Returns top-5 ranked candidates with score breakdowns.
    """
    try:
        candidates = synergy_scorer.run_synergy_search(req.skills_text, n=5)
        return [synergy_scorer.score_breakdown_dict(c) for c in candidates]
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"AI model resources not found: {e}")
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Missing dependency: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synergy search failed: {e}")


# ---------------------------------------------------------------------------
# ROI Calculator
# ---------------------------------------------------------------------------

@app.post("/api/roi")
def calculate_roi(req: ROIRequest):
    """
    Calculate the ROI of routing a specific expert to a bottleneck ticket.
    """
    try:
        result = roi_calculator.calculate_roi(
            ticket_id=req.ticket_id,
            expert_id=req.expert_id,
            days_already_delayed=req.days_already_delayed,
            estimated_fix_hours=req.estimated_fix_hours,
            daily_burn_rate=req.daily_burn_rate,
            expert_hourly_rate=req.expert_hourly_rate,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ROI calculation failed: {e}")


# ---------------------------------------------------------------------------
# Account / Audit Log
# ---------------------------------------------------------------------------

@app.post("/api/account")
def handle_account_action(action: AccountAction):
    """Log a user action to the audit trail."""
    database.log_action(action.user_id, action.action_type, action.details)
    return {"status": "success", "message": "Action logged successfully"}


@app.get("/api/account/actions")
def get_account_actions():
    """Return the 10 most recent logged actions."""
    return database.get_recent_actions()
