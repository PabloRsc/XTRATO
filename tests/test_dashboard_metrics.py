from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Card, Category, InvoiceEntry, Purchase, User
from app.routers.finance import dashboard


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
        "path": "/api/dashboard",
        "headers": [],
        "query_string": b"",
        "session": {"user_id": user_id, "auth_version": 0},
    })


def test_dashboard_forecast_and_card_available_limit_include_future_open_installments():
    engine = make_db()
    with Session(engine) as db:
        user = User(username="dashboard-owner", password_hash="test")
        db.add(user)
        db.flush()

        card = Card(
            user_id=user.id,
            name="Cartão principal",
            issuer="Nubank",
            limit_cents=100_000,
            closing_day=25,
            due_day=5,
            due_month_offset=1,
            color="#247a57",
            active=True,
        )
        category = Category(
            user_id=user.id,
            name="Compras",
            color="#78a88b",
            icon="shopping-bag",
            active=True,
        )
        db.add_all([card, category])
        db.flush()

        purchase = Purchase(
            user_id=user.id,
            description="Compra parcelada",
            kind="parcelado",
            direction="expense",
            purchase_date=date(2026, 10, 10),
            card_id=card.id,
            category_id=category.id,
            total_cents=60_000,
            installment_count=3,
            first_invoice_month=date(2026, 10, 1),
            current_installment=1,
            active=True,
            notes="",
        )
        db.add(purchase)
        db.flush()

        for month, installment in (
            (date(2026, 10, 1), 1),
            (date(2026, 11, 1), 2),
            (date(2026, 12, 1), 3),
        ):
            db.add(InvoiceEntry(
                purchase_id=purchase.id,
                invoice_month=month,
                installment_number=installment,
                amount_cents=20_000,
                status="open",
            ))
        db.commit()

        result = dashboard("2026-11", make_request(user.id), db=db)

        card_summary = next(item for item in result["cards"] if item["id"] == card.id)
        assert card_summary["total_cents"] == 20_000
        assert card_summary["committed_cents"] == 40_000
        assert card_summary["available_cents"] == 60_000

        november = next(item for item in result["forecast"] if item["month"] == "2026-11")
        december = next(item for item in result["forecast"] if item["month"] == "2026-12")
        assert november["total_cents"] == 20_000
        assert december["total_cents"] == 20_000
        assert len(result["forecast"]) == 12

    engine.dispose()


def test_dashboard_card_commitment_is_scoped_to_authenticated_user():
    engine = make_db()
    with Session(engine) as db:
        owner = User(username="owner", password_hash="test")
        other = User(username="other", password_hash="test")
        db.add_all([owner, other])
        db.flush()

        owner_card = Card(
            user_id=owner.id, name="Cartão do dono", limit_cents=80_000,
            closing_day=25, due_day=5, color="#247a57",
        )
        other_card = Card(
            user_id=other.id, name="Cartão de outra conta", limit_cents=90_000,
            closing_day=25, due_day=5, color="#247a57",
        )
        db.add_all([owner_card, other_card])
        db.flush()

        owner_category = Category(
            user_id=owner.id, name="Compras", color="#78a88b", icon="tag",
        )
        other_category = Category(
            user_id=other.id, name="Compras", color="#78a88b", icon="tag",
        )
        db.add_all([owner_category, other_category])
        db.flush()

        for account, card, category, description in (
            (owner, owner_card, owner_category, "Compra do dono"),
            (other, other_card, other_category, "Compra de outra conta"),
        ):
            purchase = Purchase(
                user_id=account.id,
                description=description,
                kind="avista",
                direction="expense",
                purchase_date=date(2026, 11, 5),
                card_id=card.id,
                category_id=category.id,
                total_cents=10_000,
                installment_count=1,
                first_invoice_month=date(2026, 11, 1),
                current_installment=1,
                active=True,
                notes="",
            )
            db.add(purchase)
            db.flush()
            db.add(InvoiceEntry(
                purchase_id=purchase.id,
                invoice_month=date(2026, 11, 1),
                installment_number=None,
                amount_cents=10_000,
                status="open",
            ))
        db.commit()

        result = dashboard("2026-11", make_request(owner.id), db=db)

        assert [item["id"] for item in result["cards"]] == [owner_card.id]
        assert result["cards"][0]["committed_cents"] == 10_000
        assert result["cards"][0]["available_cents"] == 70_000

    engine.dispose()

def test_dashboard_card_limit_ignores_historical_and_inactive_open_entries():
    engine = make_db()
    with Session(engine) as db:
        user = User(username="limit-owner", password_hash="test")
        db.add(user)
        db.flush()
        card = Card(
            user_id=user.id, name="Cartão", limit_cents=100_000,
            closing_day=25, due_day=5, color="#247a57",
        )
        category = Category(
            user_id=user.id, name="Compras", color="#78a88b", icon="tag",
        )
        db.add_all([card, category])
        db.flush()

        active_purchase = Purchase(
            user_id=user.id, description="Compra ativa", kind="parcelado",
            direction="expense", purchase_date=date(2026, 10, 1),
            card_id=card.id, category_id=category.id, total_cents=40_000,
            installment_count=4, first_invoice_month=date(2026, 10, 1),
            current_installment=1, active=True, notes="",
        )
        inactive_purchase = Purchase(
            user_id=user.id, description="Compra arquivada", kind="avista",
            direction="expense", purchase_date=date(2026, 11, 2),
            card_id=card.id, category_id=category.id, total_cents=50_000,
            installment_count=1, first_invoice_month=date(2026, 11, 1),
            current_installment=1, active=False, notes="",
        )
        db.add_all([active_purchase, inactive_purchase])
        db.flush()

        db.add_all([
            InvoiceEntry(
                purchase_id=active_purchase.id, invoice_month=date(2026, 10, 1),
                installment_number=1, amount_cents=10_000, status="open",
            ),
            InvoiceEntry(
                purchase_id=active_purchase.id, invoice_month=date(2026, 11, 1),
                installment_number=2, amount_cents=10_000, status="open",
            ),
            InvoiceEntry(
                purchase_id=active_purchase.id, invoice_month=date(2026, 12, 1),
                installment_number=3, amount_cents=10_000, status="open",
            ),
            InvoiceEntry(
                purchase_id=inactive_purchase.id, invoice_month=date(2026, 11, 1),
                installment_number=None, amount_cents=50_000, status="open",
            ),
        ])
        db.commit()

        result = dashboard("2026-11", make_request(user.id), db=db)
        summary = next(item for item in result["cards"] if item["id"] == card.id)

        # Only November and later installments from active purchases consume limit.
        assert summary["committed_cents"] == 20_000
        assert summary["available_cents"] == 80_000

    engine.dispose()

