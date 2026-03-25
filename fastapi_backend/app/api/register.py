import base64
import uuid
import json
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    options_to_json,
)
from webauthn.helpers import parse_registration_credential_json

from app.core.config import RP_ID, RP_NAME, ORIGIN
from app.db.database import get_db
from app.db import models, crud

router = APIRouter(prefix="/auth/register", tags=["Registration"])


class VerifyRegistrationReq(BaseModel):
    username: str
    response: dict


@router.get("/options/{username}")
async def get_registration_options(
        request: Request,
        username: str,
        db: Session = Depends(get_db)
):
    # 1. Check if user exists in SQL
    user = crud.get_user_by_username(db, username)

    if user:
        user_id = user.id
    else:
        # Generate new UUID for brand new user
        user_id = str(uuid.uuid4())

    # 2. Generate WebAuthn Options
    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=user_id.encode("utf-8"),
        user_name=username,
    )

    # 3. Store challenge in the SESSION (RAM/Cookie) instead of db.json
    # This automatically cleans up when the browser session ends
    request.session["registration_challenge"] = {
        "challenge": base64.b64encode(options.challenge).decode('utf-8'),
        "user_id": user_id,
        "username": username
    }

    return json.loads(options_to_json(options))


@router.post("/verify")
async def verify_registration(
        request: Request,
        payload: VerifyRegistrationReq,
        db: Session = Depends(get_db)
):
    # 1. Retrieve challenge from SessionMiddleware
    challenge_data = request.session.get("registration_challenge")

    if not challenge_data or challenge_data["username"] != payload.username:
        print("❌ SESSION ERROR: No challenge found in request.session. Check CORS/Cookies.")
        raise HTTPException(status_code=400, detail="Registration challenge not found or expired")

    expected_challenge = base64.b64decode(challenge_data["challenge"])

    try:
        # 2. Parse and Verify the Credential
        credential = parse_registration_credential_json(payload.response)
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            require_user_verification=True,
        )
    except Exception as e:
        print(f"❌ WEBAMUTHN VERIFICATION ERROR: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    # 3. SQL PERSISTENCE: Ensure User exists
    user_id = challenge_data["user_id"]
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        user = models.User(id=user_id, username=payload.username)
        db.add(user)

    # 4. SQL PERSISTENCE: Save the new Passkey
    # We use the credential ID provided by the browser
    new_passkey = models.Passkey(
        id=credential.id,
        user_id=user.id,
        public_key=verification.credential_public_key.hex(),
        sign_count=verification.sign_count
    )

    db.add(new_passkey)

    try:
        db.commit()  # Save both User and Passkey to pitchpass.db
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database save failed")
    finally:
        # Clear the challenge from session now that it's used
        request.session.pop("reg_challenge", None)

    return {"status": "success", "user_id": user_id}