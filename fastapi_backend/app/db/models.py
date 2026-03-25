from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)

    # Relationships (Optional but highly recommended for easy querying)
    passkeys = relationship("Passkey", back_populates="owner")
    matches_hosted = relationship("Match", back_populates="host")

class Passkey(Base):
    __tablename__ = "passkeys"

    id = Column(String, primary_key=True, index=True) # The Credential ID
    user_id = Column(String, ForeignKey("users.id"))
    public_key = Column(String)
    sign_count = Column(Integer, default=0)

    owner = relationship("User", back_populates="passkeys")

class Match(Base):
    __tablename__ = "matches"

    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    sport = Column(String)
    duration = Column(String)
    date = Column(String)
    time = Column(String)
    location = Column(String)
    roster_size = Column(Integer, default=0)
    cost = Column(String)
    host_id = Column(String, ForeignKey("users.id"))
    is_cancelled = Column(Boolean, default=False)

    host = relationship("User", back_populates="matches_hosted")
    players = relationship("MatchPlayer", back_populates="match", cascade="all, delete-orphan")

class MatchPlayer(Base):
    __tablename__ = "match_players"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    match_id = Column(String, ForeignKey("matches.id"))
    user_id = Column(String, ForeignKey("users.id"))
    status = Column(String, default="confirmed")
    joined_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    match = relationship("Match", back_populates="players")