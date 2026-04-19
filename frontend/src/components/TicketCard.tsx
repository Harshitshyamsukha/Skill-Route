import type { ProjectTicket } from '../api';
import { priorityBadgeClass, statusClass, fmt$ } from '../api';

interface Props {
  ticket: ProjectTicket;
  onAllocate: (ticket: ProjectTicket) => void;
  animDelay?: number;
}

export default function TicketCard({ ticket, onAllocate, animDelay = 0 }: Props) {
  const delayClass = animDelay > 0 ? ` delay-${animDelay}` : '';

  return (
    <div
      className={`ticket-card animate${delayClass}`}
    >
      <div className="card-header">
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="card-id mb-4">{ticket.id}</div>
          <div className="card-title">{ticket.title}</div>
        </div>
        <div className="card-meta" style={{ flexShrink: 0, marginTop: 2 }}>
          <span className={`badge ${priorityBadgeClass(ticket.priority)}`}>{ticket.priority}</span>
          <span className={`status-pill ${statusClass(ticket.status)}`}>{ticket.status}</span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 20, marginBottom: 10, flexWrap: 'wrap' }}>
        <div>
          <div className="text-xs text-muted mb-4">Team</div>
          <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>{ticket.team}</div>
        </div>
        <div>
          <div className="text-xs text-muted mb-4">Assignee</div>
          <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>{ticket.assignee}</div>
        </div>
        <div>
          <div className="text-xs text-muted mb-4">Days in Status</div>
          <div
            className="text-sm font-mono font-bold"
            style={{ color: ticket.days_in_status > 5 ? 'var(--accent-red)' : ticket.days_in_status > 3 ? '#d4a84b' : 'var(--text-primary)' }}
          >
            {ticket.days_in_status}d
          </div>
        </div>
        <div>
          <div className="text-xs text-muted mb-4">Bounces</div>
          <div className="text-sm font-mono font-bold" style={{ color: ticket.reassignment_bounces > 5 ? 'var(--accent-red)' : 'var(--text-primary)' }}>
            {ticket.reassignment_bounces}×
          </div>
        </div>
        <div>
          <div className="text-xs text-muted mb-4">Burn Rate</div>
          <div className="text-sm font-mono" style={{ color: 'var(--text-secondary)' }}>{fmt$(ticket.daily_burn_rate)}/d</div>
        </div>
        <div>
          <div className="text-xs text-muted mb-4">Est. Hours</div>
          <div className="text-sm font-mono" style={{ color: 'var(--text-secondary)' }}>{ticket.estimated_hours}h</div>
        </div>
      </div>

      {ticket.required_skills.length > 0 && (
        <div className="skills-list mb-8">
          {ticket.required_skills.map(s => (
            <span key={s} className="skill-tag">{s}</span>
          ))}
        </div>
      )}

      {ticket.is_bottleneck && ticket.bottleneck_reason && (
        <div style={{
          background: 'rgba(255,87,87,0.06)', border: '0.5px solid rgba(255,87,87,0.2)',
          borderRadius: 'var(--radius-sm)', padding: '6px 10px', marginBottom: 10,
          fontSize: 11, color: 'rgba(255,150,150,0.8)',
        }}>
          ⚠ {ticket.bottleneck_reason}
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 4 }}>
        <button
          className="btn btn-primary"
          style={{ fontSize: 11, padding: '6px 14px' }}
          onClick={() => onAllocate(ticket)}
        >
          ⚡ Route Talent
        </button>
      </div>
    </div>
  );
}
