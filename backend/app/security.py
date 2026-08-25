"""
Digital-ID security helpers.

These functions create and validate signed JWT tokens that act as a
cryptographic digital ID for a registered tourist. The JWT contains only the
minimum identity claims (id + name) and NEVER includes the tourist's phone
number.
"""
import datetime

import jwt

from app.config import JWT_ALGORITHM, JWT_EXPIRATION_HOURS, JWT_SECRET_KEY

# Token lifetime expressed as a datetime.timedelta for jwt's exp claim.
_TOKEN_TTL = datetime.timedelta(hours=JWT_EXPIRATION_HOURS)


def create_token(*, tourist_id: int, name: str) -> str:
    """Sign and return a JWT for the given tourist.

    Claims:
      - sub: tourist ID (string, as per JWT conventions)
      - name: tourist name
      - iat: issued-at timestamp
      - exp: expiration timestamp
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(tourist_id),
        "name": name,
        "iat": now,
        "exp": now + _TOKEN_TTL,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Verify signature + expiration and return the decoded payload.

    Raises jwt.InvalidTokenError (or a subclass such as ExpiredSignatureError
    or InvalidSignatureError) if the token is invalid in any way.
    """
    return jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
        options={"require": ["exp", "iat", "sub"]},
    )


def token_expiry(token: str) -> datetime.datetime:
    """Return the expiration datetime of a token (without verifying it).

    Used on the generation path, where the token was just signed and is known
    to be valid.
    """
    unverified = jwt.decode(token, options={"verify_signature": False})
    return datetime.datetime.fromtimestamp(unverified["exp"], datetime.timezone.utc)
