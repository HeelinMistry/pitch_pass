"""
CRUD (Create, Read, Update, Delete) operations for the application.

This module contains utility functions for interacting with the database
using SQLAlchemy.
"""

from sqlalchemy.orm import Session
from app.db import tables
from typing import Optional

def get_user_by_username(db: Session, username: str) -> Optional[tables.User]:
    """
    Retrieve a user from the database by their username.

    Args:
        db (Session): The SQLAlchemy database session.
        username (str): The username of the user to retrieve.

    Returns:
        Optional[tables.User]: The user if found, otherwise None.
    """
    return db.query(tables.User).filter(tables.User.username == username).first()

def get_user_by_id(db: Session, user_id: str) -> Optional[tables.User]:
    """
    Retrieve a user from the database by their ID.

    Args:
        db (Session): The SQLAlchemy database session.
        user_id (str): The ID of the user to retrieve.

    Returns:
        Optional[tables.User]: The user if found, otherwise None.
    """
    return db.query(tables.User).filter(tables.User.id == user_id).first()

def create_user(db: Session, user_id: str, username: str) -> tables.User:
    """
    Create a new user in the database.

    Args:
        db (Session): The SQLAlchemy database session.
        user_id (str): The ID for the new user.
        username (str): The username for the new user.

    Returns:
        tables.User: The newly created user.
    """
    db_user = tables.User(id=user_id, username=username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
