import json

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
import uuid
import base64

from webauthn.helpers import parse_registration_credential_json, parse_authentication_credential_json
from webauthn.helpers.structs import PublicKeyCredentialDescriptor

from webauthn import (
    generate_registration_options, verify_registration_response,
    generate_authentication_options, verify_authentication_response,
    options_to_json
)
from app.core.config import RP_ID, RP_NAME, ORIGIN
from app.core.auth_utils import create_access_token
from app.db.database import get_db
from app.db import models, crud
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])


class AuthVerifyReq(BaseModel):
    username: str
    response: dict


# --- REGISTRATION ---
@router.get("/register/options/{username}")
async def get_reg_options(request: Request, username: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username)
    user_id = user.id if user else str(uuid.uuid4())

    options = generate_registration_options(
        rp_id=RP_ID, rp_name=RP_NAME,
        user_id=user_id.encode("utf-8"), user_name=username
    )

    # FIX: Encode the bytes challenge to a string so the session can save it
    request.session["registration_challenge"] = {
        "challenge": base64.b64encode(options.challenge).decode('utf-8'),
        "user_id": user_id
    }

    # Also ensure the response is a proper JSON object, not a string
    return json.loads(options_to_json(options))

@router.post("/register/verify")
async def verify_reg(payload: AuthVerifyReq, request: Request, db: Session = Depends(get_db)):
    challenge_data = request.session.get("registration_challenge")
    if not challenge_data: raise HTTPException(400, "Missing challenge")

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
        request.session.pop("registration_challenge", None)

    return {"status": "success"}


# --- LOGIN ---
@router.get("/login/options/{username}")
async def get_log_options(request: Request, username: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(404, "User not found")

    user_passkeys = db.query(models.Passkey).filter(models.Passkey.user_id == user.id).all()

    # FIX: Wrap the dictionary in a PublicKeyCredentialDescriptor
    # and decode the string ID into bytes.
    allow_credentials = []
    for p in user_passkeys:
        # Handle base64url padding if necessary
        padded_id = p.id + '=' * (4 - len(p.id) % 4)
        allow_credentials.append(
            PublicKeyCredentialDescriptor(id=base64.urlsafe_b64decode(padded_id))
        )

    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=allow_credentials
    )

    # Store the challenge in the session (encoded to string)
    request.session["login_challenge"] = {
        "challenge": base64.b64encode(options.challenge).decode('utf-8'),
        "username": username
    }

    return json.loads(options_to_json(options))


@router.post("/login/verify")
async def verify_log(payload: AuthVerifyReq, request: Request, db: Session = Depends(get_db)):
    # 1. Retrieve challenge from SessionMiddleware
    challenge_data = request.session.get("login_challenge")
    if not challenge_data or challenge_data["username"] != payload.username:
        raise HTTPException(status_code=400, detail="Login challenge not found or expired")

    expected_challenge = base64.b64decode(challenge_data["challenge"])

    try:
        # 2. Parse the credential from the browser
        credential = parse_authentication_credential_json(payload.response)

        # 3. Find the specific Passkey in SQL using the Credential ID
        target_passkey = db.query(models.Passkey).filter(models.Passkey.id == credential.id).first()

        if not target_passkey:
            # Fallback check for URL-safe base64 variations if necessary
            normalized_id = base64url_to_standard_base64(credential.id)
            target_passkey = db.query(models.Passkey).filter(models.Passkey.id == normalized_id).first()

        if not target_passkey:
            raise HTTPException(status_code=404, detail="Device not recognized. Please register this device.")

        # 4. Perform Cryptographic Verification
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            credential_public_key=bytes.fromhex(target_passkey.public_key),
            credential_current_sign_count=target_passkey.sign_count,
            require_user_verification=True,
        )
    except Exception as e:
        print(f"❌ LOGIN VERIFICATION ERROR: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    # 5. Update the sign count in SQL (Security requirement of WebAuthn)
    target_passkey.sign_count = verification.new_sign_count

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update security counters")
    finally:
        request.session.pop("login_challenge", None)

    # 6. Generate the Production JWT
    # We use the UUID as the 'sub' (subject) for architectural stability
    token_data = {
        "sub": target_passkey.user_id,  # The UUID
        "username": payload.username,  # Friendly name
        "id": target_passkey.user_id  # Explicit ID field
    }
    access_token = create_access_token(data=token_data)

    return {
        "status": "success",
        "user_id": target_passkey.user_id,
        "access_token": access_token,
        "token_type": "bearer"
    }


def base64url_to_standard_base64(s: str) -> str:
    """Converts Base64URL string to Standard Base64 with padding."""
    s = s.replace('-', '+').replace('_', '/')
    padding = len(s) % 4
    if padding:
        s += '=' * (4 - padding)
    return s