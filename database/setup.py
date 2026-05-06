"""Database engine and session factory for local SQLite persistence."""

from dotenv import load_dotenv

load_dotenv()

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

db_path = Path(__file__).parent / 'history.db'
DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Create database tables when they do not already exist."""
    Base.metadata.create_all(bind=engine)

init_db()
