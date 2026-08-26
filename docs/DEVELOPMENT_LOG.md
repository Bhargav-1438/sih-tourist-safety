# SIH Tourist Safety — Development Log

## 1. Project Overview

The SIH Tourist Safety prototype is a backend focused on issuing and verifying
cryptographically signed digital IDs for tourists. The prototype supports a
minimal workflow:

1. A tourist registers with a name and an Indian mobile phone number.
2. The backend issues a signed JWT digital ID for that tourist, along with a
   QR code that encodes the token.
3. A verifier submits the token to the backend; the backend validates the
   signature, checks expiration, and confirms the tourist still exists in the
   database.

The project targets the problem statement: *Predictive Tourist Safety &
Resource Optimization System using AI-Driven Risk Clustering and Geo-Fencing*.
Only the foundational, registration, and digital-ID/QR layers have been
implemented so far. Features such as SOS, risk clustering, DBSCAN, patrol
optimization, live location, and the React + Leaflet frontend are planned for
future milestones and are **not yet implemented**.

## 2. Current Technology Stack

### Implemented technologies

| Category | Technology | Details |
|---|---|---|
| Language | Python | 3.13.14 (via `.venv`) |
| Web framework | FastAPI | 0.141.1 |
| ASGI server | Uvicorn | 0.52.4 (+ `uvicorn[standard]`) |
| ORM | SQLAlchemy | 2.0.52 |
| Validation | Pydantic | 2.13.4 (bundled with FastAPI) |
| Database | SQLite | Local file via SQLAlchemy ORM |
| JWT | PyJWT | 2.13.0 |
| QR codes | qrcode + Pillow | qrcode 8.2, Pillow 12.3.0 |
| HTTP client (tests) | httpx | 0.28.1 |
| Test framework | pytest | 9.1.1 |
| Env config | python-dotenv | 1.2.3 |

### Technologies present in the project but not yet activated

- **Starlette** (1.6.0): transitive dependency of FastAPI; provides
  `TestClient` and middleware (e.g. CORS).
- **Frontend (Prompt 8):** a React 18 + Vite 5 + TypeScript foundation now
  lives under `frontend/`, with Leaflet wired through react-leaflet v4 and
  a typed API service layer against the backend routes.

### Planned / future technologies (NOT implemented)

## 3. Architecture

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application factory + lifespan + /health
│   ├── config.py            # Environment-based settings (no secrets in source)
│   ├── database.py          # SQLAlchemy engine, SessionLocal, Base, get_db
│   ├── security.py          # JWT create / decode / expiry helpers
│   ├── models/
│   │   ├── __init__.py
│   │   └── tourist.py       # SQLAlchemy ORM model(s)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── tourist.py       # Pydantic request/response schemas
│   │   └── digital_id.py
│   └── api/
│       ├── __init__.py      # api_router (prefix /api)
│       ├── tourist.py       # POST /register
│       └── digital_id.py    # POST /digital-id/{id}, POST /verify-id
├── tests/
│   ├── conftest.py          # Test DB isolation, table creation, cleanup
│   ├── test_health.py
│   ├── test_registration.py
│   └── test_digital_id.py
├── requirements.txt
└── .env.example
```

### FastAPI application (`app/main.py`)

- A single `FastAPI` instance is created with the project title, description,
  version, and debug flag sourced from `app.config`.
- A **lifespan** context manager calls `Base.metadata.create_all(bind=engine)`
  on startup so that SQLite tables are created automatically — no migrations.
- `GET /health` returns `{"status": "ok"}` and does **not** touch the database.
- A single `api_router` is mounted under the `/api` prefix.

### API routing (`app/api/`)

- All application endpoints live under `/api/` via `api_router`.
- `tourist.py` registers `POST /api/register`.
- `digital_id.py` registers `POST /api/digital-id/{tourist_id}` and
  `POST /api/verify-id`.

### Configuration (`app/config.py`)

- Settings are read from environment variables via `os.getenv`, with a
  `.env` file loaded from the `backend/` directory by `python-dotenv`.
- No secrets are hard-coded; only non-sensitive defaults are provided.
- Configuration keys include project metadata, `DATABASE_URL`, and JWT
  settings (`JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRATION_HOURS`).

### Database layer (`app/database.py`)

- SQLAlchemy 2.x engine created from `DATABASE_URL` (default SQLite local file).
- `SessionLocal` session factory (`autocommit=False`, `autoflush=False`).
- `Base` declarative base shared by all models.
- `get_db()` dependency yields a session and closes it after the request.

### SQLAlchemy models (`app/models/`)

- `Tourist` — the single implemented ORM model (see Section 6).

### Pydantic schemas (`app/schemas/`)

- `TouristCreate`, `TouristResponse` — registration request/response.
- `DigitalIdRequest`, `DigitalIdResponse`, `VerifiedTourist`,
  `VerifyResponse` — digital-ID request/response.

### Security / JWT layer (`app/security.py`)

- `create_token()` — signs a JWT with HS256 using `JWT_SECRET_KEY`.
- `decode_token()` — verifies signature + expiration + required claims.
- `token_expiry()` — reads `exp` without verification (used on the
  generation path) and returns a timezone-aware UTC `datetime`.

### Testing structure (`tests/`)

- `conftest.py` sets `DATABASE_URL` to an isolated temp SQLite file **before**
  application modules are imported, creates tables, and wipes the `tourists`
  table before each test.
- Each test module uses FastAPI's `TestClient` (backed by `httpx`).
- The existing health and registration tests are **not modified**.

## 4. Development Milestones

### 4.1 Prompt 1 — Backend Foundation

**Objective:** Create a minimal, runnable FastAPI backend with a health-check
endpoint and SQLAlchemy/SQLite foundation, plus project structure and tests.

**Implementation:**

- Created the `backend/app/` package with `main.py`, `config.py`,
  `database.py`, and an empty `api/` package.
- `config.py` loads settings from environment variables (with a `.env` file
  optional load) and exposes `PROJECT_NAME`, `ENVIRONMENT`, `DEBUG`,
  `DATABASE_URL`, and other non-sensitive defaults.
- `database.py` defines the SQLAlchemy engine (SQLite,
  `check_same_thread=False`), `SessionLocal`, and `Base`, plus a `get_db`
  dependency. No connection is opened at import time.
- `main.py` builds the FastAPI app, registers a `lifespan` that calls
  `Base.metadata.create_all(bind=engine)`, and exposes `GET /health` →
  `{"status": "ok"}`.
- CORS middleware is added **only in development** (`ENVIRONMENT ==
  "development"`) and allows only `http://localhost:5173` (the Vite dev
  server).
