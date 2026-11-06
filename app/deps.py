from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models import User


def authenticated_user(request: Request, db: Session) -> User:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(status_code=401, detail="Sessão expirada. Entre novamente.")
    user = db.get(User, user_id)
    if not user:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Sessão inválida. Entre novamente.")
    return user
