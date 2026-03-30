"""
SQLAlchemy table definitions.

This module contains the SQLAlchemy model definitions for the application's
database tables, including users, passkeys, matches, and match players.
"""

import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    """
    Represents a user in the system.

    Attributes:
        id (str): Unique identifier for the user.
        username (str): The user's unique username.
        passkeys (relationship): Relationship to the user's registered passkeys.
        matches_hosted (relationship): Relationship to the matches hosted by the user.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)

    # Relationships
    passkeys = relationship("Passkey", back_populates="owner")
    matches_hosted = relationship("Match", back_populates="host")

class Passkey(Base):
    """
    Represents a WebAuthn passkey associated with a user.

    Attributes:
        id (str): The credential ID for the passkey.
        user_id (str): Foreign key to the user who owns the passkey.
        public_key (str): The public key used for authentication.
        sign_count (int): The current sign count for the passkey.
        owner (relationship): Relationship to the user who owns the passkey.
    """
    __tablename__ = "passkeys"

    id = Column(String, primary_key=True, index=True) # The Credential ID
    user_id = Column(String, ForeignKey("users.id"))
    public_key = Column(String)
    sign_count = Column(Integer, default=0)

    owner = relationship("User", back_populates="passkeys")

class Match(Base):
    """
    Represents a sports match hosted by a user.

    Attributes:
        id (str): Unique identifier for the match.
        title (str): The title of the match.
        sport (str): The sport being played.
        duration (str): The duration of the match.
        date_event (str): The date of the match.
        date_modified (datetime): The last time the match was modified.
        time (str): The time of the match.
        location (str): The location of the match.
        roster_size (int): The maximum number of players for the match.
        cost (str): The cost to participate in the match.
        host_id (str): Foreign key to the user who is hosting the match.
        is_cancelled (bool): Whether the match has been cancelled.
        host (relationship): Relationship to the user hosting the match.
        players (relationship): Relationship to the players participating in the match.
    """
    __tablename__ = "matches"

    id = Column(String, primary_key=True, index=True, default=f"m_{uuid.uuid4().hex[:8]}")
    title = Column(String)
    sport = Column(String)
    duration = Column(String)
    date_event = Column(String)
    date_modified = Column(DateTime, server_default=func.now(), onupdate=func.now())
    time = Column(String)
    location = Column(String)
    roster_size = Column(Integer, default=0)
    cost = Column(String)
    host_id = Column(String, ForeignKey("users.id"))
    is_cancelled = Column(Boolean, default=False)

    host = relationship("User", back_populates="matches_hosted")
    players = relationship("MatchPlayer", back_populates="match", cascade="all, delete-orphan")

class MatchPlayer(Base):
    """
    Represents a player participating in a match.

    Attributes:
        id (int): Unique identifier for the match player entry.
        match_id (str): Foreign key to the match.
        user_id (str): Foreign key to the user.
        status (str): The status of the player (e.g., 'confirmed', 'pending').
        date_modified (datetime): The last time the entry was modified.
        match (relationship): Relationship to the match.
    """
    __tablename__ = "match_players"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    match_id = Column(String, ForeignKey("matches.id"))
    user_id = Column(String, ForeignKey("users.id"))
    status = Column(String, default="confirmed")
    date_modified = Column(DateTime, server_default=func.now(), onupdate=func.now())

    match = relationship("Match", back_populates="players")
