from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import local_today
from app.database import get_db
from app.deps import authenticated_user
from app.models import Card, Category
from app.schemas import BackupRestoreIn, CardIn, CategoryIn
from app.services.backup import build_user_backup, restore_user_backup

router = APIRouter(prefix="/api", tags=["cadastros"])


def user_or_401(request: Request, db: Session):
    return authenticated_user(request, db)


@router.get("/cards")
def list_cards(request: Request, db: Session = Depends(get_db)):
    user = user_or_401(request, db)
    cards = db.scalars(select(Card).where(Card.user_id == user.id, Card.active.is_(True)).order_by(Card.name)).all()
    return [{"id": c.id, "name": c.name, "issuer": c.issuer, "brand": c.brand, "last_four": c.last_four,
             "closing_day": c.closing_day, "due_day": c.due_day, "due_month_offset": c.due_month_offset, "color": c.color} for c in cards]


@router.post("/cards", status_code=201)
def create_card(payload: CardIn, request: Request, db: Session = Depends(get_db)):
    user = user_or_401(request, db)
    card = Card(user_id=user.id, **payload.model_dump())
    db.add(card)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe um cartão com esse nome.")
    db.refresh(card)
    return {"id": card.id, "name": card.name}


@router.put("/cards/{card_id}")
def update_card(card_id: int, payload: CardIn, request: Request, db: Session = Depends(get_db)):
    user = user_or_401(request, db)
    card = db.scalar(select(Card).where(Card.id == card_id, Card.user_id == user.id, Card.active.is_(True)))
    if not card:
        raise HTTPException(status_code=404, detail="Cartão não encontrado.")
    for key, value in payload.model_dump().items():
        setattr(card, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe um cartão com esse nome.")
    return {"ok": True}


@router.delete("/cards/{card_id}")
def archive_card(card_id: int, request: Request, db: Session = Depends(get_db)):
    user = user_or_401(request, db)
    card = db.scalar(select(Card).where(Card.id == card_id, Card.user_id == user.id, Card.active.is_(True)))
    if not card:
        raise HTTPException(status_code=404, detail="Cartão não encontrado.")
    card.active = False
    db.commit()
    return {"ok": True}


@router.get("/categories")
def list_categories(request: Request, db: Session = Depends(get_db)):
    user = user_or_401(request, db)
    categories = db.scalars(select(Category).where(Category.user_id == user.id, Category.active.is_(True)).order_by(Category.name)).all()
    return [{"id": c.id, "name": c.name, "color": c.color, "icon": c.icon} for c in categories]


@router.post("/categories", status_code=201)
def create_category(payload: CategoryIn, request: Request, db: Session = Depends(get_db)):
    user = user_or_401(request, db)
    category = Category(user_id=user.id, **payload.model_dump())
    db.add(category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe uma categoria com esse nome.")
    db.refresh(category)
    return {"id": category.id, "name": category.name}


@router.put("/categories/{category_id}")
def update_category(category_id: int, payload: CategoryIn, request: Request, db: Session = Depends(get_db)):
    user = user_or_401(request, db)
    category = db.scalar(select(Category).where(Category.id == category_id, Category.user_id == user.id, Category.active.is_(True)))
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    for key, value in payload.model_dump().items():
        setattr(category, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe uma categoria com esse nome.")
    return {"ok": True}


@router.delete("/categories/{category_id}")
def archive_category(category_id: int, request: Request, db: Session = Depends(get_db)):
    user = user_or_401(request, db)
    category = db.scalar(select(Category).where(Category.id == category_id, Category.user_id == user.id, Category.active.is_(True)))
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    category.active = False
    db.commit()
    return {"ok": True}



@router.get("/backup")
def download_backup(request: Request, db: Session = Depends(get_db)):
    user = user_or_401(request, db)
    payload = build_user_backup(db, user)
    filename = f"xtrato-backup-{local_today().isoformat()}.json"
    return JSONResponse(
        content=payload,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        },
    )


@router.post("/backup/restore")
def restore_backup(payload: BackupRestoreIn, request: Request, db: Session = Depends(get_db)):
    user = user_or_401(request, db)
    try:
        restored = restore_user_backup(db, user, payload)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail="O backup contém vínculos incompatíveis ou dados duplicados.",
        )
    return {"ok": True, "restored": restored}
