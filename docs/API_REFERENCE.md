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
