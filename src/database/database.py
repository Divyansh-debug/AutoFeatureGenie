import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config.settings import settings

# Ensure data directory exists (handle single-segment paths like "data")
_upload_parent = os.path.dirname(settings.UPLOAD_DIR)
if _upload_parent:
    os.makedirs(_upload_parent, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Default to SQLite file inside the data directory
DATABASE_URL = "sqlite:///./data/autofeaturegenie.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