- `GET /health` is a simple liveness check that does not use the database or
  authentication.

**Project structure created:**

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   └── api/
│       └── __init__.py
├── tests/
│   └── test_health.py
├── requirements.txt
└── .env.example
```

**FastAPI setup:** Application titled `"SIH Tourist Safety"`, with debug mode
sourced from config. Tables created at startup via lifespan (no Alembic).

**Configuration:** All settings come from environment variables; `.env` is
gitignored and `.env.example` documents the expected keys.

**SQLite/SQLAlchemy foundation:** SQLite local file database
(`sqlite:///./tourist_safety.db`). `Base` and `get_db` dependency are in place
for future models.

**CORS configuration:** `CORSMiddleware` added only when
`ENVIRONMENT == "development"`, allowing only `http://localhost:5173` (Vite).

**`/health`:** Returns HTTP 200 with `{"status": "ok"}`. No auth or DB
involvement.

**Testing:** Two tests in `test_health.py`:
`test_health_returns_200` checks status 200; `test_health_body_is_ok` checks
the body is `{"status": "ok"}`.

**Result:** The application starts successfully and `/health` returns the
expected response. Both health tests pass.

**Important decisions:**
- `.venv/` is used as the virtual environment (gitignored).
- No migrations (Alembic) — tables created at startup from model metadata.
- CORS restricted to the Vite dev origin rather than `["*"]`.
- `/health` is intentionally lightweight (no DB / no auth).

**Files created/modified:**
- Created: `backend/app/__init__.py`, `backend/app/main.py`,
  `backend/app/config.py`, `backend/app/database.py`,
  `backend/app/api/__init__.py`, `backend/tests/test_health.py`,
    `backend/requirements.txt`, `backend/.env.example`, `.gitignore`.

### 4.2 Prompt 2 — Tourist Registration

**Objective:** Implement the tourist database model, database initialization,
registration API with validation, duplicate-phone handling, and tests.

**Tourist model (`app/models/tourist.py`):**

| Column | Type | Constraints |
|---|---|---|
| `id` | `int` | `primary_key=True`, `index=True` |
| `name` | `str` (String(255)) | `nullable=False` |
| `phone` | `str` (String(20)) | `nullable=False`, `unique=True`, `index=True` |
| `created_at` | `datetime` | `nullable=False`, `server_default=func.now()` |

- The model uses SQLAlchemy 2.x `Mapped` / `mapped_column` typing.
- `phone` is stored as a **string**, never an integer, to preserve leading
  zeros and formatting.
- `phone` has a **database-level unique constraint** to prevent duplicate
  registrations.

**Database initialization:**
- `Tourist` is registered on the shared `Base`.
- `main.py` imports `Tourist` so its table exists when `Base.metadata.create_all`
  runs during lifespan and again during test collection in `conftest.py`.
- Tables are created at startup (no migrations).

**Registration endpoint (`POST /api/register`, in `app/api/tourist.py`):**
- Accepts `TouristCreate` (name, phone), validated by Pydantic.
- Checks for an existing tourist with the same phone (explicit `SELECT`).
- If found → HTTP 409 Conflict.
- On `IntegrityError` (defensive guard against race conditions) → HTTP 409.
- On success → commits, refreshes, returns `TouristResponse` with HTTP 201.

**Validation (Pydantic `TouristCreate` in `app/schemas/tourist.py`):**
- `name`: required, `min_length=1`, `max_length=255`; `field_validator`
  rejects empty/whitespace and strips surrounding whitespace.
- `phone`: required, `min_length=1`, `max_length=20`; validated against
  `^[6-9]\d{9}$` (Indian 10-digit mobile, leading digit 6–9).
- **Phone normalization:** separators (`-`, spaces, `()`) are stripped, and
  an optional `+91` or `91` country-code prefix is removed before validation.
  The normalized 10-digit string is stored.

**Duplicate phone handling:**
- Checked via an explicit database `SELECT` before insert.
- Reinforced by the `UNIQUE` constraint on `phone` (catches race conditions).
- Returns HTTP 409 with `{"detail": "A tourist with this phone number is already registered."}`.

**HTTP status codes:**
- 201 — tourist created.
- 409 — phone already registered.
- 422 — invalid name or phone (Pydantic validation failure).

**Test coverage (`tests/test_registration.py`, 7 tests):**
1. Successful registration → 201.
2. Response contains tourist `id`.
3. Name trimmed and phone normalized.
4. Invalid phone → 422.
5. Missing name → 422.
6. Duplicate phone → 409.
7. Tourist is persisted in SQLite.

**Result:** All registration tests pass; the endpoint works as verified
manually (HTTP 201 on success, HTTP 409 on duplicate, HTTP 422 on invalid
input, row persisted in SQLite).

**Files created/modified:**
- Created: `backend/app/models/__init__.py`, `backend/app/models/tourist.py`,
  `backend/app/schemas/__init__.py`, `backend/app/schemas/tourist.py`,
  `backend/app/api/tourist.py`, `backend/tests/test_registration.py`,
  `backend/tests/conftest.py`.
