from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.api import login, register
from app.core.config import SECRET_CHALLENGE_KEY
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.core.auth_utils import JWT_SECRET_KEY, JWT_ALGORITHM
from jose import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="Scalable WebAuthn API")

# 1. Configure CORS
# Allow the frontend to communicate with the backend.
origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Add Session Middleware
# WebAuthn requires storing "challenges" securely between requests.
app.add_middleware(SessionMiddleware, secret_key=SECRET_CHALLENGE_KEY)

# Include the routers
app.include_router(login.router, prefix="/api")
app.include_router(register.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "API is online. Go to /docs for Swagger UI"}


# This is a 'Dependency' that protects our routes
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload # Returns {'sub': user_id, 'username': '...'}
    except:
        raise HTTPException(status_code=401, detail="Invalid Session")

@app.get("/api/dashboard/matches")
async def get_matches(current_user: dict = Depends(get_current_user)):
    # For now, let's return a list with one real match from our logic
    return [
        {
            "id": "match_001",
            "title": "Community 5-a-side",
            "time": "18:00",
            "date": "MON 22 MAR",
            "location": "Powerleague Pitch 2",
            "status": "Ready",
            "joined": 8,
            "max": 10
        }
    ]


# To run: uvicorn app.main:app --reload
# Run for web testing: python3 -m http.server 3000