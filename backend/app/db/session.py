"""Create the shared SQLAlchemy database connection and request sessions.

API routes receive a short-lived session from get_db(), while models share the
Base class so startup can create their tables.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# pool_pre_ping checks a reused connection before a query, which helps after database restarts.
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    # FastAPI opens one session for the request and always closes it afterward.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
