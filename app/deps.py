from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models import User


def authenticated_user(request: Request, db: Session) -> User:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(status_code=401, detail="Sessão expirada. Entre novamente.")
    user = db.get(User, user_id)
    auth_version = request.session.get("auth_version")
    if not user or not isinstance(auth_version, int) or auth_version != user.session_version:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Sessão inválida ou revogada. Entre novamente.")
    return user
