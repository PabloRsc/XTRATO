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
