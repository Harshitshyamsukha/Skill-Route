"""
roi_calculator.py
-----------------
ROI & Cost-of-Delay Calculator

Decoupled from Streamlit — pure Python logic, FastAPI-compatible.
calculate_roi() now returns a plain dict for JSON serialization.
"""

from dataclasses import dataclass, asdict


# ---------------------------------------------------------------------------
# DATA MODELS
# ---------------------------------------------------------------------------

@dataclass
class ROIResult:
    ticket_id: str
    expert_id: str
    days_already_delayed: float
    estimated_fix_hours: int
    daily_burn_rate: float
    expert_hourly_rate: float

    cost_of_delay_so_far: float
    projected_delay_cost: float
    cost_to_hire: float
    net_roi: float
    roi_percentage: float
    break_even_days: float
    recommendation: str


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

DELAY_MULTIPLIER     = 2.0
OVERHEAD_MULTIPLIER  = 1.25


# ---------------------------------------------------------------------------
# CALCULATOR
# ---------------------------------------------------------------------------

def calculate_roi(
    ticket_id: str,
    expert_id: str,
    days_already_delayed: float,
    estimated_fix_hours: int,
    daily_burn_rate: float,
    expert_hourly_rate: float,
) -> dict:
    """
    Core ROI calculation. Returns a plain dict for JSON serialization.
    All monetary values are in USD.
    """

    cost_of_delay_so_far = days_already_delayed * daily_burn_rate

    projected_additional_days = days_already_delayed * DELAY_MULTIPLIER
    projected_delay_cost = projected_additional_days * daily_burn_rate

    cost_to_hire = estimated_fix_hours * expert_hourly_rate * OVERHEAD_MULTIPLIER

    net_roi = projected_delay_cost - cost_to_hire

    roi_pct = (net_roi / cost_to_hire * 100.0) if cost_to_hire > 0 else 0.0

    break_even = (cost_to_hire / daily_burn_rate) if daily_burn_rate > 0 else 0.0

    if roi_pct >= 50:
        recommendation = "✅ APPROVE — Strong positive ROI"
    elif roi_pct >= 0:
        recommendation = "🟡 EVALUATE — Marginal ROI; validate estimates"
    else:
        recommendation = "🔴 DEFER — Cost to hire exceeds projected savings"

    result = ROIResult(
        ticket_id=ticket_id,
        expert_id=expert_id,
        days_already_delayed=days_already_delayed,
        estimated_fix_hours=estimated_fix_hours,
        daily_burn_rate=daily_burn_rate,
        expert_hourly_rate=expert_hourly_rate,
        cost_of_delay_so_far=round(cost_of_delay_so_far, 2),
        projected_delay_cost=round(projected_delay_cost, 2),
        cost_to_hire=round(cost_to_hire, 2),
        net_roi=round(net_roi, 2),
        roi_percentage=round(roi_pct, 1),
        break_even_days=round(break_even, 1),
        recommendation=recommendation,
    )
    return asdict(result)


def format_currency(value: float) -> str:
    """Format a USD value with commas and dollar sign."""
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"
