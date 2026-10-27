"""Application configuration loaded from environment / .env."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (avoids a hard python-dotenv dependency)."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv(BASE_DIR / ".env")


def _bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    def __init__(self) -> None:
        self.app_name = os.environ.get("APP_NAME", "NestQuest")
        self.base_dir = BASE_DIR

        # Database
        self.database_url = os.environ.get("DATABASE_URL", "")
        self.db_name = os.environ.get("DB_NAME", "house")

        # Auth
        self.jwt_secret = os.environ.get("JWT_SECRET", "dev-insecure-secret")
        self.jwt_algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
        self.jwt_expire_minutes = int(os.environ.get("JWT_EXPIRE_MINUTES", "10080"))

        # SMTP
        self.smtp_host = os.environ.get("SMTP_HOST", "")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_pass = os.environ.get("SMTP_PASS", "")
        self.smtp_from = os.environ.get("SMTP_FROM", "noreply@example.com")
        self.smtp_enabled = _bool("SMTP_ENABLED", False)

        # Cloudinary (image uploads)
        self.cloudinary_cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
        self.cloudinary_api_key = os.environ.get("CLOUDINARY_API_KEY", "")
        self.cloudinary_api_secret = os.environ.get("CLOUDINARY_API_SECRET", "")

        # Seed admin
        self.admin_email = os.environ.get("ADMIN_EMAIL", "admin@gmail.com")
        self.admin_password = os.environ.get("ADMIN_PASSWORD", "Admin@123")
        self.admin_name = os.environ.get("ADMIN_NAME", "Platform Admin")

        # App URLs
        self.frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        self.backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")

        self.seed_demo_data = _bool("SEED_DEMO_DATA", True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
