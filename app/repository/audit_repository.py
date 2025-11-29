from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.security_models import SecurityAuditLog


def log_event(
    db: Session,
    *,
    event_type: str,
    status: str,
    message: str,
    user_id: str | None = None,
    role: str | None = None,
    integration_name: str | None = None,
    api_key_prefix: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: str | None = None,
) -> SecurityAuditLog:
    entry = SecurityAuditLog(
        event_type=event_type,
        status=status,
        message=message,
        user_id=user_id,
        role=role,
        integration_name=integration_name,
        api_key_prefix=api_key_prefix,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
