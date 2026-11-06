from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import authenticated_user
from app.models import User
from app.schemas import LoginIn, PasswordChangeIn
from app.security import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])
_attempts: dict[str, deque[float]] = defaultdict(deque)
_attempts_lock = Lock()
_ATTEMPT_WINDOW_SECONDS = 15 * 60
_MAX_FAILED_ATTEMPTS = 8
_CLEANUP_EVERY_OPERATIONS = 128
_operations_since_cleanup = 0


def _cleanup_expired_attempts(now: float) -> None:
    """Remove expired IP/account buckets so abandoned keys cannot accumulate."""
    global _operations_since_cleanup
    _operations_since_cleanup += 1
    if _operations_since_cleanup < _CLEANUP_EVERY_OPERATIONS:
        return
    _operations_since_cleanup = 0
    expired_keys = [
        key for key, attempts in _attempts.items()
        if not attempts or now - attempts[-1] > _ATTEMPT_WINDOW_SECONDS
    ]
    for key in expired_keys:
        _attempts.pop(key, None)


def _check_attempt_rate(key: str) -> None:
    now = monotonic()
    with _attempts_lock:
        _cleanup_expired_attempts(now)
        attempts = _attempts.get(key)
        if attempts:
            while attempts and now - attempts[0] > _ATTEMPT_WINDOW_SECONDS:
                attempts.popleft()
        if attempts and len(attempts) >= _MAX_FAILED_ATTEMPTS:
            raise HTTPException(
                status_code=429,
                detail="Muitas tentativas. Aguarde alguns minutos antes de tentar novamente.",
                headers={"Retry-After": str(_ATTEMPT_WINDOW_SECONDS)},
            )


def _check_login_rate(request: Request) -> str:
    ip = request.client.host if request.client else "unknown"
    _check_attempt_rate(ip)
    return ip


def _record_failed_login(ip: str) -> None:
    with _attempts_lock:
        now = monotonic()
        _cleanup_expired_attempts(now)
        attempts = _attempts[ip]
        while attempts and now - attempts[0] > _ATTEMPT_WINDOW_SECONDS:
            attempts.popleft()
        attempts.append(now)


@router.post("/login")
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    ip = _check_login_rate(request)
    user = db.scalar(select(User).where(User.username == payload.username.strip()))
    if not user or not verify_password(payload.password, user.password_hash):
        _record_failed_login(ip)
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos.")
    with _attempts_lock:
        _attempts.pop(ip, None)
    request.session.clear()
    request.session["user_id"] = user.id
    request.session["auth_version"] = user.session_version
    return {"id": user.id, "username": user.username}


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.post("/password")
def change_password(payload: PasswordChangeIn, request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    rate_key = f"password-change-user:{user.id}"
    _check_attempt_rate(rate_key)
    if not verify_password(payload.current_password, user.password_hash):
        _record_failed_login(rate_key)
        raise HTTPException(status_code=400, detail="A senha atual está incorreta.")
    if verify_password(payload.new_password, user.password_hash):
        raise HTTPException(status_code=422, detail="Escolha uma senha diferente da atual.")

    user.password_hash = hash_password(payload.new_password)
    user.session_version += 1
    db.commit()
    with _attempts_lock:
        _attempts.pop(rate_key, None)
    request.session.clear()
    return {"ok": True, "reauthenticate": True}


@router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    return {"id": user.id, "username": user.username}
