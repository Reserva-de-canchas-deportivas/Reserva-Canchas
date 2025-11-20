from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from app.repository import audit_repository


def record_security_event(
    db: Session,
    *,
    event_type: str,
    status: str,
    message: str,
    user_id: str | None = None,
    role: str | None = None,
    integration_name: str | None = None,
    api_key_prefix: str | None = None,
    request: Request | None = None,
    details: str | None = None,
):
    """Helper para registrar auditoría extrayendo IP y User-Agent del request."""
    ip_address = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None
    return audit_repository.log_event(
        db,
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
