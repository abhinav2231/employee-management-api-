from typing import Optional
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core App Settings
    PROJECT_NAME: str = "LedgerForge - Zenith Nova Technologies"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "supersecretkey-for-local-development-change-in-production"

    # Database Settings
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "aura_workforce_db"

    # Optional override for direct full connection string
    DATABASE_URL: Optional[str] = None

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Returns DATABASE_URL if provided, otherwise builds the connection string.
        Automatically resolves host 'db' to 'localhost' when running on host machine.
        """
        import os
        is_container = os.path.exists("/.dockerenv")
        if self.DATABASE_URL:
            if "@db:" in self.DATABASE_URL and not is_container:
                return self.DATABASE_URL.replace("@db:", "@localhost:")
            return self.DATABASE_URL

        host = self.POSTGRES_SERVER
        if host == "db" and not is_container:
            host = "localhost"

        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{host}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
