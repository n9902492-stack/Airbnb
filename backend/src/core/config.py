from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Nestora API"
    app_env: str = "development"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nestora"
    frontend_url: str = "http://localhost:5173"

    secret_key: str = "change-this-in-your-local-env"
    access_token_expire_minutes: int = 60

    otp_expire_minutes: int = 10
    otp_max_attempts: int = 5

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "no-reply@nestora.local"
    smtp_use_tls: bool = True

    mapbox_access_token: str = ""

    transfer_base_fare: float = 120.0
    transfer_per_km_rate: float = 22.0
    transfer_minimum_fare: float = 180.0
    transfer_airport_surcharge: float = 150.0
    transfer_railway_surcharge: float = 60.0
    transfer_bus_surcharge: float = 40.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
