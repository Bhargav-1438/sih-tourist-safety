# SIH Tourist Safety — API Reference

This document describes the API endpoints currently implemented in the
prototype. All endpoints are mounted under the `/api` prefix unless noted; the
application also exposes `GET /health` at the root.

---

## GET /health

- **Purpose:** Liveness probe. Does not require authentication or a database
  connection.
- **Request:** None.

**Success response (`200 OK`):**

```json
{"status": "ok"}
```

---

## POST /api/register

- **Purpose:** Register a new tourist with a name and an Indian mobile phone
  number.
- **Request body** (`application/json`):

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Full name; 1–255 chars, non-empty after stripping |
| `phone` | string | yes | Indian 10-digit mobile (leading 6–9); optional `+91`/`91` prefix and separators (`-`, space, `()`) are accepted and stripped |

**Request example:**

```json
{"name": "Rahul Kumar", "phone": "9876543210"}
```

### Validation rules

- `name` must not be empty or whitespace-only; surrounding whitespace is
  stripped before storage.
- `phone` must resolve (after stripping separators and an optional country
  code) to exactly **10 digits** matching `^[6-9]\d{9}$`.
  - Valid: `"9876543210"`, `"+91-9876543210"`, `"91 9876543210"`.
  - Invalid: `"123"`, `"1234567890"` (starts with 1), `"98765"` (too short).

### Success response (`201 Created`):

```json
{
  "id": 1,
  "name": "Rahul Kumar",
  "phone": "9876543210",
  "created_at": "2026-08-25T15:09:29"
}
```

### Error responses

| Status | Condition | Body |
|---|---|---|
| `422 Unprocessable Content` | `name` missing/empty, or `phone` invalid format | `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}` |
| `409 Conflict` | `phone` already registered | `{"detail": "A tourist with this phone number is already registered."}` |

---

## POST /api/digital-id/{tourist_id}

- **Purpose:** Generate a signed JWT digital ID and a QR code for an existing
  tourist.
- **Path parameters:**

| Parameter | Type | Description |
|---|---|---|
| `tourist_id` | integer | The tourist's ID (as returned by `POST /api/register`). |

**Request body:** None.

### Success response (`200 OK`):

```json
{
  "tourist_id": 1,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6...",
  "expires_at": "2026-08-26T15:09:29Z",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
}
```

| Field | Type | Description |
|---|---|---|
| `tourist_id` | integer | The ID of the tourist the token was issued to. |
| `token` | string | Signed JWT (HS256) encoding `sub`, `name`, `iat`, `exp`. |
| `expires_at` | string (ISO 8601, UTC) | Token expiration timestamp. |
| `qr_code` | string (data URL) | `data:image/png;base64,...` PNG QR code encoding the token. |

### Error responses

| Status | Condition | Body |
|---|---|---|
| `404 Not Found` | No tourist with the given `tourist_id` | `{"detail": "Tourist with id 999999 not found."}` |

---

## POST /api/verify-id

- **Purpose:** Verify a signed tourist digital ID (JWT). Validates the
  signature, expiration, and tourist existence.
- **Request body** (`application/json`):

| Field | Type | Required | Description |
|---|---|---|---|
| `token` | string | yes | The signed JWT to verify. |

**Request example:**

```json
{"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiw..."}
```

### Success — valid token (`200 OK`):

```json
{
  "valid": true,
  "tourist": {
    "id": 1,
    "name": "Rahul Kumar"
  }
}
```

### Success — invalid token (`200 OK`):

Returned for a tampered, malformed, expired token, or when the token is valid
but the tourist no longer exists in the database:

```json
{
  "valid": false,
  "tourist": null
}
```

### Error responses

| Status | Condition | Body |
|---|---|---|
| `422 Unprocessable Content` | Request body is missing `token` or is not valid JSON | `{"detail": [{"loc": ["body", "token"], "msg": "Field required", "type": "missing"}]}` |

---

## GET /api/incidents

- **Purpose:** Return all recorded safety incidents (synthetic demo dataset).
  Consumed by the risk engine and future authority dashboard.
- **Query parameters:** None (no pagination at prototype scale).

### Success response (`200 OK`):

```json
[
  {
    "id": 1,
    "latitude": 16.5047,
    "longitude": 80.618,
    "incident_type": "theft",
    "severity": 3,
    "occurred_at": "2026-07-02T14:22:00"
  }
]
```

