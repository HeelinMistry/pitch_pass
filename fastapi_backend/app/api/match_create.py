from pydantic import BaseModel
from typing import List, Optional

class MatchCreate(BaseModel):
    title: str
    sport: str
    duration: float
    date: str
    time: str
    location: str
    roster_size: int
    cost: float

class MatchResponse(BaseModel):
    id: str
    title: str
    date: str
    time: str
    location: str
    cost: float
    roster_size: int
    duration: float
    host_username: str
    is_host: bool
    is_joined: bool
    current_roster: int
    player_list: List[str]

    class Config:
        from_attributes = True