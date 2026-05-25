from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "boltchats-ws"
    app_version: str = "1.0.0"
    environment: str = "development"

    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me"
    algorithm: str = "HS256"

    rate_limit_connections_per_user: int = 5
    rate_limit_messages_per_second: int = 10


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
