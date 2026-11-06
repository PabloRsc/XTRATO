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
