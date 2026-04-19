import { useState, useEffect } from 'react';
import { api, type ProjectTicket, fmt$, priorityBadgeClass, statusClass } from '../api';
import TalentModal from '../components/TalentModal';

export default function Bottlenecks() {
  const [bottlenecks, setBottlenecks] = useState<ProjectTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeModal, setActiveModal] = useState<ProjectTicket | null>(null);

  useEffect(() => {
    api.getBottlenecks()
      .then(setBottlenecks)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => setLoading(false));
  }, []);

  const totalDailyBurn = bottlenecks.reduce((s, t) => s + t.daily_burn_rate, 0);

  return (
    <div className="page-wrapper">
      <div className="animate">
        <h1 className="page-title">Critical Bottlenecks</h1>
        <p className="page-subtitle">AI-flagged tickets requiring immediate talent routing intervention</p>
      </div>

      {/* Summary strip */}
      {!loading && bottlenecks.length > 0 && (
        <div
          className="animate delay-1"
          style={{
            background: 'rgba(255,87,87,0.05)', border: '0.5px solid rgba(255,87,87,0.25)',
            borderRadius: 'var(--radius-lg)', padding: '14px 20px', marginBottom: 24,
            display: 'flex', gap: 28, alignItems: 'center', flexWrap: 'wrap',
          }}
        >
          <div>
            <div style={{ fontSize: 10, color: 'rgba(255,150,150,0.6)', fontWeight: 600, letterSpacing: '0.07em', textTransform: 'uppercase', marginBottom: 4 }}>Flagged Bottlenecks</div>
            <div style={{ fontSize: 22, fontFamily: 'JetBrains Mono', fontWeight: 700, color: 'var(--accent-red)' }}>{bottlenecks.length}</div>
          </div>
          <div>
            <div style={{ fontSize: 10, color: 'rgba(255,150,150,0.6)', fontWeight: 600, letterSpacing: '0.07em', textTransform: 'uppercase', marginBottom: 4 }}>Combined Daily Burn</div>
            <div style={{ fontSize: 22, fontFamily: 'JetBrains Mono', fontWeight: 700, color: 'var(--accent-red)' }}>{fmt$(totalDailyBurn)}</div>
          </div>
          <div style={{ marginLeft: 'auto', fontSize: 12, color: 'rgba(255,150,150,0.7)' }}>
            Sorted by severity (days × bounces)
          </div>
        </div>
      )}

      {error && (
        <div style={{ background: 'rgba(255,87,87,0.08)', border: '0.5px solid rgba(255,87,87,0.25)', borderRadius: 'var(--radius-md)', padding: '12px 16px', fontSize: 13, color: 'rgba(255,150,150,0.9)', marginBottom: 16 }}>
          {error}
        </div>
      )}

      {loading && <div className="loading-state"><div className="spinner" />Scanning for bottlenecks…</div>}

      {!loading && bottlenecks.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">✅</div>
          No critical bottlenecks detected at this time.
          <br />
          <span style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8, display: 'block' }}>All projects are flowing within normal thresholds.</span>
        </div>
      )}

      {!loading && bottlenecks.map((ticket, i) => (
        <div key={ticket.id} className={`bottleneck-card animate delay-${Math.min(i + 1, 5)}`}>
          <div className="card-header">
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                <span className="card-id">{ticket.id}</span>
                <span className="text-xs text-muted">·</span>
                <span className="text-xs text-muted">{ticket.team}</span>
                <span className="badge badge-red" style={{ marginLeft: 2 }}>BOTTLENECK</span>
              </div>
              <div className="card-title">{ticket.title}</div>
            </div>
            <div className="card-meta" style={{ flexShrink: 0 }}>
              <span className={`badge ${priorityBadgeClass(ticket.priority)}`}>{ticket.priority}</span>
              <span className={`status-pill ${statusClass(ticket.status)}`}>{ticket.status}</span>
            </div>
          </div>

          {/* Severity metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, margin: '14px 0' }}>
            {[
              { label: 'Days Stalled', val: `${ticket.days_in_status}d`, color: 'var(--accent-red)' },
              { label: 'Bounces', val: `${ticket.reassignment_bounces}×`, color: 'var(--accent-red)' },
              { label: 'Burn Rate', val: `${fmt$(ticket.daily_burn_rate)}/d`, color: '#d4a84b' },
              { label: 'Est. Hours', val: `${ticket.estimated_hours}h`, color: 'var(--text-secondary)' },
            ].map(m => (
              <div key={m.label} style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-sm)', padding: '8px 10px', textAlign: 'center' }}>
                <div style={{ fontSize: 9, color: 'rgba(255,150,150,0.6)', fontWeight: 600, letterSpacing: '0.07em', textTransform: 'uppercase', marginBottom: 4 }}>{m.label}</div>
                <div style={{ fontSize: 16, fontFamily: 'JetBrains Mono', fontWeight: 700, color: m.color }}>{m.val}</div>
              </div>
            ))}
          </div>

          {ticket.bottleneck_reason && (
            <div style={{ fontSize: 12, color: 'rgba(255,150,150,0.75)', marginBottom: 10, padding: '8px 10px', background: 'rgba(255,87,87,0.05)', borderRadius: 'var(--radius-sm)' }}>
              ⚠ {ticket.bottleneck_reason}
            </div>
          )}

          <div style={{ marginBottom: 10 }}>
            <div className="text-xs text-muted mb-4">Assignee</div>
            <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>{ticket.assignee}</div>
          </div>

          <div className="skills-list mb-8">
            {ticket.required_skills.map(s => <span key={s} className="skill-tag">{s}</span>)}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
            <button
              className="btn btn-primary"
              onClick={() => setActiveModal(ticket)}
            >
              ⚡ Route Talent Now
            </button>
          </div>
        </div>
      ))}

      {activeModal && (
        <TalentModal ticket={activeModal} onClose={() => setActiveModal(null)} />
      )}
    </div>
  );
}
