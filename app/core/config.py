import os
from datetime import date
from typing import Optional, List, Union, Any
from pydantic import computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    PROJECT_NAME: str = "Aura Workforce OS"
    VERSION: str = "1.0.0"
    ENV: str = "development"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Auth & Tokens
    SECRET_KEY: str = "supersecretkey-for-local-development-change-in-production"
    JWT_SECRET: str = "supersecretkey-for-local-development-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 60

    # Demo cut-off date per LedgerForge specification
    DEMO_TODAY: date = date(2026, 9, 30)

    # Operational & Caching
    SEED_ON_START: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"

    CORS_ORIGINS: Union[List[str], str] = ["*"]

    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "aura_workforce_db"

    DATABASE_URL: Optional[str] = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def validate_production_settings(self):
        env_val = (self.ENV or self.ENVIRONMENT).lower()
        secret_val = self.JWT_SECRET or self.SECRET_KEY
        if env_val == "production":
            if secret_val == "supersecretkey-for-local-development-change-in-production":
                raise ValueError(
                    "Default SECRET_KEY/JWT_SECRET is forbidden when ENV=production. "
                    "Please configure a secure, unique secret key."
                )
        return self

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        is_container = (
            os.getenv("RUNNING_IN_CONTAINER", "").lower() in ("true", "1")
            or os.getenv("IS_CONTAINER", "").lower() in ("true", "1")
            or os.getenv("CONTAINER", "").lower() in ("true", "1")
            or os.path.exists("/.dockerenv")
            or os.path.exists("/run/.containerenv")
        )
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if "@db:" in url and not is_container:
                url = url.replace("@db:", "@localhost:")
            # Use psycopg2 if psycopg (v3) is requested but psycopg2 is the installed driver
            if url.startswith("postgresql+psycopg://"):
                url = url.replace("postgresql+psycopg://", "postgresql+psycopg2://")
            return url

        host = self.POSTGRES_SERVER
        if host == "db" and not is_container:
            host = "localhost"

        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{host}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
