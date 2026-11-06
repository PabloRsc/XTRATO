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

if APP_ENV == "production" and len(SECRET_KEY) < 32:
    raise RuntimeError("APP_SECRET_KEY precisa ter pelo menos 32 caracteres em produção.")
if APP_ENV == "production" and not COOKIE_SECURE:
    raise RuntimeError("COOKIE_SECURE=true é obrigatório em produção, com HTTPS habilitado.")
if not SECRET_KEY:
    # Only a local-development fallback. Production refuses to start without a secret.
    SECRET_KEY = "local-development-only-change-before-deploy-please"