- Modified: `backend/app/main.py` (import model, lifespan),   `backend/app/api/__init__.py` (include tourist router).

### 4.3 Prompt 3 — Signed Digital ID + QR Verification

**Objective:** After registration, issue a signed JWT digital ID for a tourist
with an embedded QR code, and provide a verification endpoint that validates
the token's signature, expiration, and the tourist's existence in the database.

**JWT implementation (`app/security.py`):**
- Uses **PyJWT** with the **HS256** signing algorithm.
- `create_token(tourist_id, name)`: builds a payload with `sub` (stringified
  tourist ID), `name`, `iat` (issued-at, UTC), and `exp` (now + 24 h, UTC),
  then signs it with `JWT_SECRET_KEY`.
- `decode_token(token)`: verifies signature + expiration and requires the
  `exp`, `iat`, and `sub` claims. Raises `jwt.InvalidTokenError` (or a
  subclass) on any failure.
- `token_expiry(token)`: reads `exp` without verification (used on the
  generation path) and returns a timezone-aware UTC `datetime`.

**Signing algorithm:** `HS256` (symmetric HMAC-SHA256).

**JWT claims:**

| Claim | Type | Value |
|---|---|---|
| `sub` | `str` | Tourist ID |
| `name` | `str` | Tourist name |
| `iat` | `int` (JWT timestamp) | Issued-at (UTC) |
| `exp` | `int` (JWT timestamp) | Now + 24 h (UTC) |

**Expiration:** 24 hours (`JWT_EXPIRATION_HOURS`, configurable via env).

**Secret configuration:**
- `JWT_SECRET_KEY` is read from the environment (loaded via `.env` in
  development). It is **never hard-coded** in source.
- A non-sensitive default exists only for local convenience; production must
  supply `JWT_SECRET_KEY` via the environment.
- `JWT_ALGORITHM` (default `HS256`) and `JWT_EXPIRATION_HOURS` (default `24`)
  are likewise environment-driven.
- `backend/.env.example` documents the keys; `backend/.env` is gitignored.

**Security decisions:**
- The JWT contains **only** `sub`, `name`, `iat`, `exp`. The tourist's
  **phone number is never included** in the token (confirmed by test
  `test_jwt_contains_tourist_id_and_name_but_not_phone` and by the
  `create_token` signature, which only accepts `tourist_id` and `name`).
- On `/verify-id` the tourist ID is taken **only** from the signed `sub`
  claim — the request body supplies just the opaque token string.
- Signature verification is enforced in `decode_token` via
  `algorithms=[JWT_ALGORITHM]`.
- Tampered, malformed, and expired tokens all return `valid: false` with no
  stack trace leakage; the `InvalidTokenError` is caught and converted to a
  clean response.
- The secret is never logged (no `print` of the token or secret anywhere in
  the codebase).

**QR generation (`_make_qr_data_url` in `app/api/digital_id.py`):**
- Uses the `qrcode` library (with Pillow backend) to render a PNG.
- `ERROR_CORRECT_M`, `box_size=10`, `border=4`, `fit=True`.
- The token is written to an in-memory `io.BytesIO` buffer (no image files
  are written to disk or the repository).
- Returned as a **data URL**: `data:image/png;base64,<base64-png>`.

**QR transport format:** Base64-encoded PNG embedded in a `data:` URL, so a
future React frontend can render it directly with `<img src={qr_code} />`.

**Digital-ID endpoint (`POST /api/digital-id/{tourist_id}`):**
- Path parameter `tourist_id` looked up via `db.get(Tourist, ...)`.
- 404 if the tourist does not exist.
- On success: signs a JWT, computes `expires_at`, generates the QR data URL,
  and returns `DigitalIdResponse` (`tourist_id`, `token`, `expires_at`,
  `qr_code`) with HTTP 200.

**Verification endpoint (`POST /api/verify-id`):**
- Accepts `DigitalIdRequest` (`{"token": "<jwt>"}`).
- Calls `decode_token` inside a `try/except InvalidTokenError`.
- On any token error → `{"valid": false, "tourist": null}` (HTTP 200).
- Extracts the tourist ID from `claims["sub"]` (parsed as `int`), looks up
  the tourist in SQLite.
- If the tourist no longer exists → `{"valid": false, "tourist": null}`.
- On success → `{"valid": true, "tourist": {"id": ..., "name": ...}}` (HTTP 200).
- The response never includes the phone number.

**Invalid-token handling:**

| Case | Result |
|---|---|
| Invalid signature (tampered) | `{"valid": false, "tourist": null}` |
| Expired token | `{"valid": false, "tourist": null}` |
| Malformed token | `{"valid": false, "tourist": null}` |
| Valid JWT but tourist deleted | `{"valid": false, "tourist": null}` |

All four return HTTP 200 with `valid: false` (the token is rejected, not the
request); no internal errors or stack traces are exposed.

**Files created/modified:**
- Created: `backend/app/security.py`, `backend/app/schemas/digital_id.py`,
  `backend/app/api/digital_id.py`, `backend/tests/test_digital_id.py`.
- Modified: `backend/app/config.py` (JWT settings),
  `backend/app/api/__init__.py` (include digital-id router),
  `backend/requirements.txt` (PyJWT, qrcode[pil]),
  `backend/.env.example` (JWT keys),
  `backend/tests/conftest.py` (set `JWT_SECRET_KEY` for tests).

### 4.4 Prompt 4 — Incidents + SOS + Synthetic Dataset

**Objective:** Add historical incident storage, emergency SOS events, their
APIs, and a deterministic synthetic dataset for later ML evaluation.

