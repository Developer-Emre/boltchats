from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "boltchats-api"
    app_version: str = "1.0.0"
    environment: str = "development"

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "boltchats"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    secret_key: str = "change-me-to-a-strong-random-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Google OAuth
    google_client_id: str = ""

    # Rate limiting
    # Set to high values for development; production should override via env vars
    rate_limit_requests: int = 1000
    rate_limit_window_seconds: int = 60


settings = Settings()
