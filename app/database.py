from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.domain.user_model import Base  # type: ignore

# In-memory SQLite shared across threads for temporary data
DATABASE_URL = "sqlite://"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(create_all: bool = True):
    if create_all:
        Base.metadata.create_all(bind=engine)
