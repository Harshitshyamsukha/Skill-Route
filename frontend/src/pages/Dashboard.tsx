import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api, type ProjectTicket, fmt$, priorityBadgeClass, statusClass } from '../api';
import TalentModal from '../components/TalentModal';

export default function Dashboard() {
  const [tickets, setTickets] = useState<ProjectTicket[]>([]);
  const [bottlenecks, setBottlenecks] = useState<ProjectTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeModal, setActiveModal] = useState<ProjectTicket | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [t, b] = await Promise.all([api.getTickets(), api.getBottlenecks()]);
        setTickets(t);
        setBottlenecks(b);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : 'Failed to load data';
        setError(msg);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // KPI calculations
  const totalBurn = tickets.reduce((s, t) => s + t.daily_burn_rate, 0);
  const criticalCount = tickets.filter(t => t.priority === 'Critical').length;
  const blockedCount = tickets.filter(t => t.status === 'Blocked').length;
  const avgBounces = tickets.length
    ? (tickets.reduce((s, t) => s + t.reassignment_bounces, 0) / tickets.length).toFixed(1)
    : '0';

  if (error) {
    return (
      <div className="page-wrapper">
        <div style={{ background: 'rgba(255,87,87,0.08)', border: '0.5px solid rgba(255,87,87,0.25)', borderRadius: 'var(--radius-md)', padding: '16px 20px', fontSize: 13, color: 'rgba(255,150,150,0.9)' }}>
          <strong>Backend connection error:</strong> {error}
          <p style={{ marginTop: 8, color: 'var(--text-muted)', fontSize: 12 }}>Make sure the FastAPI server is running at <code style={{ fontFamily: 'JetBrains Mono', fontSize: 11 }}>http://localhost:8000</code></p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-wrapper">
      {/* Header */}
      <div className="animate">
        <h1 className="page-title">Proactive Dashboard</h1>
        <p className="page-subtitle">Real-time visibility into project bottlenecks and talent allocation opportunities</p>
      </div>

      {/* KPI Grid */}
      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 28 }}>
          {[...Array(4)].map((_, i) => (
            <div key={i} className="kpi-card" style={{ height: 90, opacity: 0.4, animation: 'pulse-border 1.5s ease-in-out infinite' }} />
          ))}
        </div>
      ) : (
        <div className="kpi-grid animate delay-1">
          <div className="kpi-card">
            <div className="kpi-label">Total Active Tickets</div>
            <div className="kpi-value accent">{tickets.length}</div>
            <div className="kpi-delta">{bottlenecks.length} flagged as bottlenecks</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">Daily Burn Rate</div>
            <div className="kpi-value danger">{fmt$(totalBurn)}</div>
            <div className="kpi-delta">Across all active tickets</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">Critical Priority</div>
            <div className="kpi-value danger">{criticalCount}</div>
            <div className="kpi-delta">{blockedCount} currently blocked</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">Avg. Bounces</div>
            <div className="kpi-value amber">{avgBounces}×</div>
            <div className="kpi-delta">Per ticket reassignment</div>
          </div>
        </div>
      )}

      {/* Bottlenecks section */}
      <div className="animate delay-2">
        <div className="flex-between mb-16">
          <div className="section-heading" style={{ marginBottom: 0, flex: 1 }}>
            Critical Bottlenecks
            {bottlenecks.length > 0 && (
              <span className="badge badge-red" style={{ marginLeft: 8 }}>{bottlenecks.length} active</span>
            )}
          </div>
          <Link to="/bottlenecks" className="btn btn-ghost" style={{ fontSize: 11, padding: '5px 12px' }}>
            View All →
          </Link>
        </div>

        {loading && (
          <div className="loading-state"><div className="spinner" />Scanning for bottlenecks…</div>
        )}

        {!loading && bottlenecks.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">✅</div>
            No critical bottlenecks detected. System healthy.
          </div>
        )}

        {!loading && bottlenecks.slice(0, 4).map((ticket, i) => (
          <div key={ticket.id} className={`bottleneck-card animate delay-${i + 1}`}>
            <div className="card-header">
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="card-id mb-4">{ticket.id} · {ticket.team}</div>
                <div className="card-title">{ticket.title}</div>
              </div>
              <div className="card-meta" style={{ flexShrink: 0 }}>
                <span className={`badge ${priorityBadgeClass(ticket.priority)}`}>{ticket.priority}</span>
                <span className={`status-pill ${statusClass(ticket.status)}`}>{ticket.status}</span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 16, marginBottom: 10, flexWrap: 'wrap' }}>
              <span className="text-xs" style={{ color: 'rgba(255,150,150,0.7)' }}>
                🕐 {ticket.days_in_status}d stalled
              </span>
              <span className="text-xs" style={{ color: 'rgba(255,150,150,0.7)' }}>
                🔄 {ticket.reassignment_bounces} bounces
              </span>
              <span className="text-xs" style={{ color: 'rgba(255,150,150,0.7)' }}>
                💸 {fmt$(ticket.daily_burn_rate)}/day burning
              </span>
              <span className="text-xs" style={{ color: 'rgba(255,150,150,0.7)' }}>
                👤 {ticket.assignee}
              </span>
            </div>

            {ticket.bottleneck_reason && (
              <div style={{ fontSize: 11, color: 'rgba(255,150,150,0.75)', marginBottom: 10 }}>
                {ticket.bottleneck_reason}
              </div>
            )}

            <div className="skills-list mb-8">
              {ticket.required_skills.map(s => <span key={s} className="skill-tag">{s}</span>)}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                className="btn btn-primary"
                style={{ fontSize: 11, padding: '6px 14px' }}
                onClick={() => setActiveModal(ticket)}
              >
                ⚡ Route Talent
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Tickets Quick View */}
      {!loading && tickets.length > 0 && (
        <div className="animate delay-3" style={{ marginTop: 32 }}>
          <div className="flex-between mb-16">
            <div className="section-heading" style={{ marginBottom: 0, flex: 1 }}>All Tickets Overview</div>
            <Link to="/active-tickets" className="btn btn-ghost" style={{ fontSize: 11, padding: '5px 12px' }}>
              View All →
            </Link>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '0.5px solid rgba(255,255,255,0.07)' }}>
                  {['ID', 'Title', 'Team', 'Status', 'Priority', 'Days', 'Burn/Day', ''].map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 10, whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tickets.map(t => (
                  <tr key={t.id} style={{ borderBottom: '0.5px solid rgba(255,255,255,0.04)', transition: 'background 0.15s ease' }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.02)')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                  >
                    <td style={{ padding: '10px 12px', fontFamily: 'JetBrains Mono', fontSize: 11, color: 'var(--text-muted)' }}>{t.id}</td>
                    <td style={{ padding: '10px 12px', color: 'var(--text-primary)', maxWidth: 260 }}>
                      <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.title}</div>
                    </td>
                    <td style={{ padding: '10px 12px', color: 'var(--text-secondary)' }}>{t.team}</td>
                    <td style={{ padding: '10px 12px' }}><span className={`status-pill ${statusClass(t.status)}`}>{t.status}</span></td>
                    <td style={{ padding: '10px 12px' }}><span className={`badge ${priorityBadgeClass(t.priority)}`}>{t.priority}</span></td>
                    <td style={{ padding: '10px 12px', fontFamily: 'JetBrains Mono', color: t.days_in_status > 5 ? 'var(--accent-red)' : 'var(--text-secondary)' }}>{t.days_in_status}d</td>
                    <td style={{ padding: '10px 12px', fontFamily: 'JetBrains Mono', color: 'var(--text-secondary)' }}>{fmt$(t.daily_burn_rate)}</td>
                    <td style={{ padding: '10px 12px' }}>
                      {t.is_bottleneck && (
                        <button
                          className="btn btn-primary"
                          style={{ fontSize: 10, padding: '4px 10px' }}
                          onClick={() => setActiveModal(t)}
                        >
                          Route
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeModal && (
        <TalentModal ticket={activeModal} onClose={() => setActiveModal(null)} />
      )}
    </div>
  );
}
