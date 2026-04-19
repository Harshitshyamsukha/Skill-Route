import { useState, useEffect, useMemo } from 'react';
import { api, type ProjectTicket } from '../api';
import TicketCard from '../components/TicketCard';
import TalentModal from '../components/TalentModal';

type StatusFilter = 'All' | 'In Progress' | 'Blocked' | 'Review' | 'Done';
type PriorityFilter = 'All' | 'Critical' | 'High' | 'Medium' | 'Low';

export default function ActiveTickets() {
  const [tickets, setTickets] = useState<ProjectTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeModal, setActiveModal] = useState<ProjectTicket | null>(null);

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('All');
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>('All');
  const [bottleneckOnly, setBottleneckOnly] = useState(false);

  useEffect(() => {
    api.getTickets()
      .then(setTickets)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    return tickets.filter(t => {
      if (statusFilter !== 'All' && t.status !== statusFilter) return false;
      if (priorityFilter !== 'All' && t.priority !== priorityFilter) return false;
      if (bottleneckOnly && !t.is_bottleneck) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          t.title.toLowerCase().includes(q) ||
          t.id.toLowerCase().includes(q) ||
          t.team.toLowerCase().includes(q) ||
          t.assignee.toLowerCase().includes(q) ||
          t.required_skills.some(s => s.toLowerCase().includes(q))
        );
      }
      return true;
    });
  }, [tickets, statusFilter, priorityFilter, bottleneckOnly, search]);

  return (
    <div className="page-wrapper">
      <div className="animate">
        <h1 className="page-title">Active Tickets</h1>
        <p className="page-subtitle">Browse, filter, and route talent across all project tickets</p>
      </div>

      {/* Filters */}
      <div className="filter-bar animate delay-1">
        <input
          className="search-input"
          placeholder="Search by title, team, skill, assignee…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select
          className="filter-select"
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value as StatusFilter)}
        >
          <option value="All">All Statuses</option>
          <option value="In Progress">In Progress</option>
          <option value="Blocked">Blocked</option>
          <option value="Review">Review</option>
          <option value="Done">Done</option>
        </select>
        <select
          className="filter-select"
          value={priorityFilter}
          onChange={e => setPriorityFilter(e.target.value as PriorityFilter)}
        >
          <option value="All">All Priorities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        <button
          className={`btn ${bottleneckOnly ? 'btn-danger' : 'btn-ghost'}`}
          style={{ fontSize: 11, padding: '6px 14px', whiteSpace: 'nowrap' }}
          onClick={() => setBottleneckOnly(v => !v)}
        >
          {bottleneckOnly ? '⚠ Bottlenecks Only' : '⚠ Show Bottlenecks'}
        </button>
      </div>

      {/* Count */}
      {!loading && (
        <div className="text-xs text-muted mb-16">
          Showing {filtered.length} of {tickets.length} tickets
        </div>
      )}

      {/* Error */}
      {error && (
        <div style={{ background: 'rgba(255,87,87,0.08)', border: '0.5px solid rgba(255,87,87,0.25)', borderRadius: 'var(--radius-md)', padding: '12px 16px', fontSize: 13, color: 'rgba(255,150,150,0.9)', marginBottom: 16 }}>
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && <div className="loading-state"><div className="spinner" />Loading tickets…</div>}

      {/* Empty */}
      {!loading && filtered.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          No tickets match your filters.
          <br />
          <button className="btn btn-ghost" style={{ marginTop: 12, fontSize: 12 }} onClick={() => { setSearch(''); setStatusFilter('All'); setPriorityFilter('All'); setBottleneckOnly(false); }}>
            Clear Filters
          </button>
        </div>
      )}

      {/* Cards */}
      {!loading && filtered.map((ticket, i) => (
        <TicketCard
          key={ticket.id}
          ticket={ticket}
          onAllocate={setActiveModal}
          animDelay={Math.min(i + 1, 5)}
        />
      ))}

      {activeModal && (
        <TalentModal ticket={activeModal} onClose={() => setActiveModal(null)} />
      )}
    </div>
  );
}
