from sqlalchemy.orm import Session
from app.db import models

def get_user_by_username(db: Session, username: str):
    # This replaces the 'for loop' through the JSON dictionary
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_id(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user_id: str, username: str):
    db_user = models.User(id=user_id, username=username)
    db.add(db_user)
    db.commit() # This replaces save_db()
    db.refresh(db_user)
    return db_user