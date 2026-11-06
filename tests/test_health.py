from sqlalchemy.exc import SQLAlchemyError

from app import main


class WorkingSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, statement):
        return [(1,)]


class UnavailableSession(WorkingSession):
    def execute(self, statement):
        raise SQLAlchemyError("database unavailable")


def test_readyz_returns_ready_when_database_query_succeeds(monkeypatch):
    monkeypatch.setattr(main, "SessionLocal", WorkingSession)

    assert main.readyz() == {"status": "ready"}


def test_readyz_returns_service_unavailable_when_database_query_fails(monkeypatch):
    monkeypatch.setattr(main, "SessionLocal", UnavailableSession)

    response = main.readyz()

    assert response.status_code == 503
    assert response.body == b'{"status":"not_ready"}'

def test_existing_accounts_keep_exact_categories_after_application_restart(monkeypatch):
    import asyncio

    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session
    from sqlalchemy.pool import StaticPool

    from app.database import Base
    from app.models import Category, User

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(username="restored", password_hash="test-hash")
        db.add(user)
        db.flush()
        db.add(Category(
            user_id=user.id,
            name="Categoria importada",
            color="#123456",
            icon="tag",
            active=True,
        ))
        db.commit()
        user_id = user.id

    monkeypatch.setattr(main, "SessionLocal", lambda: Session(engine))

    async def run_lifespan():
        async with main.lifespan(main.app):
            pass

    asyncio.run(run_lifespan())

    with Session(engine) as db:
        names = db.scalars(
            select(Category.name).where(Category.user_id == user_id)
        ).all()
        assert names == ["Categoria importada"]

    engine.dispose()

