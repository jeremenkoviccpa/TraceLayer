from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str
    database_url: str
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    fernet_key: str
    supabase_url: str = ""
    supabase_service_key: str = ""
    storage_bucket: str = ""
    storage_endpoint: str = ""
    storage_access_key: str = ""
    storage_secret_key: str = ""
    cors_origins: List[str] = ["http://localhost:3000"]
    app_frontend_url: str = "http://localhost:3000"
    resend_api_key: str = ""
    email_from: str = "TraceLayer <hello@tracelayer.it.com>"
    seed_demo: bool = False
    groq_api_key: str = ""
    # LemonSqueezy billing
    ls_api_key: str = ""
    app_ls_store_id: str = ""
    ls_growth_variant_id: str = ""
    ls_webhook_secret: str = ""
    ls_partner_client_variant_id: str = ""
    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    backend_url: str = "http://localhost:8000"
    # Observability
    sentry_dsn: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
