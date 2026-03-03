from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    options_to_json,
)
from webauthn.helpers import parse_registration_credential_json

from app.core.config import RP_ID, RP_NAME, ORIGIN
from app.db.mock_db import pending_challenges, user_credentials

# The prefix here means all routes in this file start with /api/auth/register
router = APIRouter(prefix="/auth/register", tags=["Registration"])


class VerifyRegistrationReq(BaseModel):
    username: str
    response: dict


@router.get("/options/{username}")  # Cleaned path: becomes /api/auth/register/options/{username}
async def get_registration_options(username: str):
    # In a scalable app, use a persistent user UUID, not the raw username string
    user_id = username.encode("utf-8")

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=user_id,
        user_name=username,
    )

    # Store challenge (In production, use Redis with an expiry)
    pending_challenges[username] = options.challenge

    return json.loads(options_to_json(options))


@router.post("/verify")  # Cleaned path: becomes /api/auth/register/verify
async def verify_registration(payload: VerifyRegistrationReq):
    username = payload.username

    if username not in pending_challenges:
        raise HTTPException(status_code=400, detail="Challenge not found or expired")

    expected_challenge = pending_challenges.pop(username)

    try:
        # Crucial for WebAuthn v2: parse the JSON dictionary into a library object
        credential = parse_registration_credential_json(payload.response)

        verification = verify_registration_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            require_user_verification=True,
        )
    except Exception as e:
        # If verification fails, we don't save anything
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

    # Store credential
    if username not in user_credentials:
        user_credentials[username] = []

    user_credentials[username].append({
        "id": verification.credential_id,
        "public_key": verification.credential_public_key,
        "sign_count": verification.sign_count,
    })

    return {"status": "success", "message": "Passkey registered successfully!"}