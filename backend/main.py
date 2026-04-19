"""
backend/main.py — SkillRoute Proactive API
===========================================
Security hardening applied:
  - CORS locked to ALLOWED_ORIGINS env var (no wildcard in production)
  - API key auth on all /api/* routes via X-API-Key header
  - Input length limits on all user-supplied strings
  - Internal error details never forwarded to the client
  - Security response headers on every reply (X-Frame-Options, CSP, etc.)
  - /api/docs and /api/redoc disabled in production
  - Rate limiting via SlowAPI (100 req/min per IP)
"""

import logging
import os
import sys
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

load_dotenv()

# ---------------------------------------------------------------------------
# Logging — structured, no sensitive values
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("skillroute.api")

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bottleneck_engine
import roi_calculator
import synergy_scorer
from backend import database

# ---------------------------------------------------------------------------
# Config from environment
# ---------------------------------------------------------------------------
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]

API_SECRET_KEY = os.getenv("API_SECRET_KEY", "")
if not API_SECRET_KEY or API_SECRET_KEY == "change_me_to_a_random_64_char_hex_string":
    logger.warning(
        "API_SECRET_KEY is not set or is still the default placeholder. "
        "All requests will be rejected in production. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

# Disable interactive docs in production (set ENABLE_DOCS=true for local dev)
_enable_docs = os.getenv("ENABLE_DOCS", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="SkillRoute Proactive API",
    version="1.0.0",
    docs_url="/api/docs" if _enable_docs else None,
    redoc_url="/api/redoc" if _enable_docs else None,
    openapi_url="/api/openapi.json" if _enable_docs else None,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    # Strict CSP — tighten further once you know your asset CDNs
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )
    # Only send HSTS on HTTPS — the browser ignores it over HTTP
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )
    return response

# ---------------------------------------------------------------------------
# CORS — explicit origins only, no wildcard
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,   # no cookies/sessions in this API
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
    expose_headers=[],
    max_age=600,
)

# ---------------------------------------------------------------------------
# API key authentication
# ---------------------------------------------------------------------------
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def _require_api_key(key: Annotated[str | None, Security(_api_key_header)]) -> str:
    """Dependency — rejects requests without a valid API key."""
    if not API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not configured. Set API_SECRET_KEY.",
        )
    if not key or key != API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return key

# Reusable dependency
AuthDep = Annotated[str, Depends(_require_api_key)]

# ---------------------------------------------------------------------------
# Request Models — with length limits to prevent oversized payloads
# ---------------------------------------------------------------------------

class SynergyRequest(BaseModel):
    ticket_id:   str = Field(..., max_length=32,   pattern=r"^[A-Z0-9\-]+$")
    skills_text: str = Field(..., max_length=1000, min_length=3)

class ROIRequest(BaseModel):
    ticket_id:            str   = Field(..., max_length=32, pattern=r"^[A-Z0-9\-]+$")
    expert_id:            str   = Field(..., max_length=64)
    days_already_delayed: float = Field(..., ge=0, le=3650)   # 0 – 10 years
    estimated_fix_hours:  int   = Field(..., ge=1,   le=2000)
    daily_burn_rate:      float = Field(..., ge=0,   le=1_000_000)
    expert_hourly_rate:   float = Field(..., ge=0,   le=10_000)

class AccountAction(BaseModel):
    user_id:     str = Field(..., max_length=128)
    action_type: str = Field(..., max_length=64,  pattern=r"^[a-zA-Z0-9_\-]+$")
    details:     str = Field(..., max_length=2000)

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    database.init_db()
    logger.info("Database initialised. CORS origins: %s", ALLOWED_ORIGINS)

# ---------------------------------------------------------------------------
# Health — public, no auth required (for load balancers)
# ---------------------------------------------------------------------------
@app.get("/api/health")
@limiter.limit("30/minute")
def health(request: Request):
    return {"status": "ok"}

# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------
@app.get("/api/tickets")
@limiter.limit("60/minute")
def get_tickets(request: Request, _auth: AuthDep):
    return bottleneck_engine.get_all_tickets()

@app.get("/api/bottlenecks")
@limiter.limit("60/minute")
def get_bottlenecks(request: Request, _auth: AuthDep):
    return bottleneck_engine.get_critical_bottlenecks()

@app.get("/api/tickets/{ticket_id}")
@limiter.limit("60/minute")
def get_ticket(ticket_id: str, request: Request, _auth: AuthDep):
    # Validate the path parameter before using it
    if not ticket_id or len(ticket_id) > 32 or not ticket_id.replace("-", "").isalnum():
        raise HTTPException(status_code=400, detail="Invalid ticket ID format.")
    ticket = bottleneck_engine.get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return ticket

# ---------------------------------------------------------------------------
# AI Matching
# ---------------------------------------------------------------------------
@app.post("/api/match")
@limiter.limit("20/minute")
def match_candidates(req: SynergyRequest, request: Request, _auth: AuthDep):
    try:
        candidates = synergy_scorer.run_synergy_search(req.skills_text, n=5)
        return [synergy_scorer.score_breakdown_dict(c) for c in candidates]
    except FileNotFoundError:
        logger.error("FAISS index or metadata not found", exc_info=True)
        raise HTTPException(status_code=503, detail="AI matching service unavailable.")
    except ImportError:
        logger.error("Missing ML dependency", exc_info=True)
        raise HTTPException(status_code=503, detail="AI matching service unavailable.")
    except Exception:
        logger.error("Synergy search failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error.")

# ---------------------------------------------------------------------------
# ROI Calculator
# ---------------------------------------------------------------------------
@app.post("/api/roi")
@limiter.limit("30/minute")
def calculate_roi(req: ROIRequest, request: Request, _auth: AuthDep):
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
    except Exception:
        logger.error("ROI calculation failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error.")

# ---------------------------------------------------------------------------
# Account / Audit Log
# ---------------------------------------------------------------------------
@app.post("/api/account")
@limiter.limit("30/minute")
def handle_account_action(action: AccountAction, request: Request, _auth: AuthDep):
    try:
        database.log_action(action.user_id, action.action_type, action.details)
        return {"status": "success"}
    except Exception:
        logger.error("Failed to log action", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error.")

@app.get("/api/account/actions")
@limiter.limit("20/minute")
def get_account_actions(request: Request, _auth: AuthDep):
    try:
        return database.get_recent_actions()
    except Exception:
        logger.error("Failed to fetch actions", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error.")
