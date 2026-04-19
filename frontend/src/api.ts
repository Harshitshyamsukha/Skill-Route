// ─── Types matching the Python dataclasses ──────────────────────────────────

export interface ProjectTicket {
  id: string;
  title: string;
  description: string;
  status: 'In Progress' | 'Blocked' | 'Review' | 'Done';
  assignee: string;
  team: string;
  days_in_status: number;
  reassignment_bounces: number;
  priority: 'Critical' | 'High' | 'Medium' | 'Low';
  estimated_hours: number;
  daily_burn_rate: number;
  required_skills: string[];
  is_bottleneck: boolean;
  bottleneck_reason: string;
}

export interface ScoredCandidate {
  id: string;
  synergy_score: number;
  semantic_score: number;
  availability_score: number;
  success_score: number;
  available_hours_per_week: number;
  past_success_rate_pct: number;
  hourly_rate: number;
}

export interface ROIResult {
  ticket_id: string;
  expert_id: string;
  days_already_delayed: number;
  estimated_fix_hours: number;
  daily_burn_rate: number;
  expert_hourly_rate: number;
  cost_of_delay_so_far: number;
  projected_delay_cost: number;
  cost_to_hire: number;
  net_roi: number;
  roi_percentage: number;
  break_even_days: number;
  recommendation: string;
}

// ─── Config ──────────────────────────────────────────────────────────────────
// VITE_API_BASE_URL   — set to your deployed backend URL in production
// VITE_API_KEY        — set to the API_SECRET_KEY value from your backend .env
//                       These are build-time variables and end up in the JS
//                       bundle, so they are only appropriate for
//                       internal/authenticated deployments. For a public-facing
//                       app add a server-side auth layer instead.
const BASE    = import.meta.env.VITE_API_BASE_URL ?? '';
const API_KEY = import.meta.env.VITE_API_KEY ?? '';

// ─── HTTP helper ─────────────────────────────────────────────────────────────

// Safe error messages — never forward raw server internals to the UI
const SAFE_ERRORS: Record<number, string> = {
  401: 'Authentication failed. Check your API key configuration.',
  403: 'You do not have permission to perform this action.',
  404: 'The requested resource was not found.',
  429: 'Too many requests. Please slow down and try again.',
  500: 'A server error occurred. Please try again later.',
  503: 'A required service is temporarily unavailable.',
};

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      // Send the API key on every request
      ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
    },
    ...options,
  });

  if (!res.ok) {
    // Use a generic safe message — never expose raw server error bodies
    const safeMessage =
      SAFE_ERRORS[res.status] ?? `Request failed (HTTP ${res.status}).`;
    throw new Error(safeMessage);
  }

  return res.json() as Promise<T>;
}

// ─── API surface ─────────────────────────────────────────────────────────────

export const api = {
  getTickets:     () => apiFetch<ProjectTicket[]>('/api/tickets'),
  getBottlenecks: () => apiFetch<ProjectTicket[]>('/api/bottlenecks'),
  getTicket:      (id: string) => apiFetch<ProjectTicket>(`/api/tickets/${id}`),

  matchCandidates: (ticket_id: string, skills_text: string) =>
    apiFetch<ScoredCandidate[]>('/api/match', {
      method: 'POST',
      body: JSON.stringify({ ticket_id, skills_text }),
    }),

  calculateROI: (payload: {
    ticket_id: string; expert_id: string; days_already_delayed: number;
    estimated_fix_hours: number; daily_burn_rate: number; expert_hourly_rate: number;
  }) =>
    apiFetch<ROIResult>('/api/roi', { method: 'POST', body: JSON.stringify(payload) }),
};

// ─── UI helpers ──────────────────────────────────────────────────────────────

export function priorityBadgeClass(p: string): string {
  if (p === 'Critical') return 'badge-red';
  if (p === 'High') return 'badge-amber';
  if (p === 'Medium') return 'badge-blue';
  return 'badge-gray';
}

export function statusClass(s: string): string {
  if (s === 'In Progress') return 'status-progress';
  if (s === 'Blocked') return 'status-blocked';
  if (s === 'Review') return 'status-review';
  if (s === 'Done') return 'status-done';
  return '';
}

export function fmt$(n: number): string {
  const sign = n < 0 ? '-' : '';
  return `${sign}$${Math.abs(n).toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
}

export function parseCandidate(c: ScoredCandidate): { name: string; role: string } {
  const names = [
    'Arjun Mehta','Priya Sharma','Rahul Gupta','Sneha Iyer','Vikram Nair',
    'Deepika Patel','Ankit Reddy','Kavita Joshi','Meera Singh','Ravi Kumar',
    'Sanjay Bose','Pooja Rao','Aditya Shah','Neha Verma','Karthik Murugan',
  ];
  const roles = [
    'Senior Engineer','Staff Engineer','Tech Lead','Principal Engineer',
    'Full-Stack Dev','Backend Specialist','DevOps Engineer','ML Engineer',
    'Security Analyst','Data Engineer','Cloud Architect','Platform Engineer',
  ];
  const seed = parseInt(c.id, 10) || (c.id.charCodeAt(0) ?? 0);
  return { name: names[seed % names.length], role: roles[(seed * 3) % roles.length] };
}
