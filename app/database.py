"""
Compat wrapper for database utilities.

This keeps existing imports (`from app.database import get_db`) working while
centralising the actual engine/session configuration in `app.utils.database`.
"""

from app.utils.database import engine, SessionLocal, get_db, init_db  # noqa: F401
from app.domain.user_model import Base  # noqa: F401

# Import models to register them in SQLAlchemy metadata
from app.models.sede import Sede  # noqa: F401
from app.models.cancha import Cancha  # noqa: F401
from app.models.tarifario import Tarifario  # noqa: F401
from app.models.reserva import Reserva  # noqa: F401
from app.domain.security_models import ApiKey, SecurityAuditLog  # noqa: F401
from app.domain.profile_model import PerfilUsuario  # noqa: F401
from app.models.pago import Pago  # noqa: F401
from app.models.factura import Factura  # noqa: F401
