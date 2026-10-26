from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_origin: str = "http://127.0.0.1:3000"
    log_level: str = "INFO"

    database_url: str = "sqlite+pysqlite:///./data/resume_workshop.db"
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10

    ai_provider: str = "mock"
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str | None = None
    deepseek_timeout_seconds: int = 30

    sms_provider: str = "mock"
    sms_api_key: str | None = None
    sms_sign_name: str | None = None
    sms_template_code: str | None = None

    captcha_provider: str = "mock"
    turnstile_secret_key: str | None = None

    app_secret_key: str | None = None
    cookie_secure: bool = False
    cors_allowed_origins: str = "http://127.0.0.1:3000"

    rate_limit_enabled: bool = True
    rate_limit_login: str = "5/minute"
    rate_limit_otp: str = "1/minute"
    rate_limit_ai: str = "10/minute"

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_allowed_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
