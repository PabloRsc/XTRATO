from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

APP_ENV = os.getenv("APP_ENV", "development").lower()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./xtrato.db")
SECRET_KEY = os.getenv("APP_SECRET_KEY", "")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() in {"1", "true", "yes", "on"}
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "America/Sao_Paulo")
try:
    APP_TZ = ZoneInfo(APP_TIMEZONE)
except ZoneInfoNotFoundError as exc:
    raise RuntimeError(f"Fuso horário inválido em APP_TIMEZONE: {APP_TIMEZONE}") from exc

def local_today():
    return datetime.now(APP_TZ).date()
SESSION_MAX_AGE = int(os.getenv("SESSION_MAX_AGE", str(60 * 60 * 24 * 14)))
INITIAL_ADMIN_USERNAME = os.getenv("INITIAL_ADMIN_USERNAME", "").strip()
INITIAL_ADMIN_PASSWORD = os.getenv("INITIAL_ADMIN_PASSWORD", "")

def validate_production_settings(
    app_env: str,
    secret_key: str,
    cookie_secure: bool,
    initial_admin_password: str,
) -> None:
    if app_env != "production":
        return
    if (
        len(secret_key) < 32
        or secret_key.startswith("CHANGE_ME")
        or secret_key.startswith("local-development")
    ):
        raise RuntimeError(
            "APP_SECRET_KEY deve ser um segredo único de pelo menos 32 caracteres; "
            "valores de exemplo não são aceitos em produção."
        )
    if not cookie_secure:
        raise RuntimeError("COOKIE_SECURE=true é obrigatório em produção, com HTTPS habilitado.")
    if initial_admin_password and (
        len(initial_admin_password) < 12
        or initial_admin_password.startswith("CHANGE_ME")
    ):
        raise RuntimeError(
            "INITIAL_ADMIN_PASSWORD deve ter pelo menos 12 caracteres e não pode ser o valor de exemplo."
        )


validate_production_settings(APP_ENV, SECRET_KEY, COOKIE_SECURE, INITIAL_ADMIN_PASSWORD)
if not SECRET_KEY:
    # Only a local-development fallback. Production refuses to start without a secret.
    SECRET_KEY = "local-development-only-change-before-deploy-please"
