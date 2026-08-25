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
- **Leaflet / React / Vite**: mentioned in the project's overall plan but not
  yet integrated.

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

## 6. Current Database Schema

### Table: `tourists`

| Column | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique tourist identifier |
| `name` | VARCHAR(255) | NOT NULL | Tourist display name |
| `phone` | VARCHAR(20) | NOT NULL, UNIQUE, INDEXED | Indian mobile number (string) |
| `created_at` | DATETIME | NOT NULL, `server_default=NOW()` | Registration timestamp |

Only the `tourists` table exists at this stage. No other tables have been
created.

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

### Current test count

**23 tests, all passing** (verified via `python -m pytest tests/ -v`).

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
- **QR-based SOS / live-location reporting.**
- **Risk clustering** (DBSCAN) and **patrol optimization** (routing).
- **Risk heatmaps** and geo-fencing.
- **React + Vite + Leaflet** frontend.
- **WebSockets** for real-time updates.
- **PostgreSQL / PostGIS** migration (SQLite is used only for the prototype).
- **Docker** containerization.
- **Redis / Celery** for background jobs / caching.
- **Alembic** migrations.
- **Microservices** separation.