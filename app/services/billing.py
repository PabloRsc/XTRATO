from __future__ import annotations

import calendar
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Card, InvoiceEntry, Purchase


def parse_month(value: str) -> date:
    year, month = (int(part) for part in value.split("-", 1))
    if month < 1 or month > 12:
        raise ValueError("Mês inválido.")
    return date(year, month, 1)


def month_key(value: date) -> str:
    return value.strftime("%Y-%m")


def add_months(value: date, count: int) -> date:
    absolute = value.year * 12 + (value.month - 1) + count
    year, month0 = divmod(absolute, 12)
    month = month0 + 1
    return date(year, month, 1)


def month_from_purchase_date(purchase_date: date, closing_day: int, due_day: int) -> date:
    """Suggest the month the invoice is paid, using both closing and due days.

    Purchases after closing move to the next statement cycle. The payment month
    is the closing month when the due day is after the closing day; otherwise
    payment happens in the following calendar month.
    """
    base = date(purchase_date.year, purchase_date.month, 1)
    statement_offset = 1 if purchase_date.day > closing_day else 0
    payment_offset = 1 if due_day <= closing_day else 0
    return add_months(base, statement_offset + payment_offset)


def split_amount(total_cents: int, parts: int) -> list[int]:
    """Split integer cents exactly; any remainder is placed in the final installment."""
    base, remainder = divmod(total_cents, parts)
    return [base] * (parts - 1) + [base + remainder]


def create_invoice_entries(db: Session, purchase: Purchase, ongoing: bool = False) -> None:
    if purchase.kind == "recorrente":
        return
    values = split_amount(purchase.total_cents, purchase.installment_count)
    for index, amount in enumerate(values, start=1):
        invoice_month = add_months(purchase.first_invoice_month, index - 1)
        status = "historical" if ongoing and index < purchase.current_installment else "open"
        db.add(InvoiceEntry(
            purchase_id=purchase.id,
            invoice_month=invoice_month,
            installment_number=index if purchase.kind == "parcelado" else None,
            amount_cents=amount,
            status=status,
        ))


def ensure_recurring_entries(db: Session, user_id: int, through_month: date) -> None:
    recurrences = db.scalars(select(Purchase).where(
        Purchase.user_id == user_id,
        Purchase.kind == "recorrente",
        Purchase.active.is_(True),
        Purchase.first_invoice_month <= through_month,
    )).all()
    for purchase in recurrences:
        final_month = min(purchase.end_invoice_month, through_month) if purchase.end_invoice_month else through_month
        cursor = purchase.first_invoice_month
        while cursor <= final_month:
            existing = db.scalar(select(InvoiceEntry.id).where(
                InvoiceEntry.purchase_id == purchase.id,
                InvoiceEntry.invoice_month == cursor,
            ))
            if existing is None:
                db.add(InvoiceEntry(
                    purchase_id=purchase.id,
                    invoice_month=cursor,
                    installment_number=None,
                    amount_cents=purchase.total_cents,
                    status="open",
                ))
            cursor = add_months(cursor, 1)
    db.flush()


def card_suggested_invoice_month(db: Session, card_id: int, purchase_date: date) -> date:
    card = db.get(Card, card_id)
    if card is None:
        return date(purchase_date.year, purchase_date.month, 1)
    return month_from_purchase_date(purchase_date, card.closing_day, card.due_day)


def query_month_entries(db: Session, user_id: int, month: date, card_id: int | None = None, search: str | None = None):
    stmt = (
        select(InvoiceEntry, Purchase, Card)
        .join(Purchase, Purchase.id == InvoiceEntry.purchase_id)
        .join(Card, Card.id == Purchase.card_id)
        .where(
            Purchase.user_id == user_id,
            InvoiceEntry.invoice_month == month,
            InvoiceEntry.status != "cancelled",
        )
        .order_by(Purchase.purchase_date.desc(), InvoiceEntry.id.desc())
    )
    if card_id:
        stmt = stmt.where(Purchase.card_id == card_id)
    if search:
        stmt = stmt.where(Purchase.description.ilike(f"%{search.strip()}%"))
    return db.execute(stmt).all()
