from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import select

from app.config import (
    COOKIE_SECURE, INITIAL_ADMIN_PASSWORD, INITIAL_ADMIN_USERNAME,
    SECRET_KEY, SESSION_MAX_AGE,
)
from app.database import SessionLocal
from app.models import Category, User
from app.routers import auth, finance, resources
from app.security import hash_password

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
DEFAULT_CATEGORIES = [
    ("Alimentação", "#d39b61", "utensils"),
    ("Mercado", "#72a58a", "shopping-basket"),
    ("Transporte", "#7797c6", "car-front"),
    ("Saúde", "#c77c78", "heart-pulse"),
    ("Assinaturas", "#9b86bf", "repeat"),
    ("Lazer", "#d38aab", "ticket"),
    ("Compras", "#6f9fa5", "shopping-bag"),
    ("Outros", "#929a94", "tag"),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    with SessionLocal() as db:
        user_count = len(db.scalars(select(User.id)).all())
        if user_count == 0:
            if not INITIAL_ADMIN_USERNAME or not INITIAL_ADMIN_PASSWORD:
                raise RuntimeError(
                    "Nenhum usuário inicial foi configurado. Defina "
                    "INITIAL_ADMIN_USERNAME e INITIAL_ADMIN_PASSWORD no ambiente."
                )
            user = User(username=INITIAL_ADMIN_USERNAME, password_hash=hash_password(INITIAL_ADMIN_PASSWORD))
            db.add(user)
            db.flush()
            for name, color, icon in DEFAULT_CATEGORIES:
                db.add(Category(user_id=user.id, name=name, color=color, icon=icon))
            db.commit()
        else:
            # Seed only missing defaults for the existing owner; custom categories remain untouched.
            users = db.scalars(select(User)).all()
            for user in users:
                existing = set(db.scalars(select(Category.name).where(Category.user_id == user.id)).all())
                for name, color, icon in DEFAULT_CATEGORIES:
                    if name not in existing:
                        db.add(Category(user_id=user.id, name=name, color=color, icon=icon))
            db.commit()
    yield


app = FastAPI(
    title="XTRATO",
    description="Controle pessoal de gastos em cartões de crédito.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.add_middleware(
    BackupRestoreSizeLimitMiddleware,
    max_bytes=MAX_BACKUP_UPLOAD_BYTES,
)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="xtrato_session",
    max_age=SESSION_MAX_AGE,
    same_site="strict",
    https_only=COOKIE_SECURE,
)


MAX_BACKUP_UPLOAD_BYTES = 10 * 1024 * 1024


class _BackupRestoreTooLarge(Exception):
    pass


class BackupRestoreSizeLimitMiddleware:
    def __init__(self, app, max_bytes: int = MAX_BACKUP_UPLOAD_BYTES):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if (
            scope["type"] != "http"
            or scope.get("path") != "/api/backup/restore"
            or scope.get("method") != "POST"
        ):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        raw_length = headers.get(b"content-length")
        if raw_length is not None:
            try:
                declared_length = int(raw_length.decode("ascii"))
            except (UnicodeDecodeError, ValueError):
                response = JSONResponse(
                    {"detail": "Cabeçalho de tamanho da requisição inválido."},
                    status_code=400,
                )
                await response(scope, receive, send)
                return
            if declared_length < 0:
                response = JSONResponse(
                    {"detail": "Cabeçalho de tamanho da requisição inválido."},
                    status_code=400,
                )
                await response(scope, receive, send)
                return
            if declared_length > self.max_bytes:
                response = JSONResponse(
                    {"detail": "O arquivo de backup excede o limite de 10 MB."},
                    status_code=413,
                )
                await response(scope, receive, send)
                return

        received_bytes = 0

        async def limited_receive():
            nonlocal received_bytes
            message = await receive()
            if message["type"] == "http.request":
                received_bytes += len(message.get("body", b""))
                if received_bytes > self.max_bytes:
                    raise _BackupRestoreTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _BackupRestoreTooLarge:
            response = JSONResponse(
                {"detail": "O arquivo de backup excede o limite de 10 MB."},
                status_code=413,
            )
            await response(scope, receive, send)


def private_api_error(detail: str, status_code: int) -> JSONResponse:
    response = JSONResponse({"detail": detail}, status_code=status_code)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    if COOKIE_SECURE:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.middleware("http")
async def protect_mutations(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        if request.headers.get("x-xtrato-request") != "1":
            return private_api_error("Requisição não autorizada.", 403)
        origin = request.headers.get("origin")
        host = request.headers.get("host", "").lower()
        if origin:
            from urllib.parse import urlparse
            if (urlparse(origin).netloc or "").lower() != host:
                return private_api_error("Origem não autorizada.", 403)
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    if COOKIE_SECURE:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


app.include_router(auth.router)
app.include_router(resources.router)
app.include_router(finance.router)


@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok"}


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")
