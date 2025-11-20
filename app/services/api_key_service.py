from __future__ import annotations

import hashlib
from dataclasses import dataclass


def hash_api_key(raw_key: str) -> str:
    """Devuelve hash SHA-256 de la API Key."""
    clean = raw_key.strip()
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()


def get_prefix(raw_key: str, length: int = 8) -> str:
    clean = raw_key.strip().replace(" ", "")
    return clean[:length]


def get_last_four(raw_key: str) -> str:
    clean = raw_key.strip().replace(" ", "")
    return clean[-4:] if len(clean) >= 4 else clean


@dataclass(frozen=True)
class ApiKeySeed:
    integration_name: str
    raw_key: str
    description: str
    usage_limit: int | None = None


DEFAULT_API_KEY_SEEDS: tuple[ApiKeySeed, ...] = (
    ApiKeySeed(
        integration_name="integracion_demo",
        raw_key="DEMO-INTEGRACION-2024-KEY",
        description="Llave de pruebas para integraciones externas",
        usage_limit=None,
    ),
)
