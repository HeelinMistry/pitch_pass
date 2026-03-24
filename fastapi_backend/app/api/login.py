import base64
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json

from app.db.mock_db import get_db, save_db, get_user_by_username
from webauthn.helpers import parse_authentication_credential_json
from webauthn.helpers.structs import PublicKeyCredentialDescriptor
from app.core.auth_utils import create_access_token

from webauthn import (
    generate_authentication_options,
    verify_authentication_response,
    options_to_json
)
from app.core.config import RP_ID, ORIGIN

router = APIRouter(prefix="/auth/login", tags=["Authentication"])


class VerifyAuthReq(BaseModel):
    username: str
    response: dict


@router.get("/options/{username}")
async def get_login_options(username: str):
    db = get_db()
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_passkeys = [p for p in db["passkeys"] if p["user_id"] == user["id"]]

    # 2. FIX: Convert dicts to PublicKeyCredentialDescriptor objects
    # Also decode the ID from Base64 string back to bytes
    allow_credentials = []
    for p in user_passkeys:
        allow_credentials.append(PublicKeyCredentialDescriptor(
            id=base64.b64decode(p["id"])
        ))

    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=allow_credentials,
    )

    # 3. Store the challenge (as a Base64 string)
    db["challenges"][username] = base64.b64encode(options.challenge).decode('utf-8')
    save_db(db)

    return json.loads(options_to_json(options))


@router.post("/verify")
async def verify_login(payload: VerifyAuthReq):
    db = get_db()
    username = payload.username

    # 1. Retrieve and decode the challenge
    challenges = db.get("challenges", {})
    if username not in challenges:
        raise HTTPException(status_code=400, detail="Challenge not found")

    encoded_challenge = challenges.pop(username)
    # The library MUST have the challenge in bytes
    expected_challenge = base64.b64decode(encoded_challenge)

    try:
        # 2. Parse the incoming credential
        credential = parse_authentication_credential_json(payload.response)
        normalized_id = base64url_to_standard_base64(credential.id)
        # 3. Find the passkey
        # We use credential.id (the string ID from the browser)
        target_passkey = next(
            (p for p in db["passkeys"] if p["id"] == credential.id),
            None
        )

        if not target_passkey:
            # If standard match fails, try a "URL Safe" check
            # Some browsers/libraries swap +/ with -_
            # normalized_id = credential.id.replace('-', '+').replace('_', '/')
            target_passkey = next(
                (p for p in db["passkeys"] if p["id"] == normalized_id),
                None
            )

        if not target_passkey:
            save_db(db)
            raise HTTPException(status_code=404, detail="Device not recognized. Please register this device.")

        # 4. Cryptographic verification
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            credential_public_key=bytes.fromhex(target_passkey["public_key"]),
            credential_current_sign_count=int(target_passkey["sign_count"]),
            require_user_verification=True,
        )
    except Exception as e:
        print(f"❌ LOGIN ERROR: {str(e)}")
        save_db(db)
        raise HTTPException(status_code=400, detail=str(e))

    # 5. Update sign count and save
    target_passkey["sign_count"] = verification.new_sign_count
    save_db(db)

    # 6. Generate the real JWT!
    # We store the user_id as the "subject" (sub) and throw in the username for convenience
    token_data = {
        "sub": username,  # Standard practice: 'sub' is the human-readable name
        "username": username,  # For convenience
        "id": target_passkey["user_id"]  # Explicitly add the UUID as 'id'
    }
    access_token = create_access_token(data=token_data)

    return {
        "status": "success",
        "user_id": target_passkey["user_id"],
        "access_token": access_token,  # <-- RETURN REAL TOKEN
        "token_type": "bearer"  # <-- STANDARD OAUTH2 FORMAT
    }

def base64url_to_standard_base64(s: str) -> str:
    """Converts Base64URL string to Standard Base64 with padding."""
    # 1. Replace URL-safe characters
    s = s.replace('-', '+').replace('_', '/')
    # 2. Add padding '=' if necessary
    padding = len(s) % 4
    if padding:
        s += '=' * (4 - padding)
    return s