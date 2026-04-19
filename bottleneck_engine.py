"""
bottleneck_engine.py
--------------------
Proactive Bottleneck Detection Engine (Heuristic MVP)

Decoupled from Streamlit — pure Python logic, FastAPI-compatible.
All public functions return plain dicts so FastAPI can serialize them.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime


# ---------------------------------------------------------------------------
# DATA MODEL
# ---------------------------------------------------------------------------

@dataclass
class ProjectTicket:
    id: str
    title: str
    description: str
    status: str                        # "In Progress" | "Blocked" | "Review" | "Done"
    assignee: str
    team: str
    days_in_status: float
    reassignment_bounces: int
    priority: str                      # "Critical" | "High" | "Medium" | "Low"
    estimated_hours: int
    daily_burn_rate: float
    required_skills: List[str] = field(default_factory=list)
    is_bottleneck: bool = False
    bottleneck_reason: str = ""


# ---------------------------------------------------------------------------
# MOCK TICKET DATASET
# ---------------------------------------------------------------------------

_MOCK_TICKETS: List[ProjectTicket] = [
    ProjectTicket(
        id="PROJ-101",
        title="Migrate legacy payment gateway to Stripe",
        description="Requires expert in Stripe API integration, PCI-DSS compliance, Python backend services, and secure tokenization of credit card data.",
        status="In Progress",
        assignee="Ravi Kumar",
        team="Payments",
        days_in_status=7.5,
        reassignment_bounces=8,
        priority="Critical",
        estimated_hours=40,
        daily_burn_rate=1200.0,
        required_skills=["Stripe API", "Python", "PCI-DSS", "Tokenization"],
    ),
    ProjectTicket(
        id="PROJ-102",
        title="Build real-time analytics dashboard with Apache Kafka",
        description="Needs expertise in Apache Kafka, PySpark streaming, AWS Kinesis, and React-based data visualization dashboards.",
        status="In Progress",
        assignee="Priya Nair",
        team="Data Engineering",
        days_in_status=5.0,
        reassignment_bounces=6,
        priority="High",
        estimated_hours=60,
        daily_burn_rate=900.0,
        required_skills=["Apache Kafka", "PySpark", "React", "AWS"],
    ),
    ProjectTicket(
        id="PROJ-103",
        title="Deploy containerized microservices on Kubernetes",
        description="Requires Kubernetes orchestration, Docker containerization, Helm charts, and CI/CD pipeline setup via GitHub Actions.",
        status="Blocked",
        assignee="Ankit Sharma",
        team="DevOps",
        days_in_status=4.0,
        reassignment_bounces=3,
        priority="High",
        estimated_hours=30,
        daily_burn_rate=800.0,
        required_skills=["Kubernetes", "Docker", "Helm", "GitHub Actions"],
    ),
    ProjectTicket(
        id="PROJ-104",
        title="Implement ML fraud detection model in production",
        description="Expert needed in machine learning model deployment, scikit-learn, feature engineering, model monitoring, and MLflow experiment tracking.",
        status="In Progress",
        assignee="Deepika Mehta",
        team="AI/ML",
        days_in_status=9.0,
        reassignment_bounces=11,
        priority="Critical",
        estimated_hours=80,
        daily_burn_rate=1500.0,
        required_skills=["Machine Learning", "Python", "scikit-learn", "MLflow", "Fraud Detection"],
    ),
    ProjectTicket(
        id="PROJ-105",
        title="Revamp SEO strategy and implement schema markup",
        description="Needs digital marketing expert with SEO audit skills, technical schema markup, Google Search Console, and content strategy.",
        status="In Progress",
        assignee="Sneha Patel",
        team="Marketing",
        days_in_status=2.0,
        reassignment_bounces=1,
        priority="Medium",
        estimated_hours=20,
        daily_burn_rate=400.0,
        required_skills=["SEO", "Schema Markup", "Google Search Console", "Content Strategy"],
    ),
    ProjectTicket(
        id="PROJ-106",
        title="Design multi-tenant SaaS billing system",
        description="Requires expertise in SaaS billing architecture, subscription management, Stripe Billing, database schema design for multi-tenancy.",
        status="In Progress",
        assignee="Vikram Singh",
        team="Platform",
        days_in_status=6.0,
        reassignment_bounces=7,
        priority="Critical",
        estimated_hours=55,
        daily_burn_rate=1100.0,
        required_skills=["SaaS Architecture", "Stripe Billing", "PostgreSQL", "Multi-tenancy"],
    ),
    ProjectTicket(
        id="PROJ-107",
        title="Integrate third-party CRM with internal ERP system",
        description="Needs CRM integration expert with Salesforce API, REST webhooks, data transformation, and ERP systems knowledge.",
        status="Review",
        assignee="Meera Iyer",
        team="Integration",
        days_in_status=1.5,
        reassignment_bounces=2,
        priority="Medium",
        estimated_hours=25,
        daily_burn_rate=500.0,
        required_skills=["Salesforce", "REST API", "ERP Integration", "ETL"],
    ),
    ProjectTicket(
        id="PROJ-108",
        title="Security penetration testing for new mobile app",
        description="Requires cybersecurity expert with mobile app pentesting, OWASP Mobile Top 10, Burp Suite, and vulnerability reporting experience.",
        status="In Progress",
        assignee="Arjun Reddy",
        team="Security",
        days_in_status=4.5,
        reassignment_bounces=6,
        priority="High",
        estimated_hours=35,
        daily_burn_rate=850.0,
        required_skills=["Penetration Testing", "Mobile Security", "OWASP", "Burp Suite"],
    ),
    ProjectTicket(
        id="PROJ-109",
        title="Migrate on-premise Oracle DB to AWS Aurora PostgreSQL",
        description="Needs database migration specialist with Oracle to PostgreSQL schema conversion, AWS DMS, data validation, and cutover planning.",
        status="In Progress",
        assignee="Kavita Joshi",
        team="Infrastructure",
        days_in_status=3.5,
        reassignment_bounces=4,
        priority="High",
        estimated_hours=70,
        daily_burn_rate=950.0,
        required_skills=["Oracle", "PostgreSQL", "AWS DMS", "Database Migration"],
    ),
    ProjectTicket(
        id="PROJ-110",
        title="Build NLP-based internal helpdesk chatbot",
        description="Requires NLP engineer with Rasa or Dialogflow, intent classification, entity extraction, Python, and Slack bot integration.",
        status="In Progress",
        assignee="Rahul Gupta",
        team="AI/ML",
        days_in_status=8.0,
        reassignment_bounces=9,
        priority="High",
        estimated_hours=50,
        daily_burn_rate=800.0,
        required_skills=["NLP", "Rasa", "Python", "Dialogflow", "Slack API"],
    ),
]


# ---------------------------------------------------------------------------
# HEURISTIC ENGINE
# ---------------------------------------------------------------------------

_DAYS_THRESHOLD = 3
_BOUNCES_THRESHOLD = 5
_BLOCKED_DAYS_THRESHOLD = 2


def _evaluate_ticket(ticket: ProjectTicket) -> ProjectTicket:
    """Apply heuristic rules and annotate the ticket in-place."""
    # Reset flags so repeated calls are idempotent
    ticket.is_bottleneck = False
    ticket.bottleneck_reason = ""
    reasons = []

    if ticket.status == "In Progress":
        if ticket.days_in_status > _DAYS_THRESHOLD and ticket.reassignment_bounces > _BOUNCES_THRESHOLD:
            ticket.is_bottleneck = True
            reasons.append(
                f"Stalled {ticket.days_in_status:.1f} days in 'In Progress' "
                f"with {ticket.reassignment_bounces} reassignment bounces"
            )

    elif ticket.status == "Blocked":
        if ticket.days_in_status > _BLOCKED_DAYS_THRESHOLD:
            ticket.is_bottleneck = True
            reasons.append(f"Blocked for {ticket.days_in_status:.1f} days with no resolution")

    # Secondary escalation: Critical priority with ANY stall > 5 days
    if ticket.priority == "Critical" and ticket.days_in_status > 5 and not ticket.is_bottleneck:
        ticket.is_bottleneck = True
        reasons.append(
            f"CRITICAL priority ticket stalled for {ticket.days_in_status:.1f} days"
        )

    ticket.bottleneck_reason = " | ".join(reasons)
    return ticket


def get_all_tickets() -> List[dict]:
    """Return all tickets (with bottleneck flags) as a list of dicts for JSON serialization."""
    return [asdict(_evaluate_ticket(t)) for t in _MOCK_TICKETS]


def get_critical_bottlenecks() -> List[dict]:
    """Return only flagged bottleneck tickets sorted by severity (days × bounces)."""
    all_tickets = [_evaluate_ticket(t) for t in _MOCK_TICKETS]
    bottlenecks = [t for t in all_tickets if t.is_bottleneck]
    bottlenecks.sort(key=lambda t: t.days_in_status * (t.reassignment_bounces + 1), reverse=True)
    return [asdict(t) for t in bottlenecks]


def get_ticket_by_id(ticket_id: str) -> Optional[dict]:
    """Look up a single ticket by its ID and return as a dict."""
    all_tickets = [_evaluate_ticket(t) for t in _MOCK_TICKETS]
    ticket = next((t for t in all_tickets if t.id == ticket_id), None)
    return asdict(ticket) if ticket else None
