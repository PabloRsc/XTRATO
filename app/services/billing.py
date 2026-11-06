from __future__ import annotations

import calendar
import re
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Card, InvoiceEntry, Purchase


def parse_month(value: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
        raise ValueError("Mês inválido. Use AAAA-MM.")
    year, month = (int(part) for part in value.split("-", 1))
    return date(year, month, 1)


def month_key(value: date) -> str:
    return value.strftime("%Y-%m")


def add_months(value: date, count: int) -> date:
    absolute = value.year * 12 + (value.month - 1) + count
    year, month0 = divmod(absolute, 12)
    month = month0 + 1
    return date(year, month, 1)


def month_from_purchase_date(purchase_date: date, closing_day: int, due_month_offset: int = 1) -> date:
    """Suggest the month the invoice is paid using the card's explicit cycle setting.

    due_month_offset is 0 when the invoice is paid in the closing month, or 1
    when it is paid in the following month. The user can override the suggestion
    on an individual purchase to match the issuer's actual statement.
    """
    if not 1 <= closing_day <= 31:
        raise ValueError("Dia de fechamento inválido.")
    if due_month_offset not in (0, 1):
        raise ValueError("O mês de vencimento deve ser o mesmo ou o seguinte ao fechamento.")
    base = date(purchase_date.year, purchase_date.month, 1)
    statement_offset = 1 if purchase_date.day > closing_day else 0
    return add_months(base, statement_offset + due_month_offset)


def budget_usage_percentage(net_spent_cents: int, limit_cents: int) -> float:
    """Return non-negative percentage of the monthly budget consumed."""
    if limit_cents < 0:
        raise ValueError("O limite mensal não pode ser negativo.")
    if net_spent_cents < 0:
        net_spent_cents = 0
    if limit_cents == 0:
        return 100.0 if net_spent_cents > 0 else 0.0
    return round((net_spent_cents / limit_cents) * 100, 1)


def signed_entry_amount(amount_cents: int, direction: str) -> int:
    """Return a purchase as positive spending or a credit as a reduction."""
    if amount_cents < 0:
        raise ValueError("O valor do lançamento não pode ser negativo.")
    if direction == "expense":
        return amount_cents
    if direction == "credit":
        return -amount_cents
    raise ValueError("Tipo de movimentação inválido.")


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


def cancel_purchase_entries(purchase: Purchase, from_month: date) -> int:
    """Cancel current and future invoice entries, keeping earlier history intact."""
    cancelled = 0
    for entry in purchase.entries:
        if entry.invoice_month >= from_month and entry.status != "cancelled":
            entry.status = "cancelled"
            cancelled += 1
    purchase.active = False
    return cancelled


def card_suggested_invoice_month(db: Session, card_id: int, purchase_date: date) -> date:
    card = db.get(Card, card_id)
    if card is None:
        return date(purchase_date.year, purchase_date.month, 1)
    return month_from_purchase_date(purchase_date, card.closing_day, card.due_month_offset)


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
