from __future__ import annotations

from datetime import datetime

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.security_models import ApiKey
from app.repository import api_key_repository
from app.services.api_key_service import get_prefix, hash_api_key
from app.services.audit_service import record_security_event
from app.services.security_responses import invalid_api_key_error


async def require_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
    db: Session = Depends(get_db),
) -> ApiKey:
    if not x_api_key:
        record_security_event(
            db,
            event_type="API_KEY_MISSING",
            status="FAILURE",
            message="Cabecera X-Api-Key ausente",
            request=request,
        )
        raise invalid_api_key_error("X-Api-Key requerida")

    prefix = get_prefix(x_api_key)
    hashed = hash_api_key(x_api_key)
    api_key = api_key_repository.get_by_prefix(db, prefix)

    if not api_key or api_key.key_hash != hashed:
        record_security_event(
            db,
            event_type="API_KEY_INVALID",
            status="FAILURE",
            message="API Key inexistente o inválida",
            api_key_prefix=prefix,
            request=request,
        )
        raise invalid_api_key_error("API Key inválida")

    now = datetime.utcnow()
    if not api_key.is_active:
        code = "API_KEY_INACTIVE"
        record_security_event(
            db,
            event_type=code,
            status="FAILURE",
            message="API Key deshabilitada",
            api_key_prefix=api_key.prefix,
            integration_name=api_key.integration_name,
            request=request,
        )
        raise invalid_api_key_error("API Key inválida", code=code)
    if api_key.expires_at <= now:
        record_security_event(
            db,
            event_type="API_KEY_EXPIRED",
            status="FAILURE",
            message="API Key expirada",
            api_key_prefix=api_key.prefix,
            integration_name=api_key.integration_name,
            request=request,
        )
        raise invalid_api_key_error("API Key expirada", code="API_KEY_EXPIRED")
    if api_key.usage_limit is not None and api_key.usage_count >= api_key.usage_limit:
        record_security_event(
            db,
            event_type="API_KEY_QUOTA",
            status="FAILURE",
            message="Límite de uso alcanzado",
            api_key_prefix=api_key.prefix,
            integration_name=api_key.integration_name,
            request=request,
        )
        raise invalid_api_key_error(
            "Límite de solicitudes consumido", code="API_KEY_QUOTA"
        )

    api_key_repository.increment_usage(db, api_key)
    record_security_event(
        db,
        event_type="API_KEY_OK",
        status="SUCCESS",
        message="API Key validada",
        api_key_prefix=api_key.prefix,
        integration_name=api_key.integration_name,
        request=request,
    )
    return api_key
