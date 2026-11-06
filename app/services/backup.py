from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Budget, Card, Category, InvoiceEntry, Purchase, User


def _iso(value: date | datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def build_user_backup(db: Session, user: User) -> dict:
    """Build a portable backup containing the user's financial data only.

    Password hashes and session/authentication data are intentionally excluded.
    Database IDs are retained so relationships can be reconstructed on restore.
    """
    cards = db.scalars(
        select(Card).where(Card.user_id == user.id).order_by(Card.id)
    ).all()
    categories = db.scalars(
        select(Category).where(Category.user_id == user.id).order_by(Category.id)
    ).all()
    budgets = db.scalars(
        select(Budget).where(Budget.user_id == user.id).order_by(Budget.month)
    ).all()
    purchases = db.scalars(
        select(Purchase).where(Purchase.user_id == user.id).order_by(Purchase.id)
    ).all()
    purchase_ids = [purchase.id for purchase in purchases]
    entries = (
        db.scalars(
            select(InvoiceEntry)
            .where(InvoiceEntry.purchase_id.in_(purchase_ids))
            .order_by(InvoiceEntry.invoice_month, InvoiceEntry.id)
        ).all()
        if purchase_ids
        else []
    )

    return {
        "format": "xtrato-backup",
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "account": {"username": user.username},
        "cards": [
            {
                "id": card.id,
                "name": card.name,
                "issuer": card.issuer,
                "brand": card.brand,
                "last_four": card.last_four,
                "closing_day": card.closing_day,
                "due_day": card.due_day,
                "due_month_offset": card.due_month_offset,
                "color": card.color,
                "active": card.active,
            }
            for card in cards
        ],
        "categories": [
            {
                "id": category.id,
                "name": category.name,
                "color": category.color,
                "icon": category.icon,
                "active": category.active,
            }
            for category in categories
        ],
        "budgets": [
            {
                "id": budget.id,
                "month": _iso(budget.month),
                "limit_cents": budget.limit_cents,
            }
            for budget in budgets
        ],
        "purchases": [
            {
                "id": purchase.id,
                "description": purchase.description,
                "kind": purchase.kind,
                "direction": purchase.direction,
                "purchase_date": _iso(purchase.purchase_date),
                "card_id": purchase.card_id,
                "category_id": purchase.category_id,
                "total_cents": purchase.total_cents,
                "installment_count": purchase.installment_count,
                "first_invoice_month": _iso(purchase.first_invoice_month),
                "current_installment": purchase.current_installment,
                "end_invoice_month": _iso(purchase.end_invoice_month),
                "active": purchase.active,
                "notes": purchase.notes,
                "created_at": _iso(purchase.created_at),
            }
            for purchase in purchases
        ],
        "invoice_entries": [
            {
                "id": entry.id,
                "purchase_id": entry.purchase_id,
                "invoice_month": _iso(entry.invoice_month),
                "installment_number": entry.installment_number,
                "amount_cents": entry.amount_cents,
                "status": entry.status,
            }
            for entry in entries
        ],
    }


def restore_user_backup(db: Session, user: User, payload) -> dict:
    """Restore a validated backup into an account with no financial records.

    New database IDs are allocated during restore and source IDs are mapped to
    them. This preserves all relationships without colliding with IDs owned by
    other accounts in the destination database.
    """
    from sqlalchemy import func

    from app.models import Budget, Card, Category, InvoiceEntry, Purchase

    has_financial_data = any([
        db.scalar(select(func.count()).select_from(Card).where(Card.user_id == user.id)),
        db.scalar(select(func.count()).select_from(Budget).where(Budget.user_id == user.id)),
        db.scalar(select(func.count()).select_from(Purchase).where(Purchase.user_id == user.id)),
    ])
    if has_financial_data:
        raise ValueError(
            "A restauração só está disponível em uma conta sem cartões, compras ou limites cadastrados."
        )

    # Default/custom categories in this empty account can be replaced safely.
    db.query(Category).filter(Category.user_id == user.id).delete(synchronize_session=False)

    card_ids: dict[int, int] = {}
    category_ids: dict[int, int] = {}
    purchase_ids: dict[int, int] = {}

    for item in payload.cards:
        card = Card(
            user_id=user.id,
            name=item.name,
            issuer=item.issuer,
            brand=item.brand,
            last_four=item.last_four,
            closing_day=item.closing_day,
            due_day=item.due_day,
            due_month_offset=item.due_month_offset,
            color=item.color,
            active=item.active,
        )
        db.add(card)
        db.flush()
        card_ids[item.id] = card.id

    for item in payload.categories:
        category = Category(
            user_id=user.id,
            name=item.name,
            color=item.color,
            icon=item.icon,
            active=item.active,
        )
        db.add(category)
        db.flush()
        category_ids[item.id] = category.id

    for item in payload.budgets:
        db.add(Budget(
            user_id=user.id,
            month=item.month,
            limit_cents=item.limit_cents,
        ))

    for item in payload.purchases:
        purchase = Purchase(
            user_id=user.id,
            description=item.description,
            kind=item.kind,
            direction=item.direction,
            purchase_date=item.purchase_date,
            card_id=card_ids[item.card_id],
            category_id=category_ids[item.category_id],
            total_cents=item.total_cents,
            installment_count=item.installment_count,
            first_invoice_month=item.first_invoice_month,
            current_installment=item.current_installment,
            end_invoice_month=item.end_invoice_month,
            active=item.active,
            notes=item.notes,
            created_at=item.created_at,
        )
        db.add(purchase)
        db.flush()
        purchase_ids[item.id] = purchase.id

    for item in payload.invoice_entries:
        db.add(InvoiceEntry(
            purchase_id=purchase_ids[item.purchase_id],
            invoice_month=item.invoice_month,
            installment_number=item.installment_number,
            amount_cents=item.amount_cents,
            status=item.status,
        ))
    db.flush()

    return {
        "cards": len(payload.cards),
        "categories": len(payload.categories),
        "budgets": len(payload.budgets),
        "purchases": len(payload.purchases),
        "invoice_entries": len(payload.invoice_entries),
    }
