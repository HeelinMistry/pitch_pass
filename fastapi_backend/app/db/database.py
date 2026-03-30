"""
Database configuration and session management.

This module sets up the SQLAlchemy engine, session factory, and base class
for the application's database models. It also provides a dependency
for FastAPI routes to obtain a database session.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

# This creates a file named pitchpass.db in your root folder
SQLALCHEMY_DATABASE_URL = "sqlite:///./pitchpass.db"

# check_same_thread=False is required for FastAPI when using SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Session factory for creating new database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative database models
Base = declarative_base()

def get_db() -> Generator:
    """
    Dependency that provides a database session for a single request.

    Yields:
        Session: A SQLAlchemy database session.

    Ensures that the session is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
