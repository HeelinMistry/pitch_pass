import base64

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
import uuid
from app.db.mock_db import get_db, save_db, get_user_by_username

# The prefix here means all routes in this file start with /api/auth/register
router = APIRouter(prefix="/auth/register", tags=["Registration"])


class VerifyRegistrationReq(BaseModel):
    username: str
    response: dict


@router.get("/options/{username}")  # Cleaned path: becomes /api/auth/register/options/{username}
async def get_registration_options(username: str, current_user_id: str = None):
    db = get_db()
    user = get_user_by_username(username)

    # PRIORITY 1: If user is already logged in, we are definitely LINKING a device
    if current_user_id:
        user_id = current_user_id
    # PRIORITY 2: If username exists, we are LINKING via username lookup
    elif user:
        user_id = user["id"]
    # PRIORITY 3: Brand new user
    else:
        user_id = str(uuid.uuid4())

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=user_id.encode("utf-8"),
        user_name=username,
    )

    # FIX: Convert bytes to a base64 string for JSON storage
    db["challenges"][username] = {
        "challenge": base64.b64encode(options.challenge).decode('utf-8'),
        "user_id": user_id
    }
    save_db(db)

    return json.loads(options_to_json(options))


@router.post("/verify")  # Cleaned path: becomes /api/auth/register/verify
async def verify_registration(payload: VerifyRegistrationReq):
    db = get_db()
    username = payload.username

    if username not in db["challenges"]:
        raise HTTPException(status_code=400, detail="Challenge not found")

    challenge_data = db["challenges"].pop(username)
    expected_challenge = base64.b64decode(challenge_data["challenge"])

    try:
        credential = parse_registration_credential_json(payload.response)
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            require_user_verification=True,
        )
    except Exception as e:
        print(f"❌ VERIFICATION ERROR: {str(e)}")  # <--- ADD THIS LINE
        save_db(db)  # Save the popped challenge
        raise HTTPException(status_code=400, detail=str(e))

    # 1. Ensure user exists in the "users" table
    user_id = challenge_data["user_id"]
    if user_id not in db["users"]:
        db["users"][user_id] = {"id": user_id, "username": username}

    cred_id_str = base64.b64encode(verification.credential_id).decode('utf-8')
    # 2. Append the new device to the "passkeys" list
    db["passkeys"].append({
        "id": cred_id_str,
        "user_id": user_id,
        "public_key": verification.credential_public_key.hex(),  # Store as hex for JSON
        "sign_count": verification.sign_count
    })

    save_db(db)
    return {"status": "success", "user_id": user_id}