**New tables:** `incidents` (`id`, `latitude`, `longitude`,
`incident_type`, `severity` 1-5, `occurred_at`) and `sos_events` (`id`,
`tourist_id`, `latitude`, `longitude`, `status` default `"active"`,
`created_at`). Both use SQLAlchemy 2.x typed mappings; `phone`-style string
discipline kept (coordinates as floats, types as plain strings, no enums).
No migrations — tables registered on `Base.metadata` and created at startup.

**Endpoints added:** `GET /api/incidents` (full dataset, prototype-scale),
`POST /api/sos` (validates tourist exists -> 201 / unknown -> 404 /
bad coordinates -> 422), `GET /api/sos` (`{"sos_events": [...]}` envelope for
the future authority dashboard). Status is server-assigned; clients cannot
set it (`extra="forbid"` on `SOSCreate`).

**Validation:** Pydantic bounds latitude -90..90, longitude -180..180,
severity 1..5, positive integer `tourist_id`; incident types restricted to
the six prototype strings via `field_validator`.

**Synthetic dataset:** `scripts/generate_incidents.py` — fixed seed **42**;
150 incidents = 5 dense clusters (25 pts each, +/-0.008 deg jitter) + 25
noise points inside the Vijayawada demo bounding box (16.40-16.70 N,
80.40-80.70 E); timestamps spread over 60 days; regeneration clears only the
`incidents` table (tourists/SOS untouched).

> The incident dataset is synthetic and created solely for prototype
> demonstration and ML/risk-clustering evaluation. It does not represent real
> crime statistics.

**Tests:** 16 incident/SOS schema + API tests added (suite: 55 passing).

**Result:** All endpoints verified live (201/404/422 paths); generator run
twice produced identical datasets without duplicate accumulation.

**Files created/modified:** `app/models/incident.py` (+`sos_event.py`
re-export), `app/schemas/incident.py`, `app/api/incident.py`,
`app/api/sos.py`, `scripts/generate_incidents.py`, router registration in
`app/api/__init__.py`, `tests/test_incidents.py`, `tests/test_sos.py`.

### 4.5 Prompt 5 — Risk Engine (DBSCAN Clustering)

**Objective:** Cluster incident+SOS points into geographic risk zones and
score each zone for the future heatmap/dashboard.

**Implementation:** New pure module `app/risk_engine.py` — loads points from
`incidents` + `sos_events` (SOS treated as effective severity 5, pseudo-type
`sos`), converts lat/lon to radians, runs
`sklearn.cluster.DBSCAN(metric="haversine", eps=eps_km/6371.0088,
min_samples=k)` so neighbourhoods are true ground distances.

**Scoring (0-100, explainable):**
`score = round(100*(0.45*min(n/25,1) + 0.40*min(avg_weighted_sev/5,1) +
0.15*distinct_types/7))`, where weighted severity applies per-type
multipliers (theft 1.0, harassment 1.2, medical 1.3, accident 1.2,
missing_person 1.5, unsafe_area 0.8, sos 1.4). Bands: >=75 CRITICAL,
>=50 HIGH, >=25 MODERATE, else LOW. Zone center = member mean; radius =
max haversine(center, member); output sorted score desc with stable
tie-breaks (fully deterministic, verified under input shuffling).

**Noise handling:** label -1 points are excluded from zones but reported as
`noise_incidents` / `noise_sos` counts — nothing disappears silently.

**Configuration:** `RISK_EPS_KM` (default 0.5) and `RISK_MIN_SAMPLES`
(default 4) env keys, overridable per-request via validated query params
(`eps_km` 0 < x <= 10, `min_samples` 1..50; violations -> 422).

**Endpoint:** `GET /api/risk-zones` returning the `RiskZonesResponse`
envelope (see `docs/API_REFERENCE.md`). Read-only; safe to poll; empty or
sub-threshold data yields HTTP 200 with `zones: []`.

**Dependency:** `scikit-learn>=1.4` added (pulls numpy/scipy/joblib).

**Tests:** 16 new tests (engine clustering/noise/scoring/bands/radius/
determinism, schema rejection cases, API sorting/empty-DB/422/SOS-counting).
Suite: **71 passed**, zero regressions.

**Manual verification:** seeded 150 incidents + 3 SOS near cluster centers;
live run returned 6 zones scored 96/92/88/80/64/50 (CRITICAL/HIGH), SOS
absorbed into the two nearest zones, totals and noise counts correct.

**Limitations:** zones recomputed per request (no caching layer); zone
center is the arithmetic mean (not medianoid); SOS severity is fixed; no
temporal decay yet; endpoint unauthenticated like the rest of the prototype.

**Files created/modified:** created `app/risk_engine.py`,
`app/schemas/risk.py`, `app/api/risk.py`, `tests/test_risk_engine.py`;
modified `requirements.txt`, `app/config.py`, `.env.example`,
`app/api/__init__.py`, plus this documentation.

### 4.6 Prompt 6 — Patrol Optimization (Greedy p-Median)

**Objective:** Recommend where to position a configurable number of patrol
units over the Prompt 5 risk zones so that weighted risk coverage is
maximised, with fully explainable placement.

**Reuse:** consumes `compute_risk_zones()` output verbatim — no clustering
logic duplicated. Candidate sites are the zone centers themselves; zone
weight `w_z = risk_score` (0-100).

**Algorithm:** classic greedy p-median heuristic. A patrol at candidate `c`
covers every unassigned zone whose center lies within `service_radius_km`
(haversine ground distance); each iteration places the candidate with the
largest total uncovered weight inside that radius:
`gain(c) = Σ w_z for unassigned z with dist(c, z.center) <= R`.
Ties break by the engine's deterministic (-score, lat, lon) ordering. A
candidate always covers its own zone (distance 0), so no placement is wasted.

**Metrics returned per unit:** served `zone_id`s, `covered_weight`,
`coverage_share_pct = 100·covered_w/total_weight`, mean haversine distance to
served centers, highest served risk level. Envelope adds
`requested/placed_units`, `total_weight`, `covered_weight`, `coverage_pct`,
and an explicit `uncovered_zones` list (gaps are reported, never hidden).

**Configuration:** `PATROL_NUM_UNITS` (default 3) and
`PATROL_SERVICE_RADIUS_KM` (default 2.0), both overridable per-request.
Query validation: `units` 1..20, `service_radius_km` > 0 and <= 25;
upstream `eps_km`/`min_samples` pass through to the risk engine.

**Endpoint:** `GET /api/patrol-plan` (see `docs/API_REFERENCE.md`).
Empty or sub-threshold data yields HTTP 200 with `patrols: []`.

**No new dependencies** — reuses the public `haversine_km()` helper
(previously private `_haversine_km`) from the risk engine.

**Tests:** 15 new (greedy priority, radius-limited chains, units>zones,
empty input, share math, shuffle-determinism, schema rejections,
API sorting/validation/critical-first placement). Suite: **86 passed**.

**Manual verification:** seeded dataset (150 incidents -> 6 zones, total
weight 458). `units=3`: placed at zones {5,6}, {1}, {2} -> coverage 65.07%;
the optimizer correctly preferred two co-located MODERATE/HIGH zones
(combined gain 114) over any single CRITICAL zone. `units=5, R=1.0`:
100.0% coverage in five patrols (one unit serves the adjacent pair).
Deterministic across repeated calls.

**Limitations:** straight-line (haversine) proximity, not road-network
routing; static demand weights (no time-of-day or live SOS weighting yet);
zone center is the deployment hint rather than an optimised medianoid;
endpoint unauthenticated like the rest of the prototype.

**Files created/modified:** created `app/patrol_optimizer.py`,
`app/schemas/patrol.py`, `app/api/patrol.py`,
`tests/test_patrol_optimizer.py`; modified `app/risk_engine.py`
(public distance helper), `app/config.py`, `.env.example`,
`app/api/__init__.py`, plus this documentation.

### 4.7 Prompt 7 — Backend Integration

**Objective:** Expose dashboard-facing views of the existing engines without
duplicating any logic, audit router wiring, review CORS for the future Vite
frontend, and lock the integration in with tests.

**New endpoints (pure adapters):**
- `GET /api/risk-heatmap` — reshapes `compute_risk_zones()` output into
  Leaflet-ready markers (`center: [lat, lon]`, `radius_meters`,
  `risk_score/level`, counts, dominant type). Ordering inherited from the
  engine (score desc) — fully deterministic.
- `GET /api/patrol-recommendations` — runs `optimize_patrols()` verbatim,
  then enriches every placement with `served_zones[]` detail (per-zone
  score/level/haversine distance, sorted nearest-first) plus a Leaflet
  `position` pair. Accepts the same parameters as `/api/patrol-plan`.

**Router audit:** each of the now-eight routers is registered exactly once;
enforced by a regression test that walks the route tree (handling FastAPI
0.141's lazy `_IncludedRouter.original_router` nesting) and asserts no
duplicate paths.

**CORS review:** middleware already restricted to `http://localhost:5173`
under `ENVIRONMENT == "development"` — correct as-is; verified live (below).
No code change.

**Tests:** 13 integration tests — cross-endpoint consistency
(heatmap ⇔ risk-zones), marker ordering/centers, empty data, 422 validation,
recommendation placement/distance recomputation, legacy key-set snapshots for
`/risk-zones` + `/patrol-plan`, incidents→heatmap total agreement, and the
router-uniqueness walk. Suite: **99 passed**, zero regressions.

**Manual verification:** seeded dataset (150 incidents -> 6 zones / weight
458): heatmap returned 6 markers (96/88/80 CRITICAL top-three);
`units=3` placed patrols serving zones [5,6], [1], [2] -> coverage 65.07%
with distances (5: 0.0 km, 6: 0.803 km); zones 3-4 reported uncovered.
CORS probes from a live server: allowed origin echoed
(`access-control-allow-origin: http://localhost:5173`), foreign origin
absent, preflight `OPTIONS` -> 200 with method list.

**Limitations:** polling only (no WebSockets by design); heatmap/recommendation
payloads recompute per request; CORS covers local development origin only.

**Files created/modified:** created `app/schemas/dashboard.py`,
`app/api/heatmap.py`, `app/api/recommendations.py`,
`tests/test_integration_prompt7.py`; modified `app/api/__init__.py`,
plus this documentation.

### 4.10 Prompt 10 — Authority Dashboard

**Objective:** Replace the `/authority` placeholder with a judge-facing
command centre that renders all five backend datasets on one screen -
without duplicating any clustering or optimization logic and without
polling.

**Data sources (single snapshot fetch on mount):** `/api/risk-heatmap`,
`/api/incidents`, `/api/sos`, `/api/patrol-plan`,
`/api/patrol-recommendations` via the existing typed API modules. Each
source has an independent loading/error/retry state so one failure never
blanks the dashboard; per-source error chips include Retry buttons.

**Map layers (`components/authority/SafetyMap.tsx` over shared `MapView`):**
1. Risk-zone `Circle`s using backend `radius_meters`, colour-coded
   CRITICAL/HIGH/MODERATE/LOW from the shared `riskStyles` palette.
2. Historical incidents as small slate dots with popups (type, severity,
   timestamp, coordinates).
3. SOS events as larger white-ringed red dots (visually urgent) with
   id/tourist/time/status/coordinates popups.
4. Current patrol posts from `/api/patrol-plan` as blue dashed rings,
   explicitly captioned "Source: GET /api/patrol-plan (no live GPS feed)".
5. AI-recommended units from `/api/patrol-recommendations` as solid green
   markers plus thin green `Polyline` links to each covered zone center,
   making the reasoning visible on-map.

An overlay legend explains risk levels, incident/SOS dots, current posts,
and AI-recommended units.

**Statistics:** six KPI tiles derived purely from responses - total
incidents, recorded SOS (+active count badge), risk zones, CRITICAL+HIGH
count, placed AI patrols, coverage %. Nothing hard-coded.

**Patrol panel:** AI recommendation cards (unit id, position pair, covered
zone ids, count, share % bar, highest-level chip, per-served-zone distance
list) plus a current-posts summary with source caption; uncovered zones are
listed explicitly when present.

**Shared refactor:** level colours extracted to
`components/common/riskStyles.ts`; tourist `RiskMap` now imports them
(single source of truth).

**Verification:** build clean first try (100 modules; CSS 23.4 kB); live
run against seeded data returned 150 incidents, 3 active SOS, 6 zones
(4 CRITICAL / 2 HIGH), plan placed 3/3, recommendations coverage 64.67%
(302/467 weight incl. one SOS-as-noise point), uncovered 2;
`/authority` served the SPA HTML. Backend suite after frontend work:
**99 passed**.

**Limitations:** single snapshot fetch - no polling/refresh yet (Prompt 11);
no live patrol GPS feed (plan positions stand in, clearly labelled);
incidents render as points without severity-sized scaling; desktop-first
layout (grid collapses under 900 px but is not phone-optimised).

**Files created/modified:** created
`src/components/authority/{SafetyMap,StatCards,PatrolPanel}.tsx` and
`src/components/common/riskStyles.ts`; rewrote
`src/pages/AuthorityPage.tsx`; extended `src/index.css`; refactored
tourist `RiskMap.tsx` imports. Backend untouched.

### 4.8 Prompt 8 — Frontend Foundation

**Objective:** Establish a clean, independently runnable React + Vite +
TypeScript foundation under `frontend/` with a typed API service layer,
routing, a reusable Leaflet map component, and environment configuration.
Placeholders only - no feature UI.

**Stack:** React 18.3 + Vite 5.4 + TypeScript 5.6, react-router-dom 6,
leaflet 1.9 + react-leaflet 4.2 (React 18 pinned deliberately for stable
react-leaflet v4 compatibility). No other libraries.

**Structure:** `src/api` (client + six feature modules), `src/types`
(five modules mirroring backend schemas field-for-field), `src/components`
(`layout/AppLayout`, `common/MapView`), `src/pages`
(Home/Tourist/Authority/NotFound), `src/routes/AppRouter`.

**API layer:** central client reads `VITE_API_BASE_URL`
(default `http://localhost:8000`), provides typed `apiGet`/`apiPost`
(optional-body POST for `/api/digital-id/{id}`), parses JSON, and throws
`ApiError {status, detail}` on non-2xx. Feature modules cover all ten
backend routes: risk-zones, risk-heatmap, patrol-plan,
patrol-recommendations, incidents, sos (GET+POST), register,
digital-id generation, verify-id.

**Types:** `RiskZone/RiskZonesResponse`, `HeatmapMarker/RiskHeatmapResponse`,
`PatrolUnit/PatrolPlanResponse`,
`ServedZone/PatrolRecommendation(s)Response`, `Incident`, `SOSEvent`,
`Tourist`, `DigitalIdResponse`, `VerificationResponse` - copied from the
Pydantic models, Leaflet positions as `[latitude, longitude]`.

**Routing:** `/` (overview + map-foundation check circle at the Vijayawada
demo center), `/tourist` and `/authority` placeholders, `*` -> NotFoundPage.
`MapView` supports center/zoom/className/children so later prompts can drop
in markers, circles, and popups.

**Verification:** `npm install` (76 packages), `npm run build` -
`tsc` clean then Vite build (84 modules; JS 323 kB / gzip 100 kB; CSS
16.6 kB includes Leaflet styles); dev server route checks returned the SPA
HTML for `/`, `/tourist`, `/authority`, and an unknown path (client-side
404). Backend regression suite after frontend work: **99 passed**.

**Issues encountered:** `npm create vite` hung on its first-run install
prompt (scaffolded manually instead); Vite binds `localhost` via IPv6 while
a 127.0.0.1 TCP probe failed (switched to HTTP-based readiness checks);
TS required ES2022 lib for `Error(..., {cause})` and `object` typing for
query-param bags (interface types lack implicit index signatures).

**Stop point:** Prompts 9-12 (tourist app, authority dashboard, polling,
feature rendering) were NOT started.

### 4.9 Prompt 9 — Tourist Application

**Objective:** Replace the `/tourist` placeholder with the complete
tourist-side experience: registration, safety dashboard (risk map + current
location), emergency SOS with confirmation, and the signed Digital ID with
QR display - all against the real backend.

**Registration flow:** `RegistrationForm` mirrors `TouristCreate` (name +
Indian mobile). Client-side normalization/validation mirrors the backend
(strips separators/+91, enforces `^[6-9]\d{9}$`) but the backend stays
authoritative; API errors render inline. Submitting shows a busy state and,
on success, transitions to the dashboard **without a page reload**.

**Prototype persistence:** only the returned `Tourist` object is stored in
`localStorage` under `sih_tourist` (validated on restore). A
"Register a different tourist" action clears it. No tokens/sessions stored.

**Dashboard:** hierarchy = safety banner -> SOS -> risk map -> identity ->
Digital ID. The banner switches between *monitored* (green) and
*SOS ACTIVE* (red pulse) based on SOS state.

**Risk map:** `RiskMap` wraps `MapView`; fetches `GET /api/risk-heatmap`
once per dashboard load with loading/error/retry states. Every marker renders
as a Leaflet `Circle` (`center` + `radius_meters`) colour-coded by level
(CRITICAL red / HIGH orange / MODERATE yellow / LOW green) with a popup
showing score, incident/SOS counts, dominant type, avg severity. An HTML
legend explains all four levels plus the current-location ring.

**Location:** one-shot `navigator.geolocation.getCurrentPosition` centers the
map and drives SOS coordinates; denial/unavailability falls back to the
documented Vijayawada coordinate `[16.5062, 80.648]` with an explicit
"demo location" note in both the UI and legend. No continuous watching.

**SOS:** big round SOS button -> confirmation card ("Your current location
will be shared...") -> `POST /api/sos` -> persistent **SOS ACTIVE** panel
with event id/timestamp/coords/status. Send failures surface an error that
explicitly says the SOS was NOT sent, with retry.

**Digital ID:** "View Digital ID" opens a modal card fed by
`POST /api/digital-id/{id}`: tourist name/ID, validity (`expires_at`),
and the **backend-provided QR rendered directly from its data URL**
(`<img src={qr_code}>` - no client-side QR generation). Includes a
"digitally signed by the SIH backend (HS256)" indication.

**Verification/build:** `npm run build` clean after fixes (94 modules;
JS 334 kB); dev-server route checks pass; live end-to-end flow replayed the
UI's exact calls - register 201, heatmap 200 (6 markers), digital-id 200
(QR ok), verify-id `valid:true`, SOS 201 active; backend suite
**99 passed**.

**Issues encountered:** a temporary validation script sent GET instead of
POST to the body-less digital-ID endpoint and reported a misleading 405
(`Allow= POST` exposed it) - the frontend's `apiPost` was always correct.
Also fixed during development: a TS narrowing error in SosPanel phase
handling and an accidental reference to a non-existent
`tourist_name` response field.

**Limitations:** location streaming, SOS polling/resolution, authority
dashboard (Prompt 10), integration/polling hardening (Prompt 11) are
intentionally out of scope; SOS state is session-only (not persisted);
single active SOS assumption.

**Files created/modified:** created
`src/components/tourist/{RegistrationForm,RiskMap,SosPanel,DigitalIdCard,TouristDashboard}.tsx`;
rewrote `src/pages/TouristPage.tsx`; extended `src/index.css`.
Backend untouched.

## 5. Current API Surface

### GET /health

- **Purpose:** Liveness check (no auth, no DB).
- **Response:** `200 {"status": "ok"}`

---

### POST /api/register

- **Purpose:** Register a new tourist.
- **Request body:**
  ```json
  {"name": "Rahul Kumar", "phone": "9876543210"}
  ```
- **Success (201):**
  ```json
  {"id": 1, "name": "Rahul Kumar", "phone": "9876543210", "created_at": "2026-08-25T15:09:29"}
  ```
- **Validation rules:**
  - `name`: required, non-empty after stripping, ≤ 255 chars.
  - `phone`: required, accepts Indian 10-digit mobile numbers (leading 6–9);
    optional `+91`/`91` prefix and separators (`-`, space, `()`) are stripped
    and normalized to 10 digits.
- **Errors:**
  - `422` — invalid name or phone (Pydantic validation).
  - `409` — phone already registered.

---

### POST /api/digital-id/{tourist_id}

- **Purpose:** Issue a signed JWT digital ID + QR code for an existing tourist.
- **Path parameters:** `tourist_id` (int).
- **Success (200):**
  ```json
  {
    "tourist_id": 1,
    "token": "<signed-jwt>",
    "expires_at": "2026-08-26T15:09:29Z",
    "qr_code": "data:image/png;base64,<base64>"
  }
  ```
- **Errors:**
  - `404` — tourist not found.

---

### POST /api/verify-id

- **Purpose:** Verify a signed tourist digital ID.
- **Request body:**
  ```json
  {"token": "<signed-jwt>"}
  ```
- **Success — valid token (200):**
  ```json
  {"valid": true, "tourist": {"id": 1, "name": "Rahul Kumar"}}
  ```
- **Success — invalid token (200):**
  ```json
  {"valid": false, "tourist": null}
  ```
- **Errors:** None at the HTTP layer for invalid tokens (returned as
  `valid: false` with HTTP 200). Malformed JSON bodies produce a standard
  FastAPI `422`.

**Added in Prompts 4-7:** `GET /api/incidents`, `POST /api/sos`,
`GET /api/sos`, `GET /api/risk-zones`, `GET /api/patrol-plan`,
`GET /api/risk-heatmap`, and `GET /api/patrol-recommendations`. Full
request/response specs live in `docs/API_REFERENCE.md`; milestone context is
in sections 4.4-4.7.

## 6. Current Database Schema

### Table: `tourists`

| Column | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique tourist identifier |
| `name` | VARCHAR(255) | NOT NULL | Tourist display name |
| `phone` | VARCHAR(20) | NOT NULL, UNIQUE, INDEXED | Indian mobile number (string) |
| `created_at` | DATETIME | NOT NULL, `server_default=NOW()` | Registration timestamp |

Tables `incidents` and `sos_events` were added in Prompt 4 (section 4.4):

### Table: `incidents`

| Column | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY | Unique incident identifier |
| `latitude` | FLOAT | NOT NULL | Incident latitude |
| `longitude` | FLOAT | NOT NULL | Incident longitude |
| `incident_type` | VARCHAR(50) | NOT NULL | theft/harassment/medical/accident/missing_person/unsafe_area |
| `severity` | INTEGER | NOT NULL | 1 (low) - 5 (high) |
| `occurred_at` | DATETIME | NOT NULL | When the incident occurred |

### Table: `sos_events`

| Column | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY | Unique SOS identifier |
| `tourist_id` | INTEGER | NOT NULL, INDEXED | Reporting tourist |
| `latitude` | FLOAT | NOT NULL | SOS latitude |
| `longitude` | FLOAT | NOT NULL | SOS longitude |
| `status` | VARCHAR(20) | NOT NULL, default `"active"` | `active` or `resolved` |
| `created_at` | DATETIME | NOT NULL | When the SOS was raised |

Both tables are consumed read-only by the Prompt 5 risk engine.

## 7. Testing & Verification

### Testing framework

- **pytest** 9.1.1 with FastAPI's `TestClient` (backed by `httpx` 0.28.1).

### Test organization

- `conftest.py` sets `DATABASE_URL` to an isolated temp SQLite file **before**
  application modules are imported, creates tables, and wipes the `tourists`
  table before each test.
- `test_health.py` — 2 tests for `GET /health`.
- `test_registration.py` — 7 tests for `POST /api/register`.
- `test_digital_id.py` — 14 tests for digital-ID generation + verification.
- `test_incidents.py` / `test_sos.py` — schema + API coverage for incidents
  and SOS (Prompt 4).
- `test_risk_engine.py` — engine, schema, and endpoint coverage for the
  DBSCAN risk engine (Prompt 5), including a determinism test.
- `test_patrol_optimizer.py` — greedy placement, coverage math, schema, and
  endpoint coverage for the patrol optimizer (Prompt 6), including a
  determinism test.
- `test_integration_prompt7.py` — cross-endpoint integration for the
  heatmap/recommendation views, backward-compatibility key-set snapshots,
  chain-total agreement, and router-registration uniqueness (Prompt 7).

### Current test count

**99 tests, all passing** (23 after Prompts 1-3; expanded by Prompt 4's
incident/SOS suites, Prompt 5's risk-engine suite, Prompt 6's
patrol-optimizer suite, and Prompt 7's integration suite; verified via
`python -m pytest tests/ -v`).

### Major behaviors tested

- Health endpoint liveness and body.
- Registration success, id presence, name trimming, phone normalization.
- Registration input validation (422) and duplicate-phone rejection (409).
- Persistence of registered tourists in SQLite.
- Digital-ID generation for existing (200) and nonexistent (404) tourists.
- JWT structure (header.payload.signature), decodability with the configured
  secret, and presence of `sub`, `name`, `iat`, `exp` claims.
- JWT **excludes** the phone number.
- QR code returned as a valid PNG data URL.
- Verification of valid, tampered, malformed, expired, and
  tourist-not-found tokens.
- Phone number is never returned by `/verify-id`.

### Known warnings

- `StarletteDeprecationWarning: Using httpx with starlette.testclient is
  deprecated; install `httpx2` instead.` — an upstream Starlette/TestClient
  notice triggered by `fastapi.testclient.TestClient`; not caused by project
  code and does not affect functionality.

### Manual verification performed

- Started the server with `uvicorn app.main:app --host 127.0.0.1 --port 8000`.
- Confirmed `GET /health` → 200 `{"status":"ok"}`.
- Registered a tourist via `POST /api/register`.
- Generated a digital ID via `POST /api/digital-id/1` → confirmed HTTP 200
  with a JWT and a `data:image/png;base64,...` QR data URL.
- Verified the token via `POST /api/verify-id` → confirmed `{valid:true}`.
- Tampered with one character of the token → `/verify-id` returned
  `{valid:false}`.

## 8. Security Decisions

1. **JWT signing:** Tokens are signed with HS256 using `JWT_SECRET_KEY`.
2. **Secret from environment:** `JWT_SECRET_KEY` is loaded from the
   environment (`.env` in development); never hard-coded in source.
3. **Expiration:** Tokens include an `exp` claim (24 h by default,
   configurable via `JWT_EXPIRATION_HOURS`).
4. **Phone exclusion:** The JWT payload contains only `sub`, `name`, `iat`,
   `exp` — the phone number is never encoded in the token.
5. **Signature verification:** `/verify-id` calls `jwt.decode` with
   `algorithms=[JWT_ALGORITHM]`, which enforces signature + expiration
   checks.
6. **Malformed/tampered/expired token handling:** All such cases are caught
   (`jwt.InvalidTokenError`) and returned as `valid: false` — no stack traces
   are exposed.
7. **No trusted client IDs:** The tourist ID for verification is taken
   only from the signed `sub` claim, not from any client-supplied ID.
8. **No secrets logged:** The token and secret are never printed or logged
   by the application.

> ⚠️ **Prototype-level security, not production-grade.** HS256 is symmetric
> (shared secret); a production system should use an asymmetric algorithm
> (e.g. RS256) and secure key management, token revocation, rate limiting,
> HTTPS enforcement, and stricter input policies.

## 9. Known Limitations

- The JWT secret is loaded from the environment, but a **non-sensitive default**
  exists in `config.py` for local development convenience. Any environment
  without `JWT_SECRET_KEY` set will silently use this default — acceptable for
  a prototype, but a production deployment must always set the real secret.
- No token revocation / blacklist mechanism.
- No rate limiting on `/verify-id` or `/api/register`.
- No HTTPS enforcement (the development server uses plain HTTP).
- Phone validation is specific to Indian 10-digit mobile numbers (leading
  6–9); international or landline numbers are not accepted.
- The QR code is rendered in-memory per request; very high request rates could
  strain memory, but this is not a concern for a one-day prototype.
- A stale phantom TCP socket on port 8000 was observed during testing
  (Windows kernel-level artifact from an earlier `--reload` server process
  that could not be killed); the application binds to any free port.

## 10. Future Development

The following features are **NOT IMPLEMENTED YET** and belong to upcoming
milestones:

- **JWT refresh / token rotation and revocation** (blacklists).
- **Live-location streaming during an active SOS.**
- **Road-network routing between patrol points.**
- **Geo-fencing alerts.**
- **React + Vite + Leaflet** frontend.
- **WebSockets** for real-time updates.
- **PostgreSQL / PostGIS** migration (SQLite is used only for the prototype).
- **Docker** containerization.
- **Redis / Celery** for background jobs / caching.
- **Alembic** migrations.
- **Microservices** separation.