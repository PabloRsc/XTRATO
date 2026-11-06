from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Card, Category, InvoiceEntry, Purchase, User
from app.services.billing import add_months, create_invoice_entries, month_from_purchase_date, split_amount


def make_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


def test_split_amount_preserves_every_cent():
    values = split_amount(10_000, 3)
    assert values == [3_333, 3_333, 3_334]
    assert sum(values) == 10_000


def test_month_arithmetic_crosses_year_boundary():
    assert add_months(date(2026, 12, 1), 1) == date(2027, 1, 1)
    assert add_months(date(2027, 1, 1), -2) == date(2026, 11, 1)


def test_card_closing_day_suggests_invoice_month():
    assert month_from_purchase_date(date(2026, 11, 20), 25) == date(2026, 11, 1)
    assert month_from_purchase_date(date(2026, 11, 28), 25) == date(2026, 12, 1)


def test_ongoing_installment_keeps_previous_entries_as_history():
    engine = make_db()
    with Session(engine) as db:
        user = User(username="owner", password_hash="test")
        db.add(user)
        db.flush()
        card = Card(user_id=user.id, name="Nubank", closing_day=25, due_day=5, color="#247a57")
        category = Category(user_id=user.id, name="Compras", color="#78a88b", icon="shopping-bag")
        db.add_all([card, category])
        db.flush()
        purchase = Purchase(
            user_id=user.id,
            description="Notebook",
            kind="parcelado",
            direction="expense",
            purchase_date=date(2026, 9, 5),
            card_id=card.id,
            category_id=category.id,
            total_cents=100_000,
            installment_count=4,
            first_invoice_month=date(2026, 9, 1),
            current_installment=3,
        )
        db.add(purchase)
        db.flush()
        create_invoice_entries(db, purchase, ongoing=True)
        db.flush()
        rows = db.scalars(select(InvoiceEntry).order_by(InvoiceEntry.installment_number)).all()
        assert [(r.installment_number, r.invoice_month, r.status, r.amount_cents) for r in rows] == [
            (1, date(2026, 9, 1), "historical", 25_000),
            (2, date(2026, 10, 1), "historical", 25_000),
            (3, date(2026, 11, 1), "open", 25_000),
            (4, date(2026, 12, 1), "open", 25_000),
        ]
    engine.dispose()
