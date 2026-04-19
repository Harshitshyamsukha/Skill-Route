import { useState, useEffect, useCallback } from 'react';
import { api, type ProjectTicket, type ScoredCandidate, type ROIResult, fmt$, parseCandidate } from '../api';

interface Props {
  ticket: ProjectTicket;
  onClose: () => void;
}

export default function TalentModal({ ticket, onClose }: Props) {
  const [candidates, setCandidates] = useState<ScoredCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<ScoredCandidate | null>(null);
  const [roi, setRoi] = useState<ROIResult | null>(null);
  const [roiLoading, setRoiLoading] = useState(false);

  const fetchCandidates = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.matchCandidates(ticket.id, ticket.description);
      setCandidates(data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to fetch candidates';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [ticket.id, ticket.description]);

  useEffect(() => {
    fetchCandidates();
  }, [fetchCandidates]);

  async function handleSelectCandidate(c: ScoredCandidate) {
    setSelectedCandidate(c);
    setRoi(null);
    setRoiLoading(true);
    try {
      const result = await api.calculateROI({
        ticket_id: ticket.id,
        expert_id: c.id,
        days_already_delayed: ticket.days_in_status,
        estimated_fix_hours: ticket.estimated_hours,
        daily_burn_rate: ticket.daily_burn_rate,
        expert_hourly_rate: c.hourly_rate,
      });
      setRoi(result);
    } catch {
      // ROI optional – silently ignore
    } finally {
      setRoiLoading(false);
    }
  }

  function recommendationClass(rec: string): string {
    if (rec.includes('APPROVE')) return 'recommend-approve';
    if (rec.includes('EVALUATE')) return 'recommend-evaluate';
    return 'recommend-defer';
  }

  // Close on backdrop click
  function handleOverlayClick(e: React.MouseEvent) {
    if (e.target === e.currentTarget) onClose();
  }

  // Close on Escape
  useEffect(() => {
    function handler(e: KeyboardEvent) { if (e.key === 'Escape') onClose(); }
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal-box">
        {/* Header */}
        <div className="modal-header">
          <div>
            <div className="card-id mb-4">{ticket.id} · Talent Routing</div>
            <div className="modal-title">{ticket.title}</div>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        {/* Ticket context */}
        <div style={{ marginBottom: 20 }}>
          <div className="info-row"><span className="info-key">Team</span><span className="info-val">{ticket.team}</span></div>
          <div className="info-row"><span className="info-key">Days Stalled</span><span className="info-val" style={{ color: 'var(--accent-red)' }}>{ticket.days_in_status}d</span></div>
          <div className="info-row"><span className="info-key">Daily Burn Rate</span><span className="info-val">{fmt$(ticket.daily_burn_rate)}/day</span></div>
          <div className="info-row"><span className="info-key">Est. Fix Hours</span><span className="info-val">{ticket.estimated_hours}h</span></div>
          <div className="info-row"><span className="info-key">Current Assignee</span><span className="info-val">{ticket.assignee}</span></div>
        </div>

        {ticket.bottleneck_reason && (
          <div style={{
            background: 'rgba(255,87,87,0.06)', border: '0.5px solid rgba(255,87,87,0.25)',
            borderRadius: 'var(--radius-md)', padding: '10px 14px', marginBottom: 18,
            fontSize: 12, color: 'rgba(255,150,150,0.85)',
          }}>
            ⚠ {ticket.bottleneck_reason}
          </div>
        )}

        <hr />

        {/* Candidates */}
        <div className="section-heading" style={{ marginBottom: 12 }}>AI-Matched Candidates</div>

        {loading && (
          <div className="loading-state">
            <div className="spinner" />
            Running synergy scoring…
          </div>
        )}
        {error && (
          <div style={{ background: 'rgba(255,87,87,0.08)', border: '0.5px solid rgba(255,87,87,0.25)', borderRadius: 'var(--radius-md)', padding: '12px 16px', fontSize: 13, color: 'rgba(255,150,150,0.9)', marginBottom: 12 }}>
            {error}
            <button className="btn btn-ghost" style={{ marginLeft: 12, fontSize: 11, padding: '4px 10px' }} onClick={fetchCandidates}>Retry</button>
          </div>
        )}

        {!loading && !error && candidates.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">🔍</div>
            No candidates found for this ticket.
          </div>
        )}

        {!loading && candidates.map((c, i) => {
          const { name, role } = parseCandidate(c);
          const isSelected = selectedCandidate?.id === c.id;
          return (
            <div
              key={c.id}
              className={`candidate-card${i === 0 ? ' top-pick' : ''}${isSelected ? ' animate' : ''}`}
              onClick={() => handleSelectCandidate(c)}
              style={{ cursor: 'pointer', outline: isSelected ? '1px solid rgba(204,255,0,0.4)' : 'none' }}
            >
              <div className="candidate-header">
                <div>
                  <div className="candidate-name">
                    {i === 0 && <span style={{ color: 'var(--primary)', marginRight: 6, fontSize: 10 }}>★ TOP MATCH</span>}
                    {name}
                  </div>
                  <div className="candidate-role">{role} · {c.available_hours_per_week}h/wk available · ${c.hourly_rate}/hr</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div className="synergy-score">{c.synergy_score.toFixed(0)}</div>
                  <div className="synergy-label">Synergy</div>
                </div>
              </div>

              <div className="score-breakdown">
                {/* Semantic */}
                <div>
                  <div className="score-item-label">Skill Match</div>
                  <div className="score-item-val">{c.semantic_score.toFixed(0)}%</div>
                  <div className="score-track"><div className="score-fill" style={{ width: `${c.semantic_score}%` }} /></div>
                </div>
                {/* Availability */}
                <div>
                  <div className="score-item-label">Availability</div>
                  <div className="score-item-val">{c.availability_score.toFixed(0)}%</div>
                  <div className="score-track"><div className="score-fill score-fill-blue" style={{ width: `${c.availability_score}%` }} /></div>
                </div>
                {/* Success */}
                <div>
                  <div className="score-item-label">Past Success</div>
                  <div className="score-item-val">{c.past_success_rate_pct.toFixed(0)}%</div>
                  <div className="score-track"><div className="score-fill score-fill-amber" style={{ width: `${c.past_success_rate_pct}%` }} /></div>
                </div>
              </div>
            </div>
          );
        })}

        {/* ROI Panel */}
        {(roiLoading || roi) && (
          <>
            <hr />
            <div className="section-heading" style={{ marginBottom: 12 }}>ROI Analysis</div>

            {roiLoading && (
              <div className="loading-state" style={{ padding: '20px' }}>
                <div className="spinner" />
                Calculating ROI…
              </div>
            )}

            {roi && !roiLoading && (
              <>
                <div className="roi-grid">
                  <div className="roi-box">
                    <div className="roi-label">Cost of Delay (so far)</div>
                    <div className="roi-value negative">{fmt$(roi.cost_of_delay_so_far)}</div>
                    <div className="roi-note">Already lost</div>
                  </div>
                  <div className="roi-box">
                    <div className="roi-label">Projected Delay Cost</div>
                    <div className="roi-value negative">{fmt$(roi.projected_delay_cost)}</div>
                    <div className="roi-note">If not resolved</div>
                  </div>
                  <div className="roi-box">
                    <div className="roi-label">Cost to Hire</div>
                    <div className="roi-value">{fmt$(roi.cost_to_hire)}</div>
                    <div className="roi-note">Incl. 1.25× overhead</div>
                  </div>
                  <div className="roi-box">
                    <div className="roi-label">Net ROI</div>
                    <div className={`roi-value ${roi.net_roi >= 0 ? 'positive' : 'negative'}`}>{fmt$(roi.net_roi)}</div>
                    <div className="roi-note">{roi.roi_percentage.toFixed(0)}% return</div>
                  </div>
                  <div className="roi-box">
                    <div className="roi-label">Break-even</div>
                    <div className="roi-value">{roi.break_even_days.toFixed(1)}d</div>
                    <div className="roi-note">Days to payback</div>
                  </div>
                  <div className="roi-box">
                    <div className="roi-label">Expert Rate</div>
                    <div className="roi-value">${roi.expert_hourly_rate}/hr</div>
                    <div className="roi-note">{roi.estimated_fix_hours}h est.</div>
                  </div>
                </div>
                <div className={`recommendation-box ${recommendationClass(roi.recommendation)}`}>
                  {roi.recommendation}
                </div>
              </>
            )}
          </>
        )}

        <hr />
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
          <button className="btn btn-ghost" onClick={onClose}>Close</button>
          {selectedCandidate && (
            <button className="btn btn-primary" onClick={() => {
              alert(`✅ Talent allocation logged for ${parseCandidate(selectedCandidate).name} on ${ticket.id}`);
              onClose();
            }}>
              Allocate Talent
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
