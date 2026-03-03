from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
import json

from webauthn import (
    generate_authentication_options,
    verify_authentication_response,
    options_to_json
)
# Add this import for V2
from webauthn.helpers import parse_authentication_credential_json

from app.core.config import RP_ID, ORIGIN
from app.db.mock_db import pending_challenges, user_credentials

# Use Router instead of FastAPI()
router = APIRouter(prefix="/auth/login", tags=["Authentication"])


class VerifyAuthReq(BaseModel):
    username: str
    response: dict


@router.get("/options/{username}")
async def get_login_options(username: str):
    if username not in user_credentials:
        raise HTTPException(status_code=404, detail="User not found")

    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=[{"id": cred["id"], "type": "public-key"} for cred in user_credentials[username]],
    )

    pending_challenges[username] = options.challenge
    return json.loads(options_to_json(options))


@router.post("/verify")
async def verify_login(payload: VerifyAuthReq):
    username = payload.username

    if username not in pending_challenges:
        raise HTTPException(status_code=400, detail="Challenge not found")

    expected_challenge = pending_challenges.pop(username)

    # V2 Logic: Parse the credential from JSON
    try:
        credential = parse_authentication_credential_json(payload.response)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid credential: {str(e)}")

    # In production: Use credential.id to find the specific public key
    user_creds = user_credentials.get(username, [])
    if not user_creds:
        raise HTTPException(status_code=404, detail="No credentials found for user")

    # Simple lookup for our mock:
    cred = next((c for c in user_creds if c["id"] == credential.raw_id), user_creds[0])

    try:
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            credential_public_key=cred["public_key"],
            credential_current_sign_count=cred["sign_count"],
            require_user_verification=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

    cred["sign_count"] = verification.new_sign_count
    return {"status": "success", "token": "dummy-jwt-token"}