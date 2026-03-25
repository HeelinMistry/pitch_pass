from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# This creates a file named pitchpass.db in your root folder
SQLALCHEMY_DATABASE_URL = "sqlite:///./pitchpass.db"

# check_same_thread=False is required for FastAPI when using SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# This is the new dependency you will inject into your routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()