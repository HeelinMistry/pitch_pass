from pydantic import BaseModel
from typing import List, Optional

class MatchCreate(BaseModel):
    title: str
    sport: str
    duration: float
    date_event: str
    time: str
    location: str
    roster_size: int
    cost: float
