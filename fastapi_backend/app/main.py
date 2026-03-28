import uuid
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer

from app.api import login, register
from app.api.match_create import MatchCreate
from app.core.config import SECRET_CHALLENGE_KEY, JWT_SECRET_KEY, JWT_ALGORITHM
from app.db.database import engine, Base, get_db
from app.db import models

from fastapi.staticfiles import StaticFiles

# Initialize Database Tables on startup
Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="PitchPass Pro API")

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_CHALLENGE_KEY,
    session_cookie="pitchpass_session",
    # 'lax' allows the cookie to be sent on cross-site requests (like port 3000 -> 8000)
    same_site="lax",
    # Must be False because we are using http:// and not https://
    https_only=False
)

# Add static web
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Authentication Routers
app.include_router(login.router, prefix="/api")
app.include_router(register.router, prefix="/api")


# --- Authentication Dependency ---
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")  # In refactored login, 'sub' is the UUID
        username: str = payload.get("username")

        if user_id is None:
            raise credentials_exception
        return {"id": user_id, "username": username}
    except JWTError:
        raise credentials_exception


# --- Match Routes ---

@app.get("/api/dashboard/matches")
async def get_matches(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    user_id = current_user["id"]
    all_matches = db.query(models.Match).all()
    user_matches = []

    for m in all_matches:
        # 1. Check if the current user is the host
        is_host = (m.host_id == user_id)

        # 2. Check if the current user is a "confirmed" player
        # Logic: Look for a record in match_players that matches user_id AND status
        is_joined = any(
            p.user_id == user_id and p.status == "confirmed"
            for p in m.players
        )

        # 3. Build the player list for the frontend
        # Filter only confirmed players to show in the UI roster
        confirmed_player_names = []
        for p in m.players:
            if p.status == "confirmed":
                # Optimization: If you have a 'user' relationship on MatchPlayer,
                # use p.user.username instead of a manual db.query
                user_record = db.query(models.User).filter(models.User.id == p.user_id).first()
                confirmed_player_names.append(user_record.username if user_record else "Unknown")

        if is_host or any(
            p.user_id == user_id
            for p in m.players
        ):
            user_matches.append({
                "id": m.id,
                "title": m.title,
                "date": m.date_event,
                "time": m.time,
                "location": m.location,
                "cost": m.cost,
                "is_host": is_host,
                "is_cancelled": m.is_cancelled,
                "is_joined": is_joined,
                "joined": len(m.players),
                "roster_size": m.roster_size
            })

    return user_matches[::-1]


@app.post("/api/matches")
async def create_match(
        match: MatchCreate,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    match_id = f"m_{uuid.uuid4().hex[:8]}"

    new_match = models.Match(
        id=match_id,
        title=match.title,
        sport=match.sport,
        duration=match.duration,
        date_event=match.date_event,
        time=match.time,
        location=match.location,
        roster_size=match.roster_size,
        cost=match.cost,
        host_id=current_user["id"]
    )
    db.add(new_match)

    db.commit()
    return {"status": "success", "match_id": match_id}


@app.get("/api/matches/{match_id}")
async def get_match_details(
        match_id: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # 1. Filter the list for the UI (only show confirmed players)
    # 2. Determine if the current viewer is one of those confirmed players
    active_players = []
    is_joined = False

    for p in match.players:
        if p.status == "confirmed":
            user_record = db.query(models.User).filter(models.User.id == p.user_id).first()
            username = user_record.username if user_record else "Unknown"
            active_players.append(username)

            # Check if this confirmed player is the person currently logged in
            if p.user_id == current_user["id"]:
                is_joined = True

    return {
        "id": match.id,
        "title": match.title,
        "date": match.date_event,
        "time": match.time,
        "location": match.location,
        "cost": match.cost,
        "roster_size": match.roster_size,
        "duration": match.duration,
        "host_username": match.host.username,
        "is_host": (match.host_id == current_user["id"]),
        "current_roster": len(active_players),
        "player_list": active_players,
        "is_cancelled": match.is_cancelled,
        "is_joined": is_joined
    }


@app.post("/api/matches/{match_id}/toggle-join")
async def toggle_join(
        match_id: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    user_id = current_user["id"]

    # Check if user is already in the match
    existing_entry = db.query(models.MatchPlayer).filter(
        models.MatchPlayer.match_id == match_id,
        models.MatchPlayer.user_id == user_id
    ).first()

    if existing_entry:
        if existing_entry.status == "confirmed":
            # Soft leave: keep the record, change the status
            existing_entry.status = "left"
            action = "left"
        else:
            # Re-joining
            existing_entry.status = "confirmed"
            action = "confirmed"
    else:
        # Check roster limit
        match = db.query(models.Match).filter(models.Match.id == match_id).first()
        if len(match.players) >= match.roster_size:
            raise HTTPException(status_code=400, detail="Match is full")

        new_player = models.MatchPlayer(match_id=match_id, user_id=user_id)
        db.add(new_player)
        action = "confirmed"

    db.commit()
    return {"status": "success", "action": action}


@app.post("/api/matches/{match_id}/toggle-cancel")
async def toggle_cancel_match(
        match_id: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    match = db.query(models.Match).filter(models.Match.id == match_id).first()

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    if match.host_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only the host can cancel this match")

    # The Python way to invert a boolean
    match.is_cancelled = not match.is_cancelled

    db.commit()

    status_text = "cancelled" if match.is_cancelled else "restored"
    return {"status": "success", "message": f"Match {status_text}"}


# Server: uvicorn app.main:app --reload
# Docs: localhost:8000/docs
# Web: python3 -m http.server 3000
# Web: localhost:3000/static/login.html