from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.security_models import ApiKey
from app.services.api_key_service import (
    ApiKeySeed,
    DEFAULT_API_KEY_SEEDS,
    get_last_four,
    get_prefix,
    hash_api_key,
)


def get_by_prefix(db: Session, prefix: str) -> Optional[ApiKey]:
    return db.query(ApiKey).filter(ApiKey.prefix == prefix).first()


def get_by_hash(db: Session, key_hash: str) -> Optional[ApiKey]:
    return db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()


def increment_usage(db: Session, api_key: ApiKey) -> None:
    api_key.usage_count += 1
    api_key.last_used_at = datetime.utcnow()
    db.add(api_key)
    db.commit()


def seed_api_keys(
    db: Session, seeds: tuple[ApiKeySeed, ...] = DEFAULT_API_KEY_SEEDS
) -> None:
    """Crea API Keys por defecto si la tabla está vacía."""
    if db.query(ApiKey).count() > 0:
        return

    for seed in seeds:
        raw = seed.raw_key
        api_key = ApiKey(
            integration_name=seed.integration_name,
            key_hash=hash_api_key(raw),
            prefix=get_prefix(raw),
            last_four=get_last_four(raw),
            description=seed.description,
            expires_at=datetime.utcnow() + timedelta(days=90),
            usage_limit=seed.usage_limit,
        )
        db.add(api_key)
    db.commit()
