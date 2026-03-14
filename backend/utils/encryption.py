import json

from cryptography.fernet import Fernet

from core.config import settings

_fernet = Fernet(settings.fernet_key.encode())


def encrypt_credentials(credentials: dict) -> str:
    return _fernet.encrypt(json.dumps(credentials).encode()).decode()


def decrypt_credentials(encrypted: str) -> dict:
    return json.loads(_fernet.decrypt(encrypted.encode()).decode())
