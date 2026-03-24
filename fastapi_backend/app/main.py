from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.api import login, register
from app.api.match_create import MatchCreate
from app.core.config import SECRET_CHALLENGE_KEY
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.core.auth_utils import JWT_SECRET_KEY, JWT_ALGORITHM
from jose import jwt, JWTError
import uuid
from app.db.mock_db import get_db, save_db

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
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. Decode the token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("id")  # <-- ADD THIS: Extract the UUID from the token

        if username is None or user_id is None:
            raise credentials_exception

        # 2. Return BOTH so the rest of the API can use them
        return {"username": username, "id": user_id}
    except JWTError:
        raise credentials_exception


@app.get("/api/dashboard/matches")
async def get_matches(current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = current_user.get("id")  # Now this will actually have a value!

    all_matches = db.get("matches", {})
    match_players = db.get("match_players", [])
    user_matches = []

    for match_id, match_data in all_matches.items():
        # Check if user is host or player
        is_host = (match_data.get("host_id") == user_id)
        is_joined = any(p["match_id"] == match_id and p["user_id"] == user_id for p in match_players)

        if is_host or is_joined:
            match_summary = match_data.copy()
            match_summary["id"] = match_id
            match_summary["is_host"] = is_host
            match_summary["is_joined"] = is_joined
            match_summary["joined"] = sum(1 for p in match_players if p["match_id"] == match_id)
            match_summary["max"] = match_data.get("roster_size", 14)
            user_matches.append(match_summary)

    return user_matches[::-1]


@app.post("/api/matches")
async def create_match(match: MatchCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = current_user['id']

    # Generate a unique ID for the match
    match_id = f"m_{uuid.uuid4().hex[:8]}"

    # 1. Save the core match rules
    new_match = {
        "id": match_id,
        "sport": match.sport,
        "duration": match.duration,
        "title": match.title,
        "date": match.date,
        "time": match.time,
        "location": match.location,
        "roster_size": match.roster_size,
        "cost": match.cost,
        "host_id": user_id,
        "status": "Ready"
    }
    db["matches"][match_id] = new_match
    save_db(db)

    return {
        "status": "success",
        "match_id": match_id
    }


@app.get("/api/matches/{match_id}")
async def get_match_details(match_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()

    # 1. Access the match correctly
    match = db.get("matches", {}).get(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # 2. Extract player usernames from the list of objects
    # We map user_ids to usernames using the 'users' table
    all_users = db.get("users", {})
    match_player_entries = [p for p in db.get("match_players", []) if p["match_id"] == match_id]

    # Create a list of usernames currently in the match
    player_list = []
    for entry in match_player_entries:
        user_data = all_users.get(entry["user_id"])
        if user_data:
            player_list.append(user_data["username"])

    current_user_id = current_user.get("id")
    host_username = all_users.get(match.get("host_id"), {}).get("username", "Unknown Organizer")

    return {
        "id": match_id,
        "title": match.get("title", "Untitled"),
        "date": match.get("date"),
        "time": match.get("time"),
        "location": match.get("location"),
        "cost": match.get("cost", 0),
        "roster_size": match.get("roster_size", 14),
        "duration": match.get("duration", 1.0),
        "host_username": host_username,
        "is_host": (match.get("host_id") == current_user_id),
        "is_joined": any(p["user_id"] == current_user_id for p in match_player_entries),
        "current_roster": len(player_list),
        "player_list": player_list
    }


@app.post("/api/matches/{match_id}/toggle-join")
async def toggle_join(match_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = current_user["id"] # Guaranteed by the JWT
    match_players = db.get("match_players", [])

    existing_entry = next((p for p in match_players if p["match_id"] == match_id and p["user_id"] == user_id), None)

    if existing_entry:
        match_players.remove(existing_entry)
        action = "left"
    else:
        match_players.append({
            "match_id": match_id,
            "user_id": user_id,
            "role": "player",
            "status": "confirmed"
        })
        action = "joined"

    db["match_players"] = match_players
    save_db(db)
    return {"status": "success", "action": action}


@app.delete("/api/matches/{match_id}")
async def cancel_match(match_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    match = db["matches"].get(match_id)

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Compare UUID to UUID
    if match["host_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only the host can cancel this match")

    del db["matches"][match_id]

    # Also clean up the player list for this match
    db["match_players"] = [p for p in db["match_players"] if p["match_id"] != match_id]

    save_db(db)
    return {"status": "success", "message": "Match cancelled"}

# To run: uvicorn app.main:app --reload
# Run for web testing: python3 -m http.server 3000