"""Tourist digital-ID and QR verification routes."""
import base64
import io

import qrcode
from fastapi import APIRouter, Body, Depends, HTTPException, status
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tourist import Tourist
from app.schemas.digital_id import (
    DigitalIdRequest,
    DigitalIdResponse,
    VerifyResponse,
    VerifiedTourist,
)
from app.security import create_token, decode_token, token_expiry

router = APIRouter()


def _make_qr_data_url(token: str) -> str:
    """Render a PNG QR code encoding the token and return it as a data URL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


@router.post(
    "/digital-id/{tourist_id}",
    response_model=DigitalIdResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Tourist not found"}},
)
def generate_digital_id(
    tourist_id: int,
    db: Session = Depends(get_db),
) -> DigitalIdResponse:
    """Generate a signed digital-ID JWT and a QR code for an existing tourist.

    The token encodes only the tourist ID and name; it never contains the
    phone number. Returns 404 if the tourist does not exist.
    """
    tourist = db.get(Tourist, tourist_id)
    if tourist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tourist with id {tourist_id} not found.",
        )

    token = create_token(tourist_id=tourist.id, name=tourist.name)
    expires_at = token_expiry(token)
    qr_code = _make_qr_data_url(token)

    return DigitalIdResponse(
        tourist_id=tourist.id,
        token=token,
        expires_at=expires_at,
        qr_code=qr_code,
    )


@router.post(
    "/verify-id",
    response_model=VerifyResponse,
    status_code=status.HTTP_200_OK,
)
def verify_id(
    payload: DigitalIdRequest = Body(...),
    db: Session = Depends(get_db),
) -> VerifyResponse:
    """Verify a tourist's signed digital ID.

    Validates the JWT signature and expiration, then looks up the tourist
    in SQLite. The tourist ID is taken *only* from the signed token (never
    from the request directly).
    """
    # --- Verify the JWT (signature + expiration) ---
    try:
        claims = decode_token(payload.token)
    except InvalidTokenError:
        return VerifyResponse(valid=False, tourist=None)

    # --- Look up the tourist referenced by the signed token ---
    try:
        tourist_id = int(claims["sub"])
    except (KeyError, TypeError, ValueError):
        return VerifyResponse(valid=False, tourist=None)

    tourist = db.get(Tourist, tourist_id)
    if tourist is None:
        # Token was valid and signed by us, but the tourist record is gone.
        return VerifyResponse(valid=False, tourist=None)

    return VerifyResponse(
        valid=True,
        tourist=VerifiedTourist(id=tourist.id, name=tourist.name),
    )
