"""
app.py  —  SkillRoute Proactive Capacity Engine  v2
====================================================
Visual overhaul: glass morphism (glass3d.dev), spring motion (60fps.design),
AI dashboard components (21st.dev), Inter + JetBrains Mono typefaces.
"""

import time
import os
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv
from google import genai
from google.genai import errors

from bottleneck_engine import get_all_tickets, get_critical_bottlenecks, get_ticket_by_id, ProjectTicket
from synergy_scorer    import run_synergy_search, ScoredCandidate
from roi_calculator    import calculate_roi, format_currency

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SkillRoute — Capacity Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("⚠️  Missing GEMINI_API_KEY in .env")
    st.stop()
client = genai.Client(api_key=GEMINI_API_KEY)

# ─── Load design system CSS ───────────────────────────────────────────────────
_css_path = os.path.join(os.path.dirname(__file__), "assets", "styles.css")
if os.path.exists(_css_path):
    with open(_css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ─── Inline component CSS (overrides + Plotly dark theme) ────────────────────
st.markdown("""
<style>
.js-plotly-plot .plotly .bg { fill: transparent !important; }
.js-plotly-plot .plotly { background: transparent !important; }
[data-testid="stPlotlyChart"] > div { background: transparent !important; }
.sr-ticker-dot {
  width: 7px; height: 7px; border-radius: 50%;
  display: inline-block; margin-right: 8px;
  animation: pulse-dot 2.4s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.5); opacity: 0.6; }
}
.kpi-wrapper-block {
  /* Class we will target from CSS */
}
div[data-testid="stVerticalBlock"]:has(.kpi-card-marker) {
  position: relative;
  transition: transform 0.3s var(--spring-smooth);
}
div[data-testid="stVerticalBlock"]:has(.kpi-card-marker):hover {
  transform: translateY(-4px) scale(1.02);
  z-index: 10;
}
div[data-testid="stVerticalBlock"]:has(.kpi-card-marker):hover .sr-glass-card {
  box-shadow: 0 12px 40px rgba(204,255,0,0.08) !important;
  border-color: rgba(204,255,0,0.3) !important;
}
/* The invisible button hack */
div[data-testid="stVerticalBlock"]:has(.kpi-card-marker) div[data-testid="stButton"] {
  position: absolute !important;
  top: 0; left: 0; 
  width: 100%; height: 100%;
  opacity: 0;
  z-index: 10;
}
div[data-testid="stVerticalBlock"]:has(.kpi-card-marker) div[data-testid="stButton"] button {
  width: 100%; height: 100%; padding:0; margin:0;
}

.center-heading { text-align: center; }
.sr-route-btn button {
  background: #CCFF00 !important;
  border-color: #CCFF00 !important;
  color: #081010 !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  padding: 8px 16px !important;
}
.sr-route-btn button:hover {
  background: #e6ff00 !important;
  border-color: #e6ff00 !important;
  box-shadow: 0 0 16px rgba(204,255,0,0.25) !important;
}
.sr-pass-btn button {
  background: rgba(255,87,87,0.08) !important;
  border-color: rgba(255,87,87,0.25) !important;
  color: rgba(255,150,150,0.9) !important;
}
.sr-find-btn button {
  background: #CCFF00 !important;
  border-color: #CCFF00 !important;
  color: #081010 !important;
  font-size: 14px !important;
  font-weight: 700 !important;
  letter-spacing: 0.02em !important;
  box-shadow: 0 0 24px rgba(204,255,0,0.10) !important;
}
</style>
""", unsafe_allow_html=True)

# ─── LLM helpers ─────────────────────────────────────────────────────────────
def _llm(prompt: str, retries: int = 3) -> str:
    for i in range(retries):
        try:
            return client.models.generate_content(model="gemini-2.5-flash", contents=prompt).text
        except errors.ServerError:
            if i < retries - 1: time.sleep(2 ** i)
            else: return "⚠️ API overloaded — please retry."
        except Exception as e:
            return f"⚠️ Error: {e}"
    return ""

def generate_dossier(ticket: ProjectTicket, c: ScoredCandidate, roi_str: str) -> str:
    return _llm(
        f"You are a talent routing AI. Ticket [{ticket.id}] '{ticket.title}' is bottlenecked "
        f"({ticket.days_in_status} days stalled, {ticket.reassignment_bounces} bounces).\n\n"
        f"Expert profile: {c.text_for_llm}\n"
        f"Synergy Score: {c.synergy_score:.1f}/100 — Semantic {c.semantic_score:.1f}%, "
        f"Availability {c.availability_score:.1f}% ({c.available_hours_per_week} hrs/wk), "
        f"Past Success {c.success_score:.1f}% ({c.past_success_rate*100:.0f}%).\n"
        f"Financials: {roi_str}\n\n"
        "Write a concise 4-section Markdown Match Dossier:\n"
        "1. **Why This Expert Matches** (2–3 sentences)\n"
        "2. **Expert Profile Summary** (2–3 sentences)\n"
        "3. **Strengths** (2–3 bullets)\n"
        "4. **Friction Points** (1–2 bullets)\n"
        "Be sharp, specific, and decision-focused."
    )

def draft_email(ticket: ProjectTicket, c: ScoredCandidate, roi) -> str:
    return _llm(
        f"Draft a professional intro email (<150 words) from an Engineering Manager to "
        f"Expert {c.id} requesting help on '{ticket.title}' (ticket {ticket.id}). "
        f"Stalled {ticket.days_in_status} days, Synergy Score {c.synergy_score:.1f}/100, "
        f"Net ROI {format_currency(roi.net_roi)}, ~{ticket.estimated_hours}h of work, "
        f"{c.available_hours_per_week} hrs/wk available. "
        f"Profile snippet: {c.text_for_llm[:250]}. "
        "Include a subject line. Be direct and professionally urgent."
    )

def extract_skills(desc: str) -> str:
    return _llm(f"Extract core technical skills (comma-separated, no preamble): {desc}")

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 4px 0 20px">
      <div style="font-size:18px;font-weight:700;letter-spacing:-0.03em;color:rgba(255,255,255,0.9)">
        ⚡ SkillRoute
      </div>
      <div style="font-size:11px;color:rgba(255,255,255,0.35);letter-spacing:0.05em;text-transform:uppercase;margin-top:2px">
        Proactive Capacity Engine
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sr-section-heading">Engine Settings</div>', unsafe_allow_html=True)
    top_n = st.slider("Candidates to retrieve", 3, 15, 8)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sr-section-heading">Detection Thresholds</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:12px;color:rgba(255,255,255,0.40);line-height:2.0">
      <span style="color:rgba(255,87,87,0.8)">●</span> &gt;3 days stalled + &gt;5 bounces<br>
      <span style="color:rgba(255,181,71,0.8)">●</span> Critical priority &gt;5 days<br>
      <span style="color:rgba(255,140,87,0.8)">●</span> Blocked &gt;2 days
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sr-section-heading">Data Sources</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:11px;color:rgba(255,255,255,0.30);line-height:1.9;font-family:'JetBrains Mono',monospace">
      dataset/employee_index.faiss<br>
      dataset/employee_metadata.pkl<br>
      model: all-MiniLM-L6-v2
    </div>
    """, unsafe_allow_html=True)

# ─── State Management ────────────────────────────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "dashboard"

def navigate_to(page_name):
    st.session_state["current_page"] = page_name

# ─── Custom Top Navigation ───────────────────────────────────────────────────
st.markdown("""
<div class="sr-top-nav sr-animate">
  <div class="sr-top-nav-logo">SkillRoute</div>
  <div class="sr-top-nav-item active">DASHBOARD</div>
  <div class="sr-top-nav-item">TALENT HUB</div>
  <div class="sr-top-nav-item">BOTTLENECKS</div>
  <div style="flex-grow: 1;"></div>
  <div style="display:flex; gap: 16px; font-size: 16px; color: var(--text-secondary);">
    <span style="cursor:pointer;" title="Notifications">🔔</span>
    <span style="cursor:pointer;" title="Search">🔍</span>
    <span style="cursor:pointer; background:rgba(204,255,0,0.1); padding:4px; border-radius:50%;" title="Profile">👨‍💼</span>
  </div>
</div>
""", unsafe_allow_html=True)

# Return to dashboard button (only visible when not in dashboard)
if st.session_state["current_page"] != "dashboard":
    if st.button("← Back to Dashboard"):
        navigate_to("dashboard")
        st.rerun()

# ─── Page header ─────────────────────────────────────────────────────────────
if st.session_state["current_page"] == "dashboard":
    st.markdown("""
    <div class="sr-animate center-heading" style="padding: 16px 0 32px">
      <h1 style="margin:0 0 8px">Command Center</h1>
      <p style="margin:0;font-size:14px;color:rgba(255,255,255,0.40);letter-spacing:0.01em">
        System operations overview and critical resource allocation.
      </p>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1  —  PROJECT DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state["current_page"] == "dashboard":

    all_tickets  = get_all_tickets()
    bottlenecks  = get_critical_bottlenecks()
    bn_cnt       = len(bottlenecks)
    total        = len(all_tickets)
    critical_cnt = sum(1 for t in all_tickets if t.priority == "Critical")
    healthy_cnt  = total - bn_cnt

    # ── KPI bar ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="sr-section-heading sr-animate">Project Health</div>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    
    def render_kpi(col, title, value, subtext, subtext_color, icon, key):
        with col:
            with st.container():
                st.markdown('<div class="kpi-card-marker" style="display:none;"></div>', unsafe_allow_html=True)
                html = f"""
                <div class="sr-glass-card" style="padding:18px 20px; display:flex; flex-direction:column; justify-content:space-between; height:120px; margin-bottom:0;">
                  <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="font-size:11px; font-weight:600; letter-spacing:0.05em; color:var(--text-secondary); text-transform:uppercase;">{title}</div>
                    <div style="font-size:16px;">{icon}</div>
                  </div>
                  <div>
                    <div style="font-size:32px; font-weight:700; font-family:'Space Grotesk', sans-serif; line-height:1.2; letter-spacing:-0.02em;">{value}</div>
                    <div style="font-size:11px; color:{subtext_color}; margin-top:4px;">{subtext}</div>
                  </div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)
                if st.button(f"Hidden_{key}", key=key, help=f"Filter by {title}"):
                    if key == "btn_btn_cnt":
                        st.session_state["dashboard_filter"] = "Bottlenecks"
                    elif key == "btn_crit_cnt":
                        st.session_state["dashboard_filter"] = "Critical"
                    else:
                        st.session_state["dashboard_filter"] = "All"
                    st.rerun()

    filter_state = st.session_state.get("dashboard_filter", "All")
    if filter_state != "All":
        st.markdown(f"<div style='font-size:11px; font-weight:600; color:var(--accent-green); margin-bottom:12px; border:0.5px solid rgba(204,255,0,0.3); background:rgba(204,255,0,0.05); padding:6px 12px; border-radius:6px; display:inline-block;'>Current View: Filtering for {filter_state} Tickets</div>", unsafe_allow_html=True)

    render_kpi(k1, "Active Tickets", total, "+12% from last week", "var(--text-muted)", "📋", "btn_total")
    render_kpi(k2, "Bottlenecks", bn_cnt, "Action Required", "var(--accent-red)", "⚠️", "btn_btn_cnt")
    render_kpi(k3, "Critical Priority", critical_cnt, "Requiring immediate attention", "var(--text-muted)", "❗", "btn_crit_cnt")
    render_kpi(k4, "System Health", f"{98.4 if healthy_cnt/total > 0.9 else 80.0}%", "Optimal performance", "var(--accent-green)", "📈", "btn_health")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Bottleneck alerts ─────────────────────────────────────────────────────
    display_bottlenecks = bottlenecks
    if filter_state == "Critical":
        display_bottlenecks = [t for t in bottlenecks if t.priority == "Critical"]
        
    if display_bottlenecks:
        st.markdown(f"""
        <div class="sr-section-heading sr-animate sr-animate-d1" style="margin-top:24px">
          <span class="sr-ticker-dot" style="background:rgba(255,87,87,0.9)"></span>
          Critical Bottlenecks &nbsp;<span style="color:rgba(255,87,87,0.7)">({len(display_bottlenecks)} flagged)</span>
        </div>
        """, unsafe_allow_html=True)

        for i, ticket in enumerate(display_bottlenecks):
            priority_colors = {"Critical": "sr-badge-red", "High": "sr-badge-amber",
                               "Medium": "sr-badge-amber", "Low": "sr-badge-gray"}
            p_cls = priority_colors.get(ticket.priority, "sr-badge-gray")

            st.markdown(f"""
            <div class="sr-bottleneck-card sr-animate" style="animation-delay:{0.05*i}s;">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
                <span class="sr-badge" style="background:rgba(255,255,255,0.06); border:0.5px solid rgba(255,255,255,0.1); padding:5px 12px; font-weight:600;"><span style="color:var(--accent-red); margin-right:6px; font-size:8px; vertical-align:middle;">●</span> {ticket.priority} IMPACT</span>
                <span style="color:var(--text-muted); font-size:18px;">❖</span>
              </div>
              <div style="font-size:22px;font-weight:700;font-family:'Space Grotesk',sans-serif;color:var(--text-primary);margin-bottom:12px;letter-spacing:-0.02em;">
                {ticket.title}
              </div>
              <div style="font-size:13px;line-height:1.6;color:var(--text-secondary);margin-bottom:24px; max-width:90%;">
                {ticket.bottleneck_reason if ticket.bottleneck_reason else ticket.description[:200] + '...'}
              </div>
              <div style="display:flex; align-items:center;">
                <span style="color:var(--text-muted); font-size:13px; font-weight:500;">⏱ Stalled for {ticket.days_in_status} days</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Move button to align right under the card
            col_exp, col_empty, col_btn = st.columns([4, 1.5, 1.5])
            with col_exp:
                with st.expander(f"Details  ·  {ticket.id}"):
                    dc1, dc2 = st.columns(2)
                    with dc1:
                        st.markdown(f"**Description**\n\n{ticket.description}")
                        st.markdown(f"**Required Skills**\n\n{', '.join(ticket.required_skills)}")
                    with dc2:
                        st.markdown(f"**Estimated Hours** · `{ticket.estimated_hours}h`")
                        st.markdown(f"**Daily Burn Rate** · `{format_currency(ticket.daily_burn_rate)}/day`")
                        st.markdown(f"**Sunk Cost** · `{format_currency(ticket.daily_burn_rate * ticket.days_in_status)}`")
            with col_btn:
                st.markdown('<div class="sr-route-btn">', unsafe_allow_html=True)
                if st.button("Allocate Talent", key=f"route_{ticket.id}"):
                    st.session_state.update({
                        "routed_ticket_id": ticket.id,
                        "candidates": None,
                        "selected_candidate_idx": 0,
                        "email_draft": None,
                        "dossier": None,
                        "current_page": "talent_routing"
                    })
                    st.toast(f"{ticket.id} queued — Routing...", icon="🎯")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="sr-glass-card" style="text-align:center;padding:32px">
          <div style="font-size:22px;margin-bottom:8px">✅</div>
          <div style="font-size:14px;font-weight:500;color:rgba(255,255,255,0.7)">All tickets within healthy thresholds</div>
          <div style="font-size:12px;color:rgba(255,255,255,0.35);margin-top:4px">No bottlenecks detected</div>
        </div>
        """, unsafe_allow_html=True)

    # ── All tickets list ──────────────────────────────────────────────────────
    st.markdown("""
    <div class="sr-section-heading sr-animate" style="margin-top:32px">Active Tickets</div>
    """, unsafe_allow_html=True)

    STATUS_CLS = {"In Progress": "sr-status-progress", "Blocked": "sr-status-blocked",
                  "Review": "sr-status-review", "Done": "sr-status-done"}
    PRI_DOT    = {"Critical": "rgba(255,87,87,0.9)", "High": "rgba(255,140,87,0.9)",
                  "Medium": "rgba(255,181,71,0.9)", "Low": "rgba(255,255,255,0.3)"}

    display_all = all_tickets
    if filter_state == "Critical":
        display_all = [t for t in all_tickets if t.priority == "Critical"]
    elif filter_state == "Bottlenecks":
        display_all = [t for t in all_tickets if t.is_bottleneck]

    if not display_all:
        st.markdown("<p style='color:var(--text-muted); font-size:13px;'>No tickets match current filter.</p>", unsafe_allow_html=True)

    for ticket in display_all:
        card_cls = "sr-bottleneck-card" if ticket.is_bottleneck else "sr-glass-card"
        dot_col  = PRI_DOT.get(ticket.priority, "rgba(255,255,255,0.3)")
        st_cls   = STATUS_CLS.get(ticket.status, "sr-badge-gray")

        st.markdown(f"""
        <div class="{card_cls}" style="padding:14px 18px">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:12px">
            <div style="display:flex;align-items:center;gap:10px;min-width:0">
              <span style="width:7px;height:7px;border-radius:50%;background:{dot_col};flex-shrink:0"></span>
              <span style="font-size:10px;color:rgba(255,255,255,0.30);font-family:'JetBrains Mono',monospace;flex-shrink:0">{ticket.id}</span>
              <span style="font-size:13px;font-weight:500;color:rgba(255,255,255,0.82);
                           white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{ticket.title}</span>
            </div>
            <span class="sr-status {st_cls}" style="flex-shrink:0">{ticket.status}</span>
          </div>
          <div style="display:flex;gap:16px;margin-top:8px;font-size:11px;color:rgba(255,255,255,0.35)">
            <span>👤 {ticket.assignee}</span>
            <span>🏢 {ticket.team}</span>
            <span>⏱ {ticket.days_in_status}d</span>
            <span>🔄 {ticket.reassignment_bounces}</span>
            <span>💰 {format_currency(ticket.daily_burn_rate)}/d</span>
          </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2  —  TALENT ROUTING
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state["current_page"] == "talent_routing":
    st.markdown("""
    <div class="sr-animate center-heading" style="padding: 16px 0 32px">
      <h1 style="margin:0 0 8px">Talent Dispatch</h1>
      <p style="margin:0;font-size:14px;color:rgba(255,255,255,0.40);letter-spacing:0.01em">
        AI-driven matching and resource allocation.
      </p>
    </div>
    """, unsafe_allow_html=True)

    all_tickets_t2  = get_all_tickets()
    bottleneck_ids  = {t.id for t in get_critical_bottlenecks()}
    all_ids         = [t.id for t in all_tickets_t2]

    default_id = st.session_state.get("routed_ticket_id",
                    next((t.id for t in get_critical_bottlenecks()), all_ids[0]))
    if default_id not in all_ids:
        default_id = all_ids[0]

    selected_id = st.selectbox(
        "Select ticket",
        options=all_ids,
        index=all_ids.index(default_id),
        format_func=lambda tid: f"{'⚡ ' if tid in bottleneck_ids else '   '}{tid}  —  {get_ticket_by_id(tid).title}",
        key="ticket_select",
        label_visibility="collapsed",
    )

    ticket = get_ticket_by_id(selected_id)

    if st.session_state.get("last_routed_id") != selected_id:
        st.session_state.update({
            "candidates": None, "selected_candidate_idx": 0,
            "email_draft": None, "dossier": None,
            "last_routed_id": selected_id,
        })

    # ── Ticket info ───────────────────────────────────────────────────────────
    is_bn    = ticket.is_bottleneck
    card_cls = "sr-bottleneck-card" if is_bn else "sr-glass-card"
    badge    = '<span class="sr-badge sr-badge-red">⚠ bottleneck</span>' if is_bn \
               else '<span class="sr-badge sr-badge-blue">active</span>'
    p_cls    = {"Critical":"sr-badge-red","High":"sr-badge-amber"}.get(ticket.priority,"sr-badge-gray")

    st.markdown(f"""
    <div class="{card_cls} sr-animate">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap">
        {badge}
        <span class="sr-badge {p_cls}">{ticket.priority}</span>
        <span style="font-size:11px;color:rgba(255,255,255,0.30);font-family:'JetBrains Mono',monospace">{ticket.id}</span>
      </div>
      <div style="font-size:16px;font-weight:600;color:rgba(255,255,255,0.90);margin-bottom:10px;letter-spacing:-0.02em">
        {ticket.title}
      </div>
      <div style="display:flex;gap:20px;flex-wrap:wrap;font-size:12px;color:rgba(255,255,255,0.42)">
        <span>👤 {ticket.assignee}</span>
        <span>🏢 {ticket.team}</span>
        <span>⏱ <strong style="color:rgba(255,181,71,0.8)">{ticket.days_in_status} days</strong> stalled</span>
        <span>🔄 <strong style="color:rgba(255,87,87,0.7)">{ticket.reassignment_bounces} bounces</strong></span>
        <span>💰 burn: <strong style="color:rgba(255,255,255,0.60)">{format_currency(ticket.daily_burn_rate)}/day</strong></span>
      </div>
      <div style="margin-top:12px;font-size:12px;color:rgba(255,255,255,0.38)">
        <strong style="color:rgba(255,255,255,0.50)">Skills needed:</strong>  {', '.join(ticket.required_skills)}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Search button ─────────────────────────────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([2, 2, 2])
    with mid:
        st.markdown('<div class="sr-find-btn">', unsafe_allow_html=True)
        search_btn = st.button("⚡  Find & Score Experts", key="search_btn")
        st.markdown('</div>', unsafe_allow_html=True)

    if search_btn:
        with st.spinner("Extracting skills → querying FAISS → computing Synergy Scores…"):
            sq = extract_skills(ticket.description)
            candidates = run_synergy_search(sq, n=top_n)
        st.session_state.update({
            "candidates": candidates, "skills_query": sq,
            "selected_candidate_idx": 0, "email_draft": None, "dossier": None,
        })

    # ── Results ───────────────────────────────────────────────────────────────
    if st.session_state.get("candidates"):
        candidates = st.session_state["candidates"]
        cur_idx    = st.session_state.get("selected_candidate_idx", 0)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        sq = st.session_state.get("skills_query", "")
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">
          <span class="sr-badge sr-badge-gray">Skills extracted</span>
          <span style="font-size:12px;color:rgba(255,255,255,0.45);font-family:'JetBrains Mono',monospace">{sq[:120]}</span>
        </div>
        <div style="font-size:11px;color:rgba(255,255,255,0.30);margin-bottom:20px">
          {len(candidates)} candidates ranked · showing {cur_idx+1} of {len(candidates)}
        </div>
        """, unsafe_allow_html=True)

        if cur_idx >= len(candidates):
            st.markdown("""
            <div class="sr-glass-card" style="text-align:center;padding:28px">
              <div style="font-size:13px;color:rgba(255,255,255,0.50)">All candidates reviewed — try a different ticket or re-run the search.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            c: ScoredCandidate = candidates[cur_idx]

            roi = calculate_roi(
                ticket_id=ticket.id, expert_id=c.id,
                days_already_delayed=ticket.days_in_status,
                estimated_fix_hours=ticket.estimated_hours,
                daily_burn_rate=ticket.daily_burn_rate,
                expert_hourly_rate=c.hourly_rate,
            )
            roi_str = (f"Sunk cost {format_currency(roi.cost_of_delay_so_far)}, "
                       f"projected delay {format_currency(roi.projected_delay_cost)}, "
                       f"cost to hire {format_currency(roi.cost_to_hire)}, "
                       f"net ROI {format_currency(roi.net_roi)} ({roi.roi_percentage:.0f}%)")

            # ── Three-column layout ───────────────────────────────────────────
            col_g, col_score, col_roi = st.columns([1.3, 1.5, 1.5])

            # — Gauge ——————————————————————————————————————————————————————————
            with col_g:
                gauge_col = ("#00D68F" if c.synergy_score >= 70
                             else "#FFB547" if c.synergy_score >= 50
                             else "#FF5757")
                fig = go.Figure(go.Indicator(
                    mode   = "gauge+number",
                    value  = c.synergy_score,
                    number = {"suffix": "%", "font": {"size": 34, "color": gauge_col, "family": "JetBrains Mono"}},
                    title  = {"text": "Synergy Score", "font": {"size": 12, "color": "rgba(255,255,255,0.40)", "family": "Inter"}},
                    gauge  = {
                        "axis": {"range": [0, 100], "tickcolor": "rgba(255,255,255,0.15)",
                                 "tickfont": {"size": 9, "color": "rgba(255,255,255,0.25)"}},
                        "bar":  {"color": gauge_col, "thickness": 0.22},
                        "bgcolor": "rgba(255,255,255,0.03)",
                        "borderwidth": 0,
                        "steps": [
                            {"range": [0,  50], "color": "rgba(255,87,87,0.06)"},
                            {"range": [50, 75], "color": "rgba(255,181,71,0.06)"},
                            {"range": [75, 100],"color": "rgba(0,214,143,0.06)"},
                        ],
                        "threshold": {"line": {"color": gauge_col, "width": 1.5}, "thickness": 0.75, "value": c.synergy_score},
                    },
                ))
                fig.update_layout(
                    height=210, margin=dict(l=10, r=10, t=30, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font={"color": "rgba(255,255,255,0.6)"},
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                st.markdown(f"""
                <div class="sr-glass-card" style="padding:14px 16px;margin-top:0">
                  <div style="font-size:14px;font-weight:600;color:rgba(255,255,255,0.85);margin-bottom:8px">
                    Employee {c.id}
                  </div>
                  <div style="font-size:11px;color:rgba(255,255,255,0.38);line-height:1.9">
                    🔗 linkedin.com/in/employee-{c.id}<br>
                    📧 emp_{c.id}@company.com<br>
                    💵 <span style="font-family:'JetBrains Mono',monospace;color:rgba(255,255,255,0.55)">${c.hourly_rate:.0f}/hr</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            # — Score breakdown ——————————————————————————————————————————————
            with col_score:
                st.markdown("""
                <div class="sr-section-heading" style="margin-bottom:16px">Score Breakdown</div>
                """, unsafe_allow_html=True)

                components = [
                    ("Semantic Match",  c.semantic_score,    "60%", f"{c.semantic_score:.1f}%"),
                    ("Availability",    c.availability_score,"25%", f"{c.available_hours_per_week} hrs/wk free"),
                    ("Past Success",    c.success_score,     "15%", f"{c.past_success_rate*100:.0f}% rate"),
                ]
                for label, score, weight, detail in components:
                    st.markdown(f"""
                    <div style="margin-bottom:16px">
                      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px">
                        <span style="font-size:12px;font-weight:500;color:rgba(255,255,255,0.70)">{label}</span>
                        <div style="display:flex;align-items:center;gap:8px">
                          <span style="font-size:10px;color:rgba(255,255,255,0.28)">{weight} weight</span>
                          <span style="font-size:12px;font-weight:600;color:rgba(255,255,255,0.80);
                                       font-family:'JetBrains Mono',monospace">{score:.1f}%</span>
                        </div>
                      </div>
                      <div class="sr-score-track">
                        <div class="sr-score-fill" style="width:{int(score)}%"></div>
                      </div>
                      <div style="font-size:10px;color:rgba(255,255,255,0.28);margin-top:3px">{detail}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="sr-glass-card" style="padding:12px 14px;margin-top:4px;text-align:center">
                  <div style="font-size:10px;color:rgba(255,255,255,0.30);text-transform:uppercase;
                              letter-spacing:0.08em;margin-bottom:4px">Weighted Synergy</div>
                  <div style="font-size:28px;font-weight:700;font-family:'JetBrains Mono',monospace;
                              color:{gauge_col};letter-spacing:-0.03em">{c.synergy_score:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)

            # — ROI panel ——————————————————————————————————————————————————————
            with col_roi:
                st.markdown("""
                <div class="sr-section-heading" style="margin-bottom:16px">Financial Impact</div>
                """, unsafe_allow_html=True)

                roi_items = [
                    ("Sunk Cost of Delay",   format_currency(roi.cost_of_delay_so_far), "already lost",     ""),
                    ("Projected Loss",        format_currency(roi.projected_delay_cost), "if unresolved",    ""),
                    ("Cost to Hire",          format_currency(roi.cost_to_hire),          "incl 1.25× overhead",""),
                    ("Net ROI",               format_currency(roi.net_roi),               f"{roi.roi_percentage:.0f}% return",
                     "positive" if roi.net_roi >= 0 else "negative"),
                    ("Break-even",            f"{roi.break_even_days:.1f} days",          "payback period",   ""),
                ]
                for label, value, note, val_cls in roi_items:
                    v_color = ("rgba(0,214,143,0.9)" if val_cls == "positive"
                               else "rgba(255,87,87,0.9)" if val_cls == "negative"
                               else "rgba(255,255,255,0.82)")
                    st.markdown(f"""
                    <div class="sr-roi-box">
                      <div class="sr-roi-label">{label}</div>
                      <div class="sr-roi-value" style="color:{v_color}">{value}</div>
                      <div class="sr-roi-note">{note}</div>
                    </div>
                    """, unsafe_allow_html=True)

                rec_color = ("rgba(0,214,143,0.9)" if "APPROVE" in roi.recommendation
                             else "rgba(255,181,71,0.9)" if "EVALUATE" in roi.recommendation
                             else "rgba(255,87,87,0.9)")
                st.markdown(f"""
                <div style="margin-top:10px;font-size:12px;font-weight:600;
                            color:{rec_color};text-align:center;
                            padding:10px;border-radius:10px;
                            background:rgba(255,255,255,0.03);
                            border:0.5px solid {rec_color.replace('0.9','0.2')}">
                  {roi.recommendation}
                </div>
                """, unsafe_allow_html=True)

            # ── Dossier ───────────────────────────────────────────────────────
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="sr-section-heading">AI Match Dossier</div>', unsafe_allow_html=True)

            if st.session_state.get("dossier") is None:
                with st.spinner("Generating dossier via Gemini 2.5 Flash…"):
                    st.session_state["dossier"] = generate_dossier(ticket, c, roi_str)

            st.markdown(f"""
            <div class="sr-glass-card" style="padding:18px 20px">
              <div style="font-size:11px;color:rgba(255,255,255,0.30);margin-bottom:10px;
                          font-family:'JetBrains Mono',monospace">
                skills queried: {sq[:100]}
              </div>
            """, unsafe_allow_html=True)
            st.markdown(st.session_state["dossier"])
            st.markdown("</div>", unsafe_allow_html=True)

            # ── Action row ────────────────────────────────────────────────────
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            a1, a2, a3 = st.columns(3)

            with a1:
                if st.button("✅  Approve & Draft Email", key="approve_btn"):
                    with st.spinner("Drafting email via Gemini…"):
                        st.session_state["email_draft"] = draft_email(ticket, c, roi)
            with a2:
                st.markdown('<div class="sr-pass-btn">', unsafe_allow_html=True)
                if st.button("✗  Pass — Next Candidate", key="pass_btn"):
                    st.session_state.update({
                        "selected_candidate_idx": cur_idx + 1,
                        "email_draft": None, "dossier": None,
                    })
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with a3:
                if st.button("↺  Re-run Search", key="rerun_btn"):
                    st.session_state.update({
                        "candidates": None, "selected_candidate_idx": 0,
                        "email_draft": None, "dossier": None,
                    })
                    st.rerun()

            if st.session_state.get("email_draft"):
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                st.markdown('<div class="sr-section-heading">Suggested Intro Email</div>', unsafe_allow_html=True)
                st.text_area("", value=st.session_state["email_draft"], height=210, key="email_display", label_visibility="collapsed")

    else:
        # Empty state — 21st.dev style
        st.markdown("""
        <div class="sr-glass-card sr-animate" style="text-align:center;padding:60px 24px;margin-top:24px">
          <div style="width:48px;height:48px;border-radius:14px;
                      background:rgba(0,214,143,0.08);border:0.5px solid rgba(0,214,143,0.20);
                      display:flex;align-items:center;justify-content:center;
                      margin:0 auto 16px;font-size:22px">🎯</div>
          <div style="font-size:15px;font-weight:600;color:rgba(255,255,255,0.65);margin-bottom:6px">
            Ready to route talent
          </div>
          <div style="font-size:12px;color:rgba(255,255,255,0.30);max-width:320px;margin:0 auto;line-height:1.7">
            Select a ticket above and click <strong style="color:rgba(0,214,143,0.7)">Find & Score Experts</strong>
            to begin routing. Bottleneck tickets are pre-selected when routed from the Dashboard tab.
          </div>
        </div>
        """, unsafe_allow_html=True)
