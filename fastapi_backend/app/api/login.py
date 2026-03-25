import base64
import json
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from webauthn import (
    generate_authentication_options,
    verify_authentication_response,
    options_to_json
)
from webauthn.helpers import parse_authentication_credential_json
from webauthn.helpers.structs import PublicKeyCredentialDescriptor

from app.core.config import RP_ID, ORIGIN
from app.core.auth_utils import create_access_token
from app.db.database import get_db
from app.db import models, crud

router = APIRouter(prefix="/auth/login", tags=["Authentication"])


class VerifyAuthReq(BaseModel):
    username: str
    response: dict


@router.get("/options/{username}")
async def get_login_options(
        request: Request,
        username: str,
        db: Session = Depends(get_db)
):
    # 1. Look up user in SQL
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Get all registered passkeys for this user from SQL
    user_passkeys = db.query(models.Passkey).filter(models.Passkey.user_id == user.id).all()

    def add_padding(s: str):
        # Base64 strings must have a length multiple of 4
        return s + "=" * (4 - len(s) % 4) if len(s) % 4 != 0 else s

    allow_credentials = [
        PublicKeyCredentialDescriptor(id=base64.urlsafe_b64decode(add_padding(p.id)))
        for p in user_passkeys
    ]

    # 3. Generate WebAuthn Authentication Options
    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=allow_credentials,
    )

    # 4. Store challenge in Session (RAM/Cookie)
    request.session["login_challenge"] = {
        "challenge": base64.b64encode(options.challenge).decode('utf-8'),
        "username": username
    }

    return json.loads(options_to_json(options))


@router.post("/verify")
async def verify_login(
        request: Request,
        payload: VerifyAuthReq,
        db: Session = Depends(get_db)
):
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