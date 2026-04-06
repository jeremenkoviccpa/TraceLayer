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
    cors_origins: str = "http://localhost:3000,https://tracelayer.it.com"
    app_frontend_url: str = "http://localhost:3000"
    resend_api_key: str = ""
    email_from: str = "TraceLayer <hello@tracelayer.it.com>"
    seed_demo: bool = False
    anthropic_api_key: str = ""
    # Paddle billing
    paddle_sk: str = ""           # was PADDLE_API_KEY — renamed to PADDLE_SK to avoid Railway caching bug
    paddle_growth_price_id: str = ""        # pri_xxxx  (Growth monthly subscription)
    paddle_webhook_secret: str = ""         # pdl_ntfset_xxxx
    paddle_partner_client_price_id: str = ""  # pri_xxxx  ($99 one-time partner client slot)
    paddle_sandbox: bool = False            # set True during testing
    # Google OAuth (for login)
    google_client_id: str = ""
    google_client_secret: str = ""
    backend_url: str = "http://localhost:8000"
    # Integration OAuth
    github_oauth_client_id: str = ""
    github_oauth_client_secret: str = ""
    slack_oauth_client_id: str = ""
    slack_oauth_client_secret: str = ""
    linear_oauth_client_id: str = ""
    linear_oauth_client_secret: str = ""
    notion_oauth_client_id: str = ""
    notion_oauth_client_secret: str = ""
    # Observability
    sentry_dsn: str = ""
    # Internal accounts that bypass billing checks (comma-separated emails in env)
    # Field name matches env var INTERNAL_ADMINS via pydantic-settings case-insensitive mapping
    internal_admins: str = ""

    @property
    def internal_admins_list(self) -> list[str]:
        return [e.strip() for e in self.internal_admins.split(",") if e.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        # Handle JSON array format e.g. '["https://foo.com","https://bar.com"]'
        if raw.startswith("["):
            import json
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
        # Handle comma-separated format
        return [o.strip() for o in raw.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_prefix = ""


settings = Settings()
