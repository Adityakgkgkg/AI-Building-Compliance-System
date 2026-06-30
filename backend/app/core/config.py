"""
AI Building Compliance System — Core Configuration

Loads environment variables via pydantic-settings.
All config values are centralized here so no module hardcodes paths or secrets.
"""

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application-wide settings loaded from .env file."""

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "AI Building Compliance System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # ── Server ───────────────────────────────────────────────────
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./app.db"

    # ── Uploads ──────────────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: str = ".ifc,.dxf"
    MAX_UPLOAD_SIZE_MB: int = 100

    @property
    def allowed_extensions_list(self) -> list[str]:
        """Return allowed extensions as a list."""
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    @property
    def max_upload_size_bytes(self) -> int:
        """Return max upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def upload_path(self) -> Path:
        """Return resolved upload directory path."""
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton — call this from anywhere."""
    return Settings()
