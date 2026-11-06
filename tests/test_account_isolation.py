from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Budget, Card, Category, InvoiceEntry, Purchase, User
from app.routers import finance, resources
from app.schemas import CardIn, CategoryIn, PurchaseIn, PurchaseUpdateIn
from app.services.backup import build_user_backup


def make_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


def make_request(user_id: int):
    from starlette.requests import Request

    return Request({
        "type": "http",
        "method": "GET",
        "path": "/api",
        "headers": [],
        "query_string": b"",
        "session": {"user_id": user_id},
    })


def seed_two_accounts(db: Session):
    owner = User(username="owner", password_hash="owner-hash")
    stranger = User(username="stranger", password_hash="stranger-hash")
    db.add_all([owner, stranger])
    db.flush()

    owner_card = Card(
        user_id=owner.id, name="Cartão privado", closing_day=25, due_day=5,
        due_month_offset=1, color="#247a57", active=True,
    )
    owner_category = Category(
        user_id=owner.id, name="Categoria privada", color="#78a88b",
        icon="tag", active=True,
    )
    stranger_card = Card(
        user_id=stranger.id, name="Cartão do visitante", closing_day=20,
        due_day=10, due_month_offset=1, color="#7797c6", active=True,
    )
    stranger_category = Category(
        user_id=stranger.id, name="Categoria do visitante", color="#7797c6",
        icon="tag", active=True,
    )
    db.add_all([owner_card, owner_category, stranger_card, stranger_category])
    db.flush()

    purchase = Purchase(
        user_id=owner.id,
        description="Compra confidencial",
        kind="parcelado",
        direction="expense",
        purchase_date=date(2026, 10, 10),
        card_id=owner_card.id,
        category_id=owner_category.id,
        total_cents=12_000,
        installment_count=3,
        first_invoice_month=date(2026, 10, 1),
        current_installment=1,
        active=True,
        notes="Informação privada",
    )
    db.add(purchase)
    db.flush()
    entry = InvoiceEntry(
        purchase_id=purchase.id,
        invoice_month=date(2026, 11, 1),
        installment_number=2,
        amount_cents=4_000,
        status="open",
    )
    db.add(entry)
    db.add(Budget(user_id=owner.id, month=date(2026, 11, 1), limit_cents=100_000))
    db.commit()

    return owner, stranger, owner_card, owner_category, stranger_card, stranger_category, purchase, entry


def test_authenticated_account_can_only_list_its_own_cards_and_categories():
    engine = make_db()
    with Session(engine) as db:
        owner, stranger, owner_card, owner_category, stranger_card, stranger_category, *_ = seed_two_accounts(db)
        request = make_request(stranger.id)

        cards = resources.list_cards(request, include_archived=True, db=db)
        categories = resources.list_categories(request, include_archived=True, db=db)

        assert [row["id"] for row in cards] == [stranger_card.id]
        assert [row["name"] for row in cards] == ["Cartão do visitante"]
        assert [row["id"] for row in categories] == [stranger_category.id]
        assert [row["name"] for row in categories] == ["Categoria do visitante"]
        assert owner_card.id not in [row["id"] for row in cards]
        assert owner_category.id not in [row["id"] for row in categories]

    engine.dispose()


def test_authenticated_account_cannot_read_another_accounts_statement_dashboard_or_backup():
    engine = make_db()
    with Session(engine) as db:
        owner, stranger, owner_card, owner_category, *_ = seed_two_accounts(db)
        request = make_request(stranger.id)

        entries = finance.list_entries("2026-11", request, db=db)
        dashboard = finance.dashboard("2026-11", request, db=db)
        recurrences = finance.list_recurrences(request, db=db)
        backup = build_user_backup(db, stranger)

        assert entries == []
        assert dashboard["spent_cents"] == 0
        assert dashboard["limit_cents"] is None
        assert dashboard["categories"] == []
        assert dashboard["card_totals"] == []
        assert dashboard["recent_entries"] == []
        assert dashboard["cards"] == [{"id": stranger_card.id, "name": stranger_card.name,
                                       "color": stranger_card.color, "active": True, "total_cents": 0}]
        assert recurrences == []
        assert backup["cards"] == [backup["cards"][0]] if backup["cards"] else []
        assert all(card["name"] != owner_card.name for card in backup["cards"])
        assert all(category["name"] != owner_category.name for category in backup["categories"])
        assert backup["purchases"] == []
        assert backup["invoice_entries"] == []

    engine.dispose()


