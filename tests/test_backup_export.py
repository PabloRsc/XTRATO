from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Budget, Card, Category, InvoiceEntry, Purchase, User
from app.services.backup import build_user_backup


def make_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


def test_backup_contains_financial_history_and_excludes_password_hash():
    engine = make_db()
    with Session(engine) as db:
        user = User(username="owner", password_hash="must-never-be-exported")
        db.add(user)
        db.flush()

        card = Card(
            user_id=user.id, name="Nubank", issuer="Nubank", brand="Mastercard",
            last_four="1234", closing_day=25, due_day=5, color="#247a57", active=False,
        )
        category = Category(
            user_id=user.id, name="Compras", color="#78a88b", icon="shopping-bag",
            active=True,
        )
        db.add_all([card, category])
        db.flush()

        db.add(Budget(user_id=user.id, month=date(2026, 11, 1), limit_cents=100_000))
        purchase = Purchase(
            user_id=user.id, description="Notebook", kind="parcelado", direction="expense",
            purchase_date=date(2026, 9, 5), card_id=card.id, category_id=category.id,
            total_cents=100_000, installment_count=4, first_invoice_month=date(2026, 9, 1),
            current_installment=3, active=True, notes="Compra em andamento",
        )
        db.add(purchase)
        db.flush()
        db.add(InvoiceEntry(
            purchase_id=purchase.id, invoice_month=date(2026, 11, 1),
            installment_number=3, amount_cents=25_000, status="open",
        ))
        db.commit()

        payload = build_user_backup(db, user)
        assert payload["format"] == "xtrato-backup"
        assert payload["version"] == 1
        assert payload["account"] == {"username": "owner"}
        assert payload["cards"][0]["active"] is False
        assert payload["purchases"][0]["description"] == "Notebook"
        assert payload["invoice_entries"][0]["installment_number"] == 3
        assert payload["budgets"][0]["limit_cents"] == 100_000
        assert "password_hash" not in str(payload)
        assert "must-never-be-exported" not in str(payload)

    engine.dispose()


def test_backup_for_empty_user_returns_empty_collections():
    engine = make_db()
    with Session(engine) as db:
        user = User(username="owner", password_hash="secret")
        db.add(user)
        db.commit()

        payload = build_user_backup(db, user)

        assert payload["cards"] == []
        assert payload["categories"] == []
        assert payload["budgets"] == []
        assert payload["purchases"] == []
        assert payload["invoice_entries"] == []

    engine.dispose()
