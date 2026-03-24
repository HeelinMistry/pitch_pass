from pydantic import BaseModel

class MatchCreate(BaseModel):
    title: str
    sport: str
    duration: float
    date: str
    time: str
    location: str
    roster_size: int
    cost: float
