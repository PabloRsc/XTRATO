from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import local_today
from app.database import get_db
from app.deps import authenticated_user
from app.models import Budget, Card, Category, InvoiceEntry, Purchase
from app.schemas import BudgetIn, PurchaseIn, PurchaseUpdateIn
from app.services.billing import (
    add_months, card_suggested_invoice_month, cancel_purchase_entries, create_invoice_entries,
    ensure_recurring_entries, parse_month, query_month_entries,
)

router = APIRouter(prefix="/api", tags=["financeiro"])


def _month_payload(value: str) -> date:
    try:
        return parse_month(value)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Mês inválido. Use AAAA-MM.")


def _entry_dict(db: Session, entry: InvoiceEntry, purchase: Purchase, card: Card):
    category = db.get(Category, purchase.category_id)
    return {
        "entry_id": entry.id,
        "purchase_id": purchase.id,
        "description": purchase.description,
        "purchase_date": purchase.purchase_date.isoformat(),
        "invoice_month": entry.invoice_month.strftime("%Y-%m"),
        "amount_cents": entry.amount_cents,
        "direction": purchase.direction,
        "kind": purchase.kind,
        "installment_number": entry.installment_number,
        "installment_count": purchase.installment_count if purchase.kind == "parcelado" else None,
        "entry_status": entry.status,
        "card_id": card.id,
        "card_name": card.name,
        "card_color": card.color,
        "category_id": category.id if category else None,
        "category_name": category.name if category else "Categoria removida",
        "category_color": category.color if category else "#9aa39b",
        "category_icon": category.icon if category else "tag",
        "notes": purchase.notes,
        "purchase_active": purchase.active,
    }


@router.get("/dashboard")
def dashboard(month: str, request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    selected = _month_payload(month)
    ensure_recurring_entries(db, user.id, add_months(selected, 12))
    db.commit()
    rows = query_month_entries(db, user.id, selected)
    total = sum((entry.amount_cents if purchase.direction == "expense" else -entry.amount_cents) for entry, purchase, _card in rows)
    expense_total = sum(entry.amount_cents for entry, purchase, _card in rows if purchase.direction == "expense")
    credits_total = sum(entry.amount_cents for entry, purchase, _card in rows if purchase.direction == "credit")

    budget = db.scalar(
        select(Budget)
        .where(Budget.user_id == user.id, Budget.month <= selected)
        .order_by(Budget.month.desc())
        .limit(1)
    )
    limit_cents = budget.limit_cents if budget else None

    card_totals: dict[int, dict] = {}
    category_totals: dict[int, dict] = {}
    for entry, purchase, card in rows:
        sign = 1 if purchase.direction == "expense" else -1
        card_row = card_totals.setdefault(card.id, {"id": card.id, "name": card.name, "color": card.color, "total_cents": 0})
        card_row["total_cents"] += sign * entry.amount_cents
        category = db.get(Category, purchase.category_id)
        if category:
            cat_row = category_totals.setdefault(category.id, {"id": category.id, "name": category.name, "color": category.color, "icon": category.icon, "total_cents": 0})
            cat_row["total_cents"] += sign * entry.amount_cents

    trends = []
    for offset in range(5, -1, -1):
        trend_month = add_months(selected, -offset)
        trend_rows = query_month_entries(db, user.id, trend_month)
        amount = sum((e.amount_cents if p.direction == "expense" else -e.amount_cents) for e, p, _c in trend_rows)
        trends.append({"month": trend_month.strftime("%Y-%m"), "label": trend_month.strftime("%b").replace("Jan", "Jan").replace("Feb", "Fev").replace("Mar", "Mar").replace("Apr", "Abr").replace("May", "Mai").replace("Jun", "Jun").replace("Jul", "Jul").replace("Aug", "Ago").replace("Sep", "Set").replace("Oct", "Out").replace("Nov", "Nov").replace("Dec", "Dez"), "total_cents": amount})

    cards = db.scalars(select(Card).where(Card.user_id == user.id, Card.active.is_(True)).order_by(Card.name)).all()
    entries = [_entry_dict(db, e, p, c) for e, p, c in rows]
    return {
        "month": month,
        "spent_cents": total,
        "expenses_cents": expense_total,
        "credits_cents": credits_total,
        "limit_cents": limit_cents,
        "limit_effective_from": budget.month.strftime("%Y-%m") if budget else None,
        "available_cents": (limit_cents - total) if limit_cents is not None else None,
        "percentage": (round((total / limit_cents) * 100, 1) if limit_cents > 0 else (100.0 if total > 0 else 0.0)) if limit_cents is not None else None,
        "cards": [{"id": c.id, "name": c.name, "color": c.color, "total_cents": card_totals.get(c.id, {}).get("total_cents", 0)} for c in cards],
        "card_totals": list(card_totals.values()),
        "categories": sorted(category_totals.values(), key=lambda x: x["total_cents"], reverse=True),
        "trend": trends,
        "recent_entries": entries[:8],
    }


@router.get("/entries")
def list_entries(month: str, request: Request, card_id: int | None = None, q: str | None = None, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    selected = _month_payload(month)
    ensure_recurring_entries(db, user.id, selected)
    db.commit()
    rows = query_month_entries(db, user.id, selected, card_id=card_id, search=q)
    return [_entry_dict(db, e, p, c) for e, p, c in rows]


@router.post("/purchases", status_code=201)
def create_purchase(payload: PurchaseIn, request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    card = db.scalar(select(Card).where(Card.id == payload.card_id, Card.user_id == user.id, Card.active.is_(True)))
    if not card:
        raise HTTPException(status_code=422, detail="Selecione um cartão ativo cadastrado na sua conta.")
    category = db.scalar(select(Category).where(Category.id == payload.category_id, Category.user_id == user.id, Category.active.is_(True)))
    if not category:
        raise HTTPException(status_code=422, detail="Selecione uma categoria ativa cadastrada na sua conta.")

    ongoing = payload.ongoing and payload.kind == "parcelado"
    if ongoing:
        current_month = _month_payload(payload.current_invoice_month or "")
        first_month = add_months(current_month, -(payload.current_installment - 1))
    elif payload.first_invoice_month:
        first_month = _month_payload(payload.first_invoice_month)
    else:
        first_month = card_suggested_invoice_month(db, card.id, payload.purchase_date)

    count = payload.installment_count if payload.kind == "parcelado" else 1
    if payload.kind == "recorrente":
        total_cents = payload.amount_cents
    elif ongoing and payload.value_mode == "installment":
        total_cents = payload.amount_cents * count
    else:
        total_cents = payload.amount_cents

    if payload.kind == "parcelado" and total_cents < count:
        raise HTTPException(status_code=422, detail="O valor total é insuficiente para a quantidade de parcelas.")

    end_month = _month_payload(payload.end_invoice_month) if payload.end_invoice_month else None
    if payload.kind == "recorrente" and end_month and end_month < first_month:
        raise HTTPException(status_code=422, detail="O término da recorrência deve ser posterior ao início.")

    purchase = Purchase(
        user_id=user.id,
        description=payload.description.strip(),
        kind=payload.kind,
        direction=payload.direction,
        purchase_date=payload.purchase_date,
        card_id=card.id,
        category_id=category.id,
        total_cents=total_cents,
        installment_count=count,
        first_invoice_month=first_month,
        current_installment=payload.current_installment if ongoing else 1,
        end_invoice_month=end_month,
        notes=payload.notes.strip(),
    )
    db.add(purchase)
    db.flush()
    if payload.kind != "recorrente":
        create_invoice_entries(db, purchase, ongoing=ongoing)
    else:
        # Materialize the first 12 months; later months are generated idempotently on demand.
        ensure_recurring_entries(db, user.id, add_months(first_month, 11))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Não foi possível registrar essa compra. Revise os dados.")
    db.refresh(purchase)
    return {"id": purchase.id, "message": "Compra registrada."}


@router.patch("/purchases/{purchase_id}")
def update_purchase(purchase_id: int, payload: PurchaseUpdateIn, request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    purchase = db.scalar(select(Purchase).where(
        Purchase.id == purchase_id,
        Purchase.user_id == user.id,
        Purchase.active.is_(True),
    ))
    if not purchase:
        raise HTTPException(status_code=404, detail="Compra não encontrada ou já cancelada.")

    values = payload.model_dump(exclude_unset=True)
    if "description" in values:
        description = (values["description"] or "").strip()
        if not description:
            raise HTTPException(status_code=422, detail="A descrição não pode ficar vazia.")
        purchase.description = description
    if "notes" in values:
        purchase.notes = (values["notes"] or "").strip()

    db.commit()
    return {"ok": True, "message": "Descrição e observações atualizadas."}


@router.post("/purchases/{purchase_id}/cancel")
def cancel_purchase(purchase_id: int, request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    purchase = db.scalar(select(Purchase).where(Purchase.id == purchase_id, Purchase.user_id == user.id, Purchase.active.is_(True)))
    if not purchase:
        raise HTTPException(status_code=404, detail="Compra não encontrada ou já cancelada.")
    current_month = local_today().replace(day=1)
    cancel_purchase_entries(purchase, current_month)
    db.commit()
    return {"ok": True, "message": "Lançamentos atuais e futuros cancelados. Histórico anterior preservado."}


@router.put("/budgets")
def save_budget(payload: BudgetIn, request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    month = _month_payload(payload.month)
    budget = db.scalar(select(Budget).where(Budget.user_id == user.id, Budget.month == month))
    if budget:
        budget.limit_cents = payload.limit_cents
    else:
        budget = Budget(user_id=user.id, month=month, limit_cents=payload.limit_cents)
        db.add(budget)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Não foi possível salvar o limite deste mês.")
    return {"ok": True, "limit_cents": budget.limit_cents}


@router.get("/recurrences")
def list_recurrences(request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    rows = db.execute(
        select(Purchase, Card, Category)
        .join(Card, Card.id == Purchase.card_id)
        .join(Category, Category.id == Purchase.category_id)
        .where(Purchase.user_id == user.id, Purchase.kind == "recorrente")
        .order_by(Purchase.active.desc(), Purchase.description.asc())
    ).all()
    return [{
        "id": p.id,
        "description": p.description,
        "amount_cents": p.total_cents,
        "card_name": c.name,
        "category_name": cat.name,
        "notes": p.notes,
        "first_invoice_month": p.first_invoice_month.strftime("%Y-%m"),
        "end_invoice_month": p.end_invoice_month.strftime("%Y-%m") if p.end_invoice_month else None,
        "active": p.active,
    } for p, c, cat in rows]
