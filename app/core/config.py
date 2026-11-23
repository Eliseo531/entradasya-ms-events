from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator


class Settings(BaseSettings):
    PORT: int = Field(default=8002)
    ENVIRONMENT: str = Field(default="development")
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://events_user:events_pass@localhost:5432/events_db"
    )
    JWT_SECRET: str = Field(default="super-secure-shared-secret-entradasya-2026")
    JWT_ALGORITHM: str = Field(default="HS256")
    INTERNAL_TOKEN: str = Field(default="internal-service-secret-entradasya-2026")
    INTERNAL_SERVICE_KEY: Optional[str] = None
    LOG_LEVEL: str = Field(default="INFO")

    # DB host/port/user/pass fallbacks if DATABASE_URL not explicitly set
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_NAME: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None

    @model_validator(mode="after")
    def assemble_db_and_keys(self) -> "Settings":
        if self.INTERNAL_SERVICE_KEY and not self.INTERNAL_TOKEN:
            self.INTERNAL_TOKEN = self.INTERNAL_SERVICE_KEY
        elif not self.INTERNAL_SERVICE_KEY:
            self.INTERNAL_SERVICE_KEY = self.INTERNAL_TOKEN

        # If DB components provided without custom DATABASE_URL
        if (
            self.DB_HOST
            and self.DB_USER
            and self.DB_NAME
            and "localhost:5432/events_db" in self.DATABASE_URL
        ):
            port = self.DB_PORT or 5432
            pwd = f":{self.DB_PASSWORD}" if self.DB_PASSWORD else ""
            self.DATABASE_URL = f"postgresql+asyncpg://{self.DB_USER}{pwd}@{self.DB_HOST}:{port}/{self.DB_NAME}"

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
