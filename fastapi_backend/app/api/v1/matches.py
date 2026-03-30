import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import tables
from app.db.database import get_db
from app.core.auth_utils import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/matches", tags=["Matches"])

class MatchCreate(BaseModel):
    title: str
    sport: str
    duration: float
    date_event: str
    time: str
    location: str
    roster_size: int
    cost: float

@router.get("/")
async def get_matches(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    user_id = current_user["id"]
    all_matches = db.query(tables.Match).all()
    user_matches = []

    for m in all_matches:
        is_host = (m.host_id == user_id)
        is_joined = any(
            p.user_id == user_id and p.status == "confirmed"
            for p in m.players
        )
        is_participant = any(p.user_id == user_id for p in m.players)

        if is_host or is_participant:
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

@router.post("/create")
async def create_match(match: MatchCreate, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    match_id = f"m_{uuid.uuid4().hex[:8]}"
    new_match = tables.Match(
        id=match_id,
        title=match.title,
        sport=match.sport,
        duration=match.duration,
        date_event=match.date_event,
        time=match.time,
        location=match.location,
        roster_size=match.roster_size,
        cost=match.cost,
        host_id=user["id"]
    )
    db.add(new_match)
    db.commit()
    return {"status": "success", "id": new_match.id}

@router.get("/{match_id}")
async def get_match_details(
        match_id: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    match = db.query(tables.Match).filter(tables.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # 1. Filter the list for the UI (only show confirmed players)
    # 2. Determine if the current viewer is one of those confirmed players
    active_players = []
    is_joined = False

    for p in match.players:
        if p.status == "confirmed":
            user_record = db.query(tables.User).filter(tables.User.id == p.user_id).first()
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
        "is_host": (match.host_id == current_user["id"]),
        "current_roster": len(active_players),
        "player_list": active_players,
        "is_cancelled": match.is_cancelled,
        "is_joined": is_joined
    }

@router.post("/{match_id}/toggle-join")
async def toggle_join(match_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = user["id"]

    # Check if user is already in the match
    existing_entry = db.query(tables.MatchPlayer).filter(
        tables.MatchPlayer.match_id == match_id,
        tables.MatchPlayer.user_id == user_id
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
        match = db.query(tables.Match).filter(tables.Match.id == match_id).first()
        if len(match.players) >= match.roster_size:
            raise HTTPException(status_code=400, detail="Match is full")

        new_player = tables.MatchPlayer(match_id=match_id, user_id=user_id)
        db.add(new_player)
        action = "confirmed"

    db.commit()
    return {"status": "success", "action": action}

@router.post("/{match_id}/toggle-cancel")
async def toggle_cancel(match_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    match = db.query(tables.Match).filter(tables.Match.id == match_id).first()

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    if match.host_id != user["id"]:
        raise HTTPException(status_code=403, detail="Only the host can cancel this match")

    # The Python way to invert a boolean
    match.is_cancelled = not match.is_cancelled
    db.commit()
    status_text = "cancelled" if match.is_cancelled else "restored"
    return {"status": "success", "message": f"Match {status_text}"}