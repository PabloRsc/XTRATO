from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

from app.database import Base
from app.deps import authenticated_user
from app.models import User
from app.routers.auth import change_password
from app.schemas import PasswordChangeIn
from app.security import hash_password, verify_password


def make_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return engine


def make_request(session):
    return Request({"type": "http", "method": "POST", "path": "/api/auth/password", "headers": [], "query_string": b"", "session": session})


def test_session_version_is_required_and_stale_sessions_are_revoked():
    import pytest
    from fastapi import HTTPException
    engine = make_db()
    with Session(engine) as db:
        user = User(username="owner", password_hash=hash_password("current-password-123"))
        db.add(user)
        db.commit()
        valid = {"user_id": user.id, "auth_version": user.session_version}
        assert authenticated_user(make_request(valid), db).id == user.id
        stale = {"user_id": user.id, "auth_version": user.session_version - 1}
        with pytest.raises(HTTPException) as exc:
            authenticated_user(make_request(stale), db)
        assert exc.value.status_code == 401
        assert stale == {}
        missing = {"user_id": user.id}
        with pytest.raises(HTTPException):
            authenticated_user(make_request(missing), db)
        assert missing == {}
    engine.dispose()


def test_password_change_hashes_new_password_and_invalidates_old_session():
    import pytest
    from fastapi import HTTPException
    engine = make_db()
    with Session(engine) as db:
        user = User(username="owner", password_hash=hash_password("current-password-123"))
        db.add(user)
        db.commit()
        old_session = {"user_id": user.id, "auth_version": user.session_version}
        active_session = {"user_id": user.id, "auth_version": user.session_version}
        result = change_password(PasswordChangeIn(current_password="current-password-123", new_password="a-brand-new-strong-password"), make_request(active_session), db)
        db.refresh(user)
        assert result == {"ok": True, "reauthenticate": True}
        assert active_session == {}
        assert user.session_version == 1
        assert verify_password("a-brand-new-strong-password", user.password_hash)
        assert not verify_password("current-password-123", user.password_hash)
        with pytest.raises(HTTPException) as exc:
            authenticated_user(make_request(old_session), db)
        assert exc.value.status_code == 401
    engine.dispose()


def test_password_change_rejects_wrong_current_password_without_mutating_account():
    import pytest
    from fastapi import HTTPException
    engine = make_db()
    with Session(engine) as db:
        user = User(username="owner", password_hash=hash_password("current-password-123"))
        db.add(user)
        db.commit()
        old_hash = user.password_hash
        with pytest.raises(HTTPException) as exc:
            change_password(PasswordChangeIn(current_password="wrong-password", new_password="a-brand-new-strong-password"), make_request({"user_id": user.id, "auth_version": user.session_version}), db)
        assert exc.value.status_code == 400
        db.refresh(user)
        assert user.password_hash == old_hash
        assert user.session_version == 0
    engine.dispose()


def test_failed_password_change_attempts_are_rate_limited_per_account():
    import pytest
    from fastapi import HTTPException
    from app.routers import auth
    engine = make_db()
    with Session(engine) as db:
        user = User(username="owner", password_hash=hash_password("current-password-123"))
        db.add(user)
        db.commit()
        session = {"user_id": user.id, "auth_version": user.session_version}
        rate_key = f"password-change-user:{user.id}"
        auth._attempts.pop(rate_key, None)
        for _ in range(auth._MAX_FAILED_ATTEMPTS):
            with pytest.raises(HTTPException) as exc:
                change_password(PasswordChangeIn(current_password="wrong-password", new_password="a-brand-new-strong-password"), make_request(session), db)
            assert exc.value.status_code == 400
        with pytest.raises(HTTPException) as limited:
            change_password(PasswordChangeIn(current_password="wrong-password", new_password="a-brand-new-strong-password"), make_request(session), db)
        assert limited.value.status_code == 429
        auth._attempts.pop(rate_key, None)
    engine.dispose()
