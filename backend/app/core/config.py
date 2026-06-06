"""Configuración de la aplicación vía variables de entorno."""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===== Aplicación =====
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    log_level: str = "INFO"
    # NoDecode evita que pydantic-settings intente parsear la env var como JSON;
    # el validator se encarga de aceptar CSV o lista.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v: object) -> list[str]:
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        if isinstance(v, list):
            return v
        raise ValueError(f"Tipo no soportado para cors_origins: {type(v)}")

    # ===== Base de datos =====
    database_url: str
    database_url_sync: str | None = None
    postgres_user: str = "gym"
    postgres_password: str = "gym"
    postgres_db: str = "gym"

    # ===== JWT =====
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 60

    # ===== Motor facial =====
    face_model_name: str = "buffalo_l"
    face_execution_provider: str = "CPU"
    face_det_size_width: int = 640
    face_det_size_height: int = 640
    face_threshold_match: float = 0.55
    face_threshold_low: float = 0.40
    face_threshold_duplicate: float = 0.60
    face_min_face_size: int = 100
    face_min_det_score: float = 0.65

    # ===== Seed =====
    seed_superadmin_email: str = "admin@example.com"
    seed_superadmin_password: str = "changeme-123"
    seed_superadmin_name: str = "Admin Sistema"
    seed_gym_name: str = "Gimnasio Demo"
    seed_gym_address: str = "Calle Falsa 123"
    seed_gym_phone: str = "+5491100000000"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
