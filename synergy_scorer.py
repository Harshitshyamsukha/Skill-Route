"""
synergy_scorer.py
-----------------
Advanced Synergy Score Algorithm

Loads the FAISS vector index from dataset/ and enriches each candidate with
three weighted components:

  a) FAISS Semantic Match   → 60% weight  (derived from L2 distance)
  b) Calendar Availability  → 25% weight  (mock: random available hours/week)
  c) Past Project Success   → 15% weight  (mock: random historical success rate)

Final Synergy Score = weighted sum, expressed as 0–100.

Decoupled from Streamlit — pure Python logic, FastAPI-compatible.
Returns plain dicts from score_breakdown_dict() for JSON serialization.
"""

import os
import faiss
import pickle
import numpy as np
import random
from dataclasses import dataclass, field
from typing import List, Tuple

try:
    from sentence_transformers import SentenceTransformer
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False

# ---------------------------------------------------------------------------
# PATHS — resolved relative to the project root
# synergy_scorer.py lives at the project root, so __file__'s directory IS
# the project root. Using dirname twice would go one level too high (e.g.
# into the user's Downloads folder on Windows).
# ---------------------------------------------------------------------------
_ROOT = os.path.dirname(os.path.abspath(__file__))
FAISS_INDEX_PATH = os.path.join(_ROOT, "dataset", "employee_index.faiss")
METADATA_PATH    = os.path.join(_ROOT, "dataset", "employee_metadata.pkl")

# ---------------------------------------------------------------------------
# WEIGHTS
# ---------------------------------------------------------------------------
W_SEMANTIC     = 0.60
W_AVAILABILITY = 0.25
W_SUCCESS_RATE = 0.15

# ---------------------------------------------------------------------------
# DATA MODEL
# ---------------------------------------------------------------------------

@dataclass
class ScoredCandidate:
    id: str
    text_for_llm: str

    semantic_score: float      = 0.0
    availability_score: float  = 0.0
    success_score: float       = 0.0
    synergy_score: float       = 0.0

    available_hours_per_week: int = 0
    past_success_rate: float      = 0.0
    hourly_rate: float = 0.0


# ---------------------------------------------------------------------------
# MODULE-LEVEL SINGLETONS  (loaded once, reused across calls)
# ---------------------------------------------------------------------------
_index:    faiss.Index        = None
_metadata: List[dict]         = None
_model                        = None


def _load_resources():
    global _index, _metadata, _model
    if not os.path.exists(FAISS_INDEX_PATH):
        raise FileNotFoundError(f"FAISS index not found at: {FAISS_INDEX_PATH}")
    if not os.path.exists(METADATA_PATH):
        raise FileNotFoundError(f"Metadata not found at: {METADATA_PATH}")
    if not _ST_AVAILABLE:
        raise ImportError("sentence-transformers is not installed. Run: pip install sentence-transformers")

    if _index is None:
        _index = faiss.read_index(FAISS_INDEX_PATH)
    if _metadata is None:
        with open(METADATA_PATH, "rb") as f:
            _metadata = pickle.load(f)
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")


# ---------------------------------------------------------------------------
# SCORING HELPERS
# ---------------------------------------------------------------------------

def _faiss_distance_to_score(distance: float) -> float:
    score = 100.0 * np.exp(-0.4 * distance)
    return float(np.clip(score, 0.0, 100.0))


def _mock_availability(seed: int) -> Tuple[int, float]:
    rng = random.Random(seed + 42)
    hours = rng.randint(5, 40)
    score = (hours / 40.0) * 100.0
    return hours, score


def _mock_success_rate(seed: int) -> Tuple[float, float]:
    rng = random.Random(seed + 99)
    rate = rng.uniform(0.55, 1.00)
    score = rate * 100.0
    return rate, score


def _mock_hourly_rate(seed: int) -> float:
    rng = random.Random(seed + 7)
    return float(rng.randint(35, 175))


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def run_synergy_search(skills_text: str, n: int = 10) -> List[ScoredCandidate]:
    """
    Query the FAISS index with `skills_text`, retrieve top-n candidates,
    compute the three-component Synergy Score for each, and return a ranked list.
    """
    _load_resources()

    query_vec = np.array([_model.encode(skills_text)], dtype=np.float32)

    k = min(n * 2, len(_metadata))
    distances, indices = _index.search(query_vec, k=k)

    candidates: List[ScoredCandidate] = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue

        meta = _metadata[idx]
        emp_id = meta.get("id", str(idx))
        seed = int(idx)

        sem_score                    = _faiss_distance_to_score(dist)
        avail_hours, av_score        = _mock_availability(seed)
        success_rate, sr_score       = _mock_success_rate(seed)
        hourly_rate                  = _mock_hourly_rate(seed)

        synergy = (
            W_SEMANTIC     * sem_score +
            W_AVAILABILITY * av_score  +
            W_SUCCESS_RATE * sr_score
        )

        candidates.append(ScoredCandidate(
            id=emp_id,
            text_for_llm=meta.get("text_for_llm", ""),
            semantic_score=round(sem_score, 1),
            availability_score=round(av_score, 1),
            success_score=round(sr_score, 1),
            synergy_score=round(synergy, 1),
            available_hours_per_week=avail_hours,
            past_success_rate=round(success_rate, 3),
            hourly_rate=hourly_rate,
        ))

    candidates.sort(key=lambda c: c.synergy_score, reverse=True)
    return candidates[:n]


def score_breakdown_dict(candidate: ScoredCandidate) -> dict:
    """Return a plain dict suitable for JSON serialization."""
    return {
        "id": candidate.id,
        "synergy_score": candidate.synergy_score,
        "semantic_score": candidate.semantic_score,
        "availability_score": candidate.availability_score,
        "success_score": candidate.success_score,
        "available_hours_per_week": candidate.available_hours_per_week,
        "past_success_rate_pct": round(candidate.past_success_rate * 100, 1),
        "hourly_rate": candidate.hourly_rate,
    }
