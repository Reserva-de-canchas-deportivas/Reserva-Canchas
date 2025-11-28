from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.domain.user_model import Base  # noqa: F401
from app.models.sede import Sede  # noqa: F401
from app.models.cancha import Cancha  # noqa: F401
from app.models.tarifario import Tarifario  # noqa: F401
from app.models.reserva import Reserva  # noqa: F401
from app.domain.security_models import ApiKey, SecurityAuditLog  # noqa: F401
from app.domain.profile_model import PerfilUsuario  # noqa: F401
from app.models.pago import Pago  # noqa: F401
from app.models.factura import Factura  # noqa: F401

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

