from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    # Optional deployment/legacy override. Local setup normally uses DB_* below.
    database_url: str = Field(default="", repr=False)
    db_host: str = Field(default="127.0.0.1", min_length=1)
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str = Field(default="neurocare_db", min_length=1)
    db_user: str = Field(default="postgres", min_length=1)
    db_password: SecretStr | None = Field(default=None, repr=False)
    app_env: str = "development"
    secret_key: str = Field(min_length=32, repr=False)
    frontend_url: str = "http://localhost:5173"
    model_dir: Path | None = None

    @property
    def cors_origins(self) -> list[str]:
        origins = [self.frontend_url]
        parsed = urlsplit(self.frontend_url)
        aliases = {"localhost": "127.0.0.1", "127.0.0.1": "localhost"}
        if (
            self.app_env == "development" and parsed.scheme in {"http", "https"}
            and parsed.hostname in aliases and not parsed.username and not parsed.password
            and parsed.path in {"", "/"} and not parsed.query and not parsed.fragment
        ):
            host = aliases[parsed.hostname]
            netloc = f"{host}:{parsed.port}" if parsed.port is not None else host
            origins.append(urlunsplit((parsed.scheme, netloc, "", "", "")))
        return origins

    @field_validator("model_dir", mode="before")
    @classmethod
    def empty_model_dir(cls, value):
        return None if value == "" else value

    @field_validator("database_url")
    @classmethod
    def postgres_only(cls, value: str) -> str:
        if value and make_url(value).drivername != "postgresql+psycopg":
            raise ValueError("DATABASE_URL must use postgresql+psycopg")
        return value

    @model_validator(mode="after")
    def assemble_database_url(self):
        if not self.database_url:
            if self.db_password is None or not self.db_password.get_secret_value():
                raise ValueError("Set DB_PASSWORD in the root .env")
            self.database_url = URL.create(
                "postgresql+psycopg", username=self.db_user,
                password=self.db_password.get_secret_value(), host=self.db_host,
                port=self.db_port, database=self.db_name,
            ).render_as_string(hide_password=False)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
