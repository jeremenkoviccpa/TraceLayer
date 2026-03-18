import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(
    user_id: str,
    company_id: str,
    extra_claims: dict | None = None,
    expire_minutes: int | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expire_minutes if expire_minutes is not None else settings.jwt_access_token_expire_minutes
    )
    payload: dict = {
        "sub": user_id,
        "company_id": company_id,
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])


def create_refresh_token() -> tuple[str, str]:
    """Returns (raw_token, token_hash)."""
    raw = secrets.token_urlsafe(64)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def encrypt_value(value: str) -> str:
    from cryptography.fernet import Fernet
    key = settings.fernet_key
    if isinstance(key, str):
        key = key.encode()
    f = Fernet(key)
    return f.encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    from cryptography.fernet import Fernet
    key = settings.fernet_key
    if isinstance(key, str):
        key = key.encode()
    f = Fernet(key)
    return f.decrypt(encrypted.encode()).decode()
