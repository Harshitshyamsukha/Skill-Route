# SkillRoute — Security Hardening Notes

## Issues found and fixed

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | **Critical** | Live Gemini API key committed in `.env` | Key removed from `.env`. Rotate it immediately at https://aistudio.google.com. Use `.env.example` as your template. |
| 2 | **Critical** | No `.gitignore` — `.env`, database, and FAISS dataset files would be committed | Added `.gitignore` that excludes `.env`, `*.db`, and `dataset/` |
| 3 | **High** | `CORS allow_origins=["*"]` — any website could make authenticated API calls | CORS now reads `ALLOWED_ORIGINS` from `.env`. Set it to your exact frontend domain. |
| 4 | **High** | No authentication on any API endpoint | All `/api/*` routes (except `/api/health`) require `X-API-Key` header matching `API_SECRET_KEY` |
| 5 | **High** | Raw exception messages forwarded to API clients (leaks stack traces, file paths, internal details) | All `except` blocks now log the full error server-side and return a generic safe message to the client |
| 6 | **Medium** | No rate limiting — API was open to abuse/DoS | Added SlowAPI rate limiting (100 req/min general, tighter on expensive endpoints) |
| 7 | **Medium** | No input length or format validation on user-supplied strings | Added Pydantic `Field(max_length=...)` and `pattern=` constraints on all request models |
| 8 | **Medium** | Interactive API docs (`/docs`, `/redoc`) enabled by default | Docs disabled unless `ENABLE_DOCS=true` in environment |
| 9 | **Medium** | No security response headers | Middleware adds `X-Frame-Options`, `X-Content-Type-Options`, `CSP`, `Referrer-Policy`, `HSTS` (on HTTPS) |
| 10 | **Medium** | Frontend displayed raw API error strings to users (could leak server internals) | `api.ts` now maps HTTP status codes to safe user-facing messages |
| 11 | **Low** | No production TLS/HTTPS configuration | Added `nginx.conf.example` with TLS termination, HSTS, and secure proxy config |
| 12 | **Low** | Frontend build had no cache-busting strategy | `vite.config.ts` now uses content-hash filenames |

## Before going live checklist

- [ ] **Rotate your Gemini API key** — the old key from `.env` was in the repo and must be considered compromised. Generate a new one and revoke the old one.
- [ ] Copy `.env.example` → `.env` and fill in real values
- [ ] Generate `API_SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] Set `ALLOWED_ORIGINS` to your exact frontend URL (e.g. `https://skillroute.yourdomain.com`)
- [ ] Copy `frontend/.env.example` → `frontend/.env.local` and set `VITE_API_KEY` to match `API_SECRET_KEY`
- [ ] Get TLS certificate: `sudo certbot --nginx -d yourdomain.com`
- [ ] Copy `nginx.conf.example` → `/etc/nginx/sites-available/skillroute` and enable it
- [ ] Confirm `/api/docs` returns 404 in production (`ENABLE_DOCS` must not be `true`)
- [ ] Run `pip install -r requirements.txt` to install `slowapi`

## Notes on the API key approach

The `VITE_API_KEY` variable is embedded in the frontend JavaScript bundle at build time. This is acceptable for **internal tools** where the users are all trusted colleagues. If you ever make this tool public-facing, replace the API key auth with a proper user authentication system (e.g. OAuth 2.0 / JWT) so that individual users can be authenticated and their sessions can be revoked.
