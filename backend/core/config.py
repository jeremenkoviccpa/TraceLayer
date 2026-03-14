from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str
    database_url: str
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    fernet_key: str
    storage_bucket: str = ""
    storage_endpoint: str = ""
    storage_access_key: str = ""
    storage_secret_key: str = ""
    cors_origins: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
