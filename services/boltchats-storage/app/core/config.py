from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "boltchats-storage"
    app_version: str = "1.0.0"
    environment: str = "development"

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "boltchats"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_queue_name: str = "messages:queue"

    # Consumer retry
    consumer_max_retries: int = 3
    consumer_retry_base_delay: float = 1.0


settings = Settings()
