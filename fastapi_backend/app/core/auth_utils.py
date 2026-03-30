from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(data: dict):
    to_encode = data.copy()

    # Safety Check: Ensure the identity and UUID are present
    if "sub" not in to_encode or "id" not in to_encode:
        # Logging this helps you catch the "401 loop" during development
        print("WARNING: Creating token without 'sub' or 'id'. This will cause 401 errors.")

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# This tells FastAPI to look for a "Bearer <token>" in the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the JWT
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("id")
        username: str = payload.get("username")

        if user_id is None or username is None:
            raise credentials_exception

        # Return a dictionary (or a DB User object) that the route can use
        return {"id": user_id, "username": username}

    except JWTError:
        raise credentials_exception