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


def test_card_closing_and_due_days_suggest_payment_month():
    # Closing on day 25 and paying on day 5: November statement is paid in December.
    assert month_from_purchase_date(date(2026, 11, 20), 25, 5) == date(2026, 12, 1)
    # A purchase after closing enters the next statement and is paid in January.
    assert month_from_purchase_date(date(2026, 11, 28), 25, 5) == date(2027, 1, 1)
    # If the due day is later than closing, payment is in the closing month.
    assert month_from_purchase_date(date(2026, 11, 3), 5, 20) == date(2026, 11, 1)
    assert month_from_purchase_date(date(2026, 11, 8), 5, 20) == date(2026, 12, 1)


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



def test_split_amount_places_uneven_cent_in_last_installment():
    assert split_amount(1_000, 3) == [333, 333, 334]
    assert split_amount(1_001, 4) == [250, 250, 250, 251]


def test_recurring_entries_are_created_only_through_end_month_and_are_idempotent():
    from app.services.billing import ensure_recurring_entries

    engine = make_db()
    with Session(engine) as db:
        user = User(username="owner", password_hash="test")
        db.add(user)
        db.flush()
        card = Card(user_id=user.id, name="Inter", closing_day=20, due_day=10, color="#247a57")
        category = Category(user_id=user.id, name="Assinaturas", color="#78a88b", icon="repeat")
        db.add_all([card, category])
        db.flush()
        purchase = Purchase(
            user_id=user.id,
            description="Streaming",
            kind="recorrente",
            direction="expense",
            purchase_date=date(2026, 11, 1),
            card_id=card.id,
            category_id=category.id,
            total_cents=3_990,
            installment_count=1,
            first_invoice_month=date(2026, 11, 1),
            current_installment=1,
            end_invoice_month=date(2027, 1, 1),
            active=True,
        )
        db.add(purchase)
        db.flush()

        ensure_recurring_entries(db, user.id, date(2026, 12, 1))
        ensure_recurring_entries(db, user.id, date(2026, 12, 1))
        db.commit()
        rows = db.scalars(
            select(InvoiceEntry).where(InvoiceEntry.purchase_id == purchase.id).order_by(InvoiceEntry.invoice_month)
        ).all()
        assert [row.invoice_month for row in rows] == [date(2026, 11, 1), date(2026, 12, 1)]

        ensure_recurring_entries(db, user.id, date(2027, 3, 1))
        db.commit()
        rows = db.scalars(
            select(InvoiceEntry).where(InvoiceEntry.purchase_id == purchase.id).order_by(InvoiceEntry.invoice_month)
        ).all()
        assert [row.invoice_month for row in rows] == [
            date(2026, 11, 1), date(2026, 12, 1), date(2027, 1, 1)
        ]
        assert all(row.amount_cents == 3_990 for row in rows)
    engine.dispose()
