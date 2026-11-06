from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Card, Category, InvoiceEntry, Purchase, User
from app.services.billing import add_months, create_invoice_entries, month_from_purchase_date, query_month_entries, split_amount


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


def test_card_closing_and_explicit_payment_month_offset():
    # Closing on day 25, paid the following month: Nov 20 is paid in December.
    assert month_from_purchase_date(date(2026, 11, 20), 25, 1) == date(2026, 12, 1)
    # After closing, the following statement is paid in January.
    assert month_from_purchase_date(date(2026, 11, 28), 25, 1) == date(2027, 1, 1)
    # A card configured to be paid in the same month as closing.
    assert month_from_purchase_date(date(2026, 11, 3), 5, 0) == date(2026, 11, 1)
    assert month_from_purchase_date(date(2026, 11, 8), 5, 0) == date(2026, 12, 1)


def test_payment_month_offset_rejects_values_other_than_zero_or_one():
    import pytest

    with pytest.raises(ValueError):
        month_from_purchase_date(date(2026, 11, 3), 25, 2)


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



def test_cancel_purchase_preserves_past_history_and_cancels_current_and_future_entries():
    from app.services.billing import cancel_purchase_entries

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
            current_installment=1,
            active=True,
        )
        db.add(purchase)
        db.flush()
        for number, month in enumerate(
            [date(2026, 9, 1), date(2026, 10, 1), date(2026, 11, 1), date(2026, 12, 1)],
            start=1,
        ):
            db.add(InvoiceEntry(
                purchase_id=purchase.id,
                invoice_month=month,
                installment_number=number,
                amount_cents=25_000,
                status="open",
            ))
        db.flush()

        cancelled_count = cancel_purchase_entries(purchase, date(2026, 11, 1))
        db.flush()
        rows = db.scalars(
            select(InvoiceEntry).where(InvoiceEntry.purchase_id == purchase.id).order_by(InvoiceEntry.invoice_month)
        ).all()

        assert cancelled_count == 2
        assert purchase.active is False
        assert [row.status for row in rows] == ["open", "open", "cancelled", "cancelled"]
    engine.dispose()


def test_cancelled_recurring_purchase_does_not_generate_more_entries():
    from app.services.billing import cancel_purchase_entries, ensure_recurring_entries

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
            purchase_date=date(2026, 10, 1),
            card_id=card.id,
            category_id=category.id,
            total_cents=3_990,
            installment_count=1,
            first_invoice_month=date(2026, 10, 1),
            current_installment=1,
            active=True,
        )
        db.add(purchase)
        db.flush()
        db.add(InvoiceEntry(
            purchase_id=purchase.id,
            invoice_month=date(2026, 10, 1),
            installment_number=None,
            amount_cents=3_990,
            status="historical",
        ))
        db.flush()

        cancel_purchase_entries(purchase, date(2026, 11, 1))
        ensure_recurring_entries(db, user.id, date(2027, 2, 1))
        db.commit()
        rows = db.scalars(
            select(InvoiceEntry).where(InvoiceEntry.purchase_id == purchase.id).order_by(InvoiceEntry.invoice_month)
        ).all()

        assert len(rows) == 1
        assert rows[0].status == "historical"
    engine.dispose()



def test_parse_month_requires_four_digit_year_and_zero_padded_month():
    from app.services.billing import parse_month

    assert parse_month("2026-01") == date(2026, 1, 1)
    assert parse_month("2026-12") == date(2026, 12, 1)


def test_parse_month_rejects_noncanonical_or_invalid_month_values():
    import pytest
    from app.services.billing import parse_month

    for value in ["2026-1", "26-01", "2026-00", "2026-13", "2026/01", "2026-01-01", "abcd-01"]:
        with pytest.raises(ValueError):
            parse_month(value)



def test_signed_invoice_amount_applies_credits_to_spending():
    from app.services.billing import signed_entry_amount

    purchases = [12_500, 4_000]
    credits = [2_000, 1_500]
    net = sum(signed_entry_amount(value, "expense") for value in purchases)
    net += sum(signed_entry_amount(value, "credit") for value in credits)

    assert net == 13_000


def test_signed_invoice_amount_allows_credit_balance_and_rejects_invalid_values():
    import pytest
    from app.services.billing import signed_entry_amount

    assert signed_entry_amount(15_000, "credit") + signed_entry_amount(10_000, "expense") == -5_000
    with pytest.raises(ValueError):
        signed_entry_amount(-1, "expense")
    with pytest.raises(ValueError):
        signed_entry_amount(100, "unknown")


def test_budget_usage_percentage_never_goes_below_zero():
    import pytest
    from app.services.billing import budget_usage_percentage

    assert budget_usage_percentage(75_000, 100_000) == 75.0
    assert budget_usage_percentage(-5_000, 100_000) == 0.0
    assert budget_usage_percentage(500, 0) == 100.0
    assert budget_usage_percentage(-500, 0) == 0.0
    with pytest.raises(ValueError):
        budget_usage_percentage(100, -1)


def test_archived_card_and_category_do_not_hide_existing_invoice_entries():
    engine = make_db()
    with Session(engine) as db:
        user = User(username="owner", password_hash="test")
        db.add(user)
        db.flush()
        card = Card(
            user_id=user.id, name="Cartão antigo", closing_day=25, due_day=5,
            color="#247a57", active=False,
        )
        category = Category(
            user_id=user.id, name="Categoria antiga", color="#78a88b",
            icon="tag", active=False,
        )
        db.add_all([card, category])
        db.flush()
        purchase = Purchase(
            user_id=user.id,
            description="Compra preservada",
            kind="avista",
            direction="expense",
            purchase_date=date(2026, 10, 10),
            card_id=card.id,
            category_id=category.id,
            total_cents=4_500,
            installment_count=1,
            first_invoice_month=date(2026, 11, 1),
            current_installment=1,
            active=True,
        )
        db.add(purchase)
        db.flush()
        db.add(InvoiceEntry(
            purchase_id=purchase.id,
            invoice_month=date(2026, 11, 1),
            installment_number=None,
            amount_cents=4_500,
            status="open",
        ))
        db.commit()

        rows = query_month_entries(db, user.id, date(2026, 11, 1))
        assert len(rows) == 1
        entry, restored_purchase, archived_card = rows[0]
        assert restored_purchase.description == "Compra preservada"
        assert archived_card.active is False
        assert db.get(Category, restored_purchase.category_id).active is False
        assert entry.amount_cents == 4_500
    engine.dispose()
