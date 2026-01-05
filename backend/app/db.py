import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database URL is configurable via env; falls back to local Postgres defaults.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://hurricane:hurricane@localhost:5432/hurricane_triage",
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
