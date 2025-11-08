from datetime import datetime, timedelta, timezone
import uuid
from typing import Any, Dict, Tuple

from jose import jwt, JWTError, ExpiredSignatureError

from app.config.settings import settings

try:
    # Optional, only if we must generate keys on the fly
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
except Exception:  # pragma: no cover
    rsa = None  # type: ignore
    serialization = None  # type: ignore


class KeyProvider:
    _private_pem: str | None = None
    _public_pem: str | None = None

    @classmethod
    def load_keys(cls) -> Tuple[str, str]:
        if cls._private_pem and cls._public_pem:
            return cls._private_pem, cls._public_pem

        # 1) Env vars direct PEM
        if settings.private_key and settings.public_key:
            cls._private_pem = settings.private_key
            cls._public_pem = settings.public_key
            return cls._private_pem, cls._public_pem

        # 2) Files by path if provided
        if settings.private_key_path and settings.public_key_path:
            with open(settings.private_key_path, "r", encoding="utf-8") as f:
                cls._private_pem = f.read()
            with open(settings.public_key_path, "r", encoding="utf-8") as f:
                cls._public_pem = f.read()
            return cls._private_pem, cls._public_pem

        # 3) Try default keys path in repo
        try:
            with open("keys/private.pem", "r", encoding="utf-8") as f:
                cls._private_pem = f.read()
            with open("keys/public.pem", "r", encoding="utf-8") as f:
                cls._public_pem = f.read()
            return cls._private_pem, cls._public_pem
        except FileNotFoundError:
            pass

        # 4) Generate ephemeral key pair (dev fallback)
        if rsa is None:
            raise RuntimeError("RSA keypair unavailable; provide PRIVATE_KEY/PUBLIC_KEY or key files.")

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
        public_pem = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
        cls._private_pem, cls._public_pem = private_pem, public_pem
        return cls._private_pem, cls._public_pem


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_token(subject: str, token_type: str, extra_claims: Dict[str, Any] | None = None) -> Tuple[str, int]:
    assert token_type in {"access", "refresh"}
    private_key, _ = KeyProvider.load_keys()
    exp_seconds = settings.access_token_expire_seconds if token_type == "access" else settings.refresh_token_expire_seconds
    jti = str(uuid.uuid4())
    expire_at = _now() + timedelta(seconds=exp_seconds)

    payload: Dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": int(_now().timestamp()),
        "exp": int(expire_at.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, private_key, algorithm=settings.jwt_algorithm)
    return token, exp_seconds


def decode_token(token: str) -> Dict[str, Any]:
    _, public_key = KeyProvider.load_keys()
    try:
        return jwt.decode(token, public_key, algorithms=[settings.jwt_algorithm])
    except ExpiredSignatureError as e:
        raise e
    except JWTError as e:  # includes invalid signature, malformed
        raise e

