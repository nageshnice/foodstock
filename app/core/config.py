from decimal import Decimal
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables and an optional .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Food Stock API"
    app_env: Literal["development", "testing", "staging", "production"] = "development"
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    log_level: str = "INFO"

    database_url: str = Field(
        validation_alias="DATABASE_URL",
        pattern=r"^mysql\+aiomysql://",
    )
    db_echo: bool = False
    db_pool_recycle: int = Field(default=3600, ge=60)

    jwt_secret: SecretStr = Field(validation_alias="JWT_SECRET", min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=10080, gt=0)

    cors_origins: list[str] = Field(default_factory=list)

    default_tax_rate: Decimal = Field(default=Decimal("5.00"), ge=0)
    delivery_fee: Decimal = Field(default=Decimal("5.00"), ge=0)
    free_delivery_threshold: Decimal = Field(default=Decimal("499.00"), ge=0)
    minimum_order_amount: Decimal = Field(default=Decimal("199.00"), ge=0)

    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: SecretStr | None = None

    # Public URL prefix when served behind a reverse proxy (e.g. /foodstock)
    root_path: str = Field(default="", validation_alias="ROOT_PATH")
    upload_dir: str = Field(default="uploads", validation_alias="UPLOAD_DIR")


@lru_cache
def get_settings() -> Settings:
    """Return one validated settings instance per process."""

    return Settings()  # type: ignore[call-arg]
