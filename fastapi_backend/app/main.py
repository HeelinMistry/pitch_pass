from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, matches
from app.db.database import engine, Base
from app.core.config import SECRET_CHALLENGE_KEY

# Initialize DB
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PitchPass Pro")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_CHALLENGE_KEY,
    same_site="lax",
    https_only=False # Set to True if using SSL
)

# Routes
app.include_router(auth.router, prefix="/api")
app.include_router(matches.router, prefix="/api")

# Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def health_check():
    return {"status": "online", "system": "PitchPass Kinetic"}