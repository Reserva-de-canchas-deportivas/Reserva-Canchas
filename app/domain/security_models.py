from __future__ import annotations

from datetime import datetime, timedelta
import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.domain.user_model import Base


class ApiKey(Base):
    """API Keys para integraciones externas."""

    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    integration_name = Column(String(120), nullable=False, index=True)
    key_hash = Column(String(128), unique=True, nullable=False)
    prefix = Column(String(12), nullable=False, index=True)
    last_four = Column(String(4), nullable=False)
    description = Column(String(255), nullable=True)
    expires_at = Column(
        DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(days=90)
    )
    usage_limit = Column(Integer, nullable=True)  # Null == ilimitado
    usage_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    def is_valid(self) -> bool:
        if not self.is_active:
            return False
        if self.expires_at <= datetime.utcnow():
            return False
        if self.usage_limit is not None and self.usage_count >= self.usage_limit:
            return False
        return True


class SecurityAuditLog(Base):
    """Registro de auditoría para accesos/autenticaciones."""

    __tablename__ = "security_audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(
        String(50), nullable=False
    )  # e.g. TOKEN_OK, TOKEN_EXPIRED, API_KEY_INVALID
    status = Column(String(20), nullable=False)  # SUCCESS / FAILURE
    message = Column(String(255), nullable=False)
    user_id = Column(String(36), nullable=True, index=True)
    role = Column(String(50), nullable=True)
    integration_name = Column(String(120), nullable=True)
    api_key_prefix = Column(String(12), nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