def test_account_cannot_edit_cancel_or_archive_another_accounts_records():
    engine = make_db()
    with Session(engine) as db:
        owner, stranger, owner_card, owner_category, *_rest, purchase, _entry = seed_two_accounts(db)
        request = make_request(stranger.id)

        with pytest.raises(HTTPException) as update_purchase_error:
            finance.update_purchase(
                purchase.id, PurchaseUpdateIn(description="Tentativa de invasão"), request, db
            )
        assert update_purchase_error.value.status_code == 404

        with pytest.raises(HTTPException) as cancel_error:
            finance.cancel_purchase(purchase.id, request, db)
        assert cancel_error.value.status_code == 404

        with pytest.raises(HTTPException) as update_card_error:
            resources.update_card(owner_card.id, CardIn(name="Cartão alterado"), request, db)
        assert update_card_error.value.status_code == 404

        with pytest.raises(HTTPException) as archive_card_error:
            resources.archive_card(owner_card.id, request, db)
        assert archive_card_error.value.status_code == 404

        with pytest.raises(HTTPException) as reactivate_card_error:
            resources.reactivate_card(owner_card.id, request, db)
        assert reactivate_card_error.value.status_code == 404

        with pytest.raises(HTTPException) as update_category_error:
            resources.update_category(owner_category.id, CategoryIn(name="Categoria alterada"), request, db)
        assert update_category_error.value.status_code == 404

        with pytest.raises(HTTPException) as archive_category_error:
            resources.archive_category(owner_category.id, request, db)
        assert archive_category_error.value.status_code == 404

        with pytest.raises(HTTPException) as reactivate_category_error:
            resources.reactivate_category(owner_category.id, request, db)
        assert reactivate_category_error.value.status_code == 404

        db.refresh(purchase)
        db.refresh(owner_card)
        db.refresh(owner_category)
        assert purchase.description == "Compra confidencial"
        assert purchase.active is True
        assert owner_card.name == "Cartão privado"
        assert owner_card.active is True
        assert owner_category.name == "Categoria privada"
        assert owner_category.active is True

    engine.dispose()


def test_account_cannot_create_purchase_using_another_accounts_card_or_category():
    engine = make_db()
    with Session(engine) as db:
        owner, stranger, owner_card, owner_category, *_ = seed_two_accounts(db)
        request = make_request(stranger.id)
        payload = PurchaseIn(
            description="Tentativa de compra",
            kind="avista",
            purchase_date=date(2026, 11, 6),
            card_id=owner_card.id,
            category_id=owner_category.id,
            amount_cents=1_000,
            first_invoice_month="2026-11",
        )

        with pytest.raises(HTTPException) as error:
            finance.create_purchase(payload, request, db)
        assert error.value.status_code == 422
        assert db.scalar(select(Purchase).where(Purchase.user_id == stranger.id)) is None

    engine.dispose()


def test_account_budget_changes_do_not_affect_another_account():
    engine = make_db()
    with Session(engine) as db:
        owner, stranger, *_ = seed_two_accounts(db)
        request = make_request(stranger.id)

        result = finance.save_budget(
            finance.BudgetIn(month="2026-11", limit_cents=25_000)
            if hasattr(finance, "BudgetIn") else None,
            request,
            db,
        )
        owner_budget = db.scalar(select(Budget).where(Budget.user_id == owner.id))
        stranger_budget = db.scalar(select(Budget).where(Budget.user_id == stranger.id))

        assert result["limit_cents"] == 25_000
        assert owner_budget.limit_cents == 100_000
        assert stranger_budget.limit_cents == 25_000

    engine.dispose()
