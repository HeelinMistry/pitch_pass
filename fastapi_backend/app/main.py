from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.api import login, register
from app.core.config import SECRET_CHALLENGE_KEY

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

# To run: uvicorn app.main:app --reload
# Run for web testing: python3 -m http.server 3000