| Field | Type | Description |
|---|---|---|
| `id` | integer | Incident ID. |
| `latitude` / `longitude` | number | Coordinates (-90..90 / -180..180). |
| `incident_type` | string | One of: `theft`, `harassment`, `medical`, `accident`, `missing_person`, `unsafe_area`. |
| `severity` | integer | 1 (low) - 5 (high). |
| `occurred_at` | string (ISO 8601) | When the incident occurred. |

---

## POST /api/sos

- **Purpose:** Raise an emergency SOS event for a registered tourist.
- **Request body** (`application/json`):

| Field | Type | Required | Description |
|---|---|---|---|
| `tourist_id` | integer | yes | Existing tourist; must be > 0. |
| `latitude` | number | yes | -90..90. |
| `longitude` | number | yes | -180..180. |

**Request example:**

```json
{"tourist_id": 1, "latitude": 16.3067, "longitude": 80.4365}
```

> `status` is set by the server (`"active"`) and **cannot** be supplied by
> the client — unknown fields are rejected.

### Success response (`201 Created`):

```json
{
  "id": 1,
  "tourist_id": 1,
  "latitude": 16.3067,
  "longitude": 80.4365,
  "status": "active",
  "created_at": "2026-08-25T18:40:12"
}
```

### Error responses

| Status | Condition | Body |
|---|---|---|
| `404 Not Found` | Tourist does not exist | `{"detail": "Tourist with id 999999 not found."}` |
| `422 Unprocessable Content` | Out-of-range coordinates or client-provided `status`/extra field | standard FastAPI validation body |

---

## GET /api/sos

- **Purpose:** Return stored SOS events (authority-dashboard polling; no
  WebSockets in the prototype).
- **Query parameters:** None.

### Success response (`200 OK`):

```json
{
  "sos_events": [
    {
      "id": 1,
      "tourist_id": 1,
      "latitude": 16.3067,
      "longitude": 80.4365,
      "status": "active",
      "created_at": "2026-08-25T18:40:12"
    }
  ]
}
```

---

## GET /api/risk-zones

- **Purpose:** Cluster incidents + SOS events into geographic risk zones with
  DBSCAN and score each zone (0-100). Read-only; safe to poll.
- **Query parameters:**

| Parameter | Type | Default | Constraints | Description |
|---|---|---|---|---|
| `eps_km` | float | `0.5` (env `RISK_EPS_KM`) | > 0 and <= 10 | DBSCAN neighbourhood radius in kilometres |
| `min_samples` | integer | `4` (env `RISK_MIN_SAMPLES`) | >= 1 and <= 50 | Minimum nearby points to form a dense zone |

Violating constraints returns `422 Unprocessable Content`.

**Request example:** `GET /api/risk-zones?eps_km=0.5&min_samples=4`

### Success response (`200 OK`):

```json
{
  "generated_at": "2026-08-25T19:05:31.123456Z",
  "eps_km": 0.5,
  "min_samples": 4,
  "total_incidents": 150,
  "total_sos": 3,
  "noise_incidents": 35,
  "noise_sos": 0,
  "zone_count": 6,
  "zones": [
    {
      "zone_id": 1,
      "center_latitude": 16.599462,
      "center_longitude": 80.449307,
      "radius_meters": 943.1,
      "point_count": 25,
      "incident_count": 25,
      "sos_count": 0,
      "dominant_incident_type": "missing_person",
      "avg_severity": 3.92,
      "distinct_types": 5,
      "last_event_at": "2026-08-20T21:14:00",
      "risk_score": 96,
      "risk_level": "CRITICAL"
    },
    {
      "zone_id": 2,
      "center_latitude": 16.475095,
      "center_longitude": 80.549394,
      "radius_meters": 1134.9,
      "point_count": 26,
      "incident_count": 25,
      "sos_count": 1,
      "dominant_incident_type": "theft",
      "avg_severity": 3.35,
      "distinct_types": 4,
      "last_event_at": "2026-08-18T09:03:00",
      "risk_score": 92,
      "risk_level": "CRITICAL"
    }
  ]
}
```

### Response fields

| Field | Type | Description |
|---|---|---|
| `generated_at` | string (ISO 8601, UTC) | When the computation ran. |
| `eps_km` / `min_samples` | number / integer | Parameters actually used. |
| `total_incidents` / `total_sos` | integer | Rows considered. |
| `noise_incidents` / `noise_sos` | integer | Points not assigned to any zone (label -1); never silently dropped. |
| `zone_count` | integer | Number of zones. |
| `zones[].center_latitude/longitude` | number | Mean of member coordinates. |
| `zones[].radius_meters` | number | Max distance from center to a member (for Leaflet circles). |
| `zones[].risk_score` | integer | 0-100; `round(100*(0.45*density + 0.40*severity + 0.15*variety))`. |
| `zones[].risk_level` | string | `>=75 CRITICAL`, `>=50 HIGH`, `>=25 MODERATE`, else `LOW`. |

Output is sorted by `risk_score` descending (deterministic tie-breaks), so
`zones[0]` is always the highest-risk area.

---

## GET /api/patrol-plan

- **Purpose:** Recommend patrol-unit locations over the current DBSCAN risk
  zones using deterministic greedy weighted-coverage (p-median style).
- **Query parameters:**

| Parameter | Type | Default | Constraints | Description |
|---|---|---|---|---|
| `units` | integer | `3` (env `PATROL_NUM_UNITS`) | >= 1 and <= 20 | Patrol units to place |
| `service_radius_km` | float | `2.0` (env `PATROL_SERVICE_RADIUS_KM`) | > 0 and <= 25 | Coverage radius around each patrol |
| `eps_km` / `min_samples` | float / integer | `0.5` / `4` | as `/api/risk-zones` | Passed through to upstream clustering |

Violating constraints returns `422 Unprocessable Content`.

**Request example:** `GET /api/patrol-plan?units=3&service_radius_km=2.0`

### Success response (`200 OK`):

```json
{
  "generated_at": "2026-08-26T10:12:44.512345Z",
  "algorithm": "greedy_pmedian_weighted_coverage",
  "requested_units": 3,
  "placed_units": 3,
  "service_radius_km": 2.0,
  "total_zones": 6,
  "total_weight": 458,
  "covered_weight": 298,
  "coverage_pct": 65.07,
  "patrols": [
    {
      "unit_id": 1,
      "latitude": 16.448418,
      "longitude": 80.680215,
      "covers_zone_ids": [5, 6],
      "covered_zone_count": 2,
      "covered_weight": 114,
      "coverage_share_pct": 24.89,
      "avg_zone_distance_km": 0.402,
      "highest_risk_level": "HIGH"
    }
  ],
  "uncovered_zones": [
    {"zone_id": 3, "risk_score": 80, "risk_level": "CRITICAL",
     "center_latitude": 16.503141, "center_longitude": 80.61929}
  ]
}
```

### Response fields

| Field | Type | Description |
|---|---|---|
| `algorithm` | string | Always `greedy_pmedian_weighted_coverage`. |
| `requested_units` / `placed_units` | integer | Asked-for vs actually placeable (`placed <= min(units, zone_count)`). |
| `total_weight` / `covered_weight` | integer | Sum of zone `risk_score`; covered portion served by patrols. |
| `coverage_pct` | number | `100 * covered_weight / total_weight`. |
| `patrols[].latitude/longitude` | number | Chosen zone center (deployment hint). |
| `patrols[].covers_zone_ids` | int array | Served zone IDs, ascending. |
| `patrols[].covered_weight` / `coverage_share_pct` | — | Weight served and its share of `total_weight`. |
| `patrols[].highest_risk_level` | string | Most severe level among served zones. |
| `uncovered_zones[]` | object array | Zones beyond reach of every placed patrol (explicit gap report). |

Output is deterministic for identical inputs; empty databases return
`patrols: []` with zeroed totals.

---

## GET /api/risk-heatmap

- **Purpose:** Leaflet-ready view of the DBSCAN risk zones. Pure adapter over
  the Prompt 5 engine — no clustering logic duplicated; deterministic ordering.
- **Query parameters:**

| Parameter | Type | Default | Constraints | Description |
|---|---|---|---|---|
| `eps_km` | float | `0.5` (env `RISK_EPS_KM`) | > 0 and <= 10 | Upstream DBSCAN radius |
| `min_samples` | integer | `4` (env `RISK_MIN_SAMPLES`) | >= 1 and <= 50 | Core-point threshold |

**Request example:** `GET /api/risk-heatmap?eps_km=0.5&min_samples=4`

### Success response (`200 OK`):

```json
{
  "generated_at": "2026-08-26T10:44:02.881234Z",
  "eps_km": 0.5,
  "min_samples": 4,
  "total_incidents": 150,
  "total_sos": 0,
  "noise_incidents": 35,
  "noise_sos": 0,
  "marker_count": 6,
  "markers": [
    {
      "zone_id": 1,
      "center": [16.599462, 80.449307],
      "radius_meters": 943.1,
      "risk_score": 96,
      "risk_level": "CRITICAL",
      "point_count": 25,
      "incident_count": 25,
      "sos_count": 0,
      "dominant_incident_type": "missing_person",
      "avg_severity": 3.92,
      "last_event_at": "2026-08-20T21:14:00"
    }
  ]
}
```

### Marker fields

| Field | Type | Description |
|---|---|---|
| `zone_id` | integer | Source risk zone. |
| `center` | `[lat, lon]` array | Direct input for Leaflet `L.circle(center, ...)`. |
| `radius_meters` | number | Circle radius in metres. |
| `risk_score` / `risk_level` | integer / string | Zone score (0–100) and band — use as the marker colour key. |
| `point_count`, `incident_count`, `sos_count` | integers | Composition of the zone. |
| `dominant_incident_type`, `avg_severity`, `last_event_at` | string / number / datetime | Tooltip metadata. |

Markers are ordered by `risk_score` descending. Empty databases return
`markers: []`.

---

## GET /api/patrol-recommendations

- **Purpose:** Map-ready patrol placements: reuses the Prompt 6 greedy
  optimizer verbatim and enriches every unit with the zones it serves.
- **Query parameters:** identical to `/api/patrol-plan` —

| Parameter | Type | Default | Constraints | Description |
|---|---|---|---|---|
| `units` | integer | `3` (env `PATROL_NUM_UNITS`) | >= 1 and <= 20 | Patrol units to place |
| `service_radius_km` | float | `2.0` (env `PATROL_SERVICE_RADIUS_KM`) | > 0 and <= 25 | Coverage radius per patrol |
| `eps_km` / `min_samples` | float / int | `0.5` / `4` | as `/api/risk-zones` | Passed through to clustering |

### Success response (`200 OK`):

```json
{
  "generated_at": "2026-08-26T10:45:10.220111Z",
  "algorithm": "greedy_pmedian_weighted_coverage",
  "requested_units": 3,
  "placed_units": 3,
  "service_radius_km": 2.0,
  "total_zones": 6,
  "total_weight": 458,
  "covered_weight": 298,
  "coverage_pct": 65.07,
  "recommendations": [
    {
      "unit_id": 1,
      "position": [16.448418, 80.680215],
      "service_radius_km": 2.0,
      "covers_zone_ids": [5, 6],
      "covered_zone_count": 2,
      "covered_weight": 114,
      "coverage_share_pct": 24.89,
      "avg_zone_distance_km": 0.402,
      "highest_risk_level": "HIGH",
      "served_zones": [
        {"zone_id": 5, "risk_score": 64, "risk_level": "HIGH", "distance_km": 0.0},
        {"zone_id": 6, "risk_score": 50, "risk_level": "HIGH", "distance_km": 0.803}
      ]
    }
  ],
  "uncovered_zones": [
    {"zone_id": 3, "risk_score": 80, "risk_level": "CRITICAL",
     "center_latitude": 16.503141, "center_longitude": 80.61929}
  ]
}
```

### Response fields

| Field | Type | Description |
|---|---|---|
| `recommendations[].position` | `[lat, lon]` array | Leaflet marker pair at the chosen zone center. |
| `recommendations[].served_zones[]` | object array | Per-served-zone `zone_id`, `risk_score`, `risk_level`, and haversine `distance_km` from the patrol — sorted nearest-first. |
| all other fields | — | Identical semantics to `/api/patrol-plan`. |

Deterministic for identical inputs; empty databases return
`recommendations: []`.

---

## JWT Token Format

The digital-ID token is a standard JWT (RFC 7519) signed with **HS256**.

**Header:**

```json
{"alg": "HS256", "typ": "JWT"}
```

**Payload claims:**

| Claim | Type | Description |
|---|---|---|
| `sub` | string | The tourist's ID (stringified). |
| `name` | string | The tourist's name. |
| `iat` | number | Issued-at timestamp (seconds since epoch, UTC). |
| `exp` | number | Expiration timestamp (issued-at + 24 h, UTC). |

> **Security note:** The JWT does **not** include the tourist's phone number or
> any other personally identifiable information beyond `name`. The secret key
> used to sign the token is loaded from the `JWT_SECRET_KEY` environment
> variable and is never exposed via the API or logged.
