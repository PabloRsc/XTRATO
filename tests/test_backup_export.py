from datetime import date

from sqlalchemy import create_engine, select
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
        assert payload["cards"][0]["due_month_offset"] == 1
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


def test_backup_can_be_restored_into_empty_account_with_history_preserved():
    from app.schemas import BackupRestoreIn
    from app.services.backup import restore_user_backup

    source_engine = make_db()
    with Session(source_engine) as source_db:
        source = User(username="source", password_hash="source-hash-must-not-copy")
        source_db.add(source)
        source_db.flush()

        source_card = Card(
            user_id=source.id,
            name="Nubank",
            issuer="Nubank",
            brand="Mastercard",
            last_four="4321",
            closing_day=25,
            due_day=5,
            due_month_offset=1,
            color="#247a57",
            active=False,
        )
        source_category = Category(
            user_id=source.id,
            name="Compras",
            color="#78a88b",
            icon="shopping-bag",
            active=True,
        )
        source_db.add_all([source_card, source_category])
        source_db.flush()
        source_db.add(Budget(user_id=source.id, month=date(2026, 11, 1), limit_cents=100_000))
        purchase = Purchase(
            user_id=source.id,
            description="Notebook",
            kind="parcelado",
            direction="expense",
            purchase_date=date(2026, 9, 5),
            card_id=source_card.id,
            category_id=source_category.id,
            total_cents=10_000,
            installment_count=2,
            first_invoice_month=date(2026, 10, 1),
            current_installment=2,
            active=False,
            notes="Parcela em andamento",
        )
        source_db.add(purchase)
        source_db.flush()
        source_db.add_all([
            InvoiceEntry(
                purchase_id=purchase.id,
                invoice_month=date(2026, 10, 1),
                installment_number=1,
                amount_cents=5_000,
                status="historical",
            ),
            InvoiceEntry(
                purchase_id=purchase.id,
                invoice_month=date(2026, 11, 1),
                installment_number=2,
                amount_cents=5_000,
                status="cancelled",
            ),
        ])
        source_db.commit()
        exported = build_user_backup(source_db, source)

    source_engine.dispose()
    target_engine = make_db()
    with Session(target_engine) as target_db:
        target = User(username="target", password_hash="target-password-hash")
        target_db.add(target)
        target_db.flush()
        # A newly initialized account may already contain default categories.
        target_db.add(Category(
            user_id=target.id,
            name="Outros",
            color="#929a94",
            icon="tag",
            active=True,
        ))
        target_db.commit()

        restore_payload = BackupRestoreIn.model_validate({
            **exported,
            "confirmation": "RESTAURAR",
        })
        result = restore_user_backup(target_db, target, restore_payload)
        target_db.commit()

        restored_card = target_db.scalar(select(Card).where(Card.user_id == target.id))
        restored_category = target_db.scalar(select(Category).where(
            Category.user_id == target.id,
            Category.name == "Compras",
        ))
        restored_budget = target_db.scalar(select(Budget).where(Budget.user_id == target.id))
        restored_purchase = target_db.scalar(select(Purchase).where(Purchase.user_id == target.id))
        restored_entries = target_db.scalars(
            select(InvoiceEntry)
            .where(InvoiceEntry.purchase_id == restored_purchase.id)
            .order_by(InvoiceEntry.invoice_month)
        ).all()

        assert result == {
            "cards": 1,
            "categories": 1,
            "budgets": 1,
            "purchases": 1,
            "invoice_entries": 2,
        }
        assert restored_card.id == source_card.id
        assert restored_card.active is False
        assert restored_card.due_month_offset == 1
        assert restored_category.id == source_category.id
        assert restored_budget.limit_cents == 100_000
        assert restored_purchase.id == purchase.id
        assert [row.status for row in restored_entries] == ["historical", "cancelled"]
        assert [row.installment_number for row in restored_entries] == [1, 2]
        assert target_db.get(User, target.id).password_hash == "target-password-hash"
        assert "source-hash-must-not-copy" not in str(restore_payload.model_dump())

    target_engine.dispose()


def test_backup_restore_refuses_an_account_that_already_has_a_card():
    import pytest

    from app.schemas import BackupRestoreIn
    from app.services.backup import restore_user_backup

    engine = make_db()
    with Session(engine) as db:
        user = User(username="target", password_hash="target-hash")
        db.add(user)
        db.flush()
        db.add(Card(
            user_id=user.id,
            name="Already used",
            closing_day=25,
            due_day=5,
            color="#247a57",
        ))
        db.commit()

        payload = BackupRestoreIn.model_validate({
            "confirmation": "RESTAURAR",
            "format": "xtrato-backup",
            "version": 1,
            "exported_at": "2026-11-06T12:00:00+00:00",
            "account": {"username": "source"},
            "cards": [],
            "categories": [],
            "budgets": [],
            "purchases": [],
            "invoice_entries": [],
        })
        with pytest.raises(ValueError, match="conta sem cartões"):
            restore_user_backup(db, user, payload)

    engine.dispose()


def test_backup_restore_requires_confirmation_and_rejects_dangling_entries():
    import pytest
    from pydantic import ValidationError

    from app.schemas import BackupRestoreIn

    base = {
        "format": "xtrato-backup",
        "version": 1,
        "exported_at": "2026-11-06T12:00:00+00:00",
        "account": {"username": "source"},
        "cards": [],
        "categories": [],
        "budgets": [],
        "purchases": [],
        "invoice_entries": [],
    }
    with pytest.raises(ValidationError):
        BackupRestoreIn.model_validate(base)

    invalid = {
        **base,
        "confirmation": "RESTAURAR",
        "invoice_entries": [{
            "id": 10,
            "purchase_id": 999,
            "invoice_month": "2026-11-01",
            "installment_number": None,
            "amount_cents": 100,
            "status": "open",
        }],
    }
    with pytest.raises(ValidationError):
        BackupRestoreIn.model_validate(invalid)
