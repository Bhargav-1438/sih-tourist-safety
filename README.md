# SIH Tourist Safety

Predictive Tourist Safety &amp; Resource Optimization prototype — AI-driven risk
clustering, geo-fenced safety zones, SOS, and patrol optimization for SIH.

> **Demo data disclaimer:** all incidents are **synthetic**, generated with a
> fixed seed by `backend/scripts/generate_incidents.py`. They exist only for
> prototype demonstration and ML/risk-clustering evaluation — they are **not**
> real crime statistics.

## Project layout

```
backend/   FastAPI + SQLite API (registration, digital ID, incidents, SOS,
           DBSCAN risk zones, patrol optimization, heatmap/recommendation views)
frontend/  React 18 + Vite + TypeScript app (tourist app + authority dashboard,
           polling integration, Leaflet maps)
docs/      DEVELOPMENT_LOG.md (milestones 1–12) and API_REFERENCE.md
```

## Quick start — backend

```bash
cd backend
python -m venv .venv                      # create the virtual environment
.venv\Scripts\activate                    # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt           # install dependencies
python -m scripts.generate_incidents      # optional: seed the demo incident dataset (150, seed 42)
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend URL: `http://127.0.0.1:8000` · health check: `GET /health`

> No `.env` is required for local development (safe defaults are compiled in).
> Copy `backend/.env.example` to `backend/.env` only if you want to override
> them. `JWT_SECRET_KEY` is a dev-only default — set a real secret anywhere
> other than a local demo.

## Quick start — frontend

```bash
cd frontend
npm install                               # install dependencies
npm run dev                               # Vite dev server
```

Frontend URL: `http://localhost:5173`

Routes: `/` home · `/tourist` tourist app · `/authority` authority dashboard.

The frontend reads `VITE_API_BASE_URL` (default `http://localhost:8000`) and
polling intervals from `frontend/.env.example`:

| Variable | Default |
|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` |
| `VITE_SOS_POLL_MS` | `5000` |
| `VITE_RISK_POLL_MS` | `15000` |
| `VITE_PATROL_POLL_MS` | `30000` |

CORS allows only `http://localhost:5173` while `ENVIRONMENT=development`.

## SIH demo flow

1. Start backend + frontend (above).
2. Open `/tourist`, register a tourist, open their Digital ID / QR.
3. Open `/authority` in a second tab — risk zones, incidents, SOS, and
   patrol recommendations render, and statistics populate from the API.
4. Press **SOS** in the tourist tab (confirm the dialog). Within the SOS
   polling interval (5 s default) the authority dashboard picks up the new
   SOS marker and bumps the SOS statistics **without a page reload**.

## Tests

```bash
cd backend && .venv\Scripts\python -m pytest tests/ -q   # 99 passing
cd frontend && npm run build                             # TypeScript + Vite
```
