import pytest
from pydantic import ValidationError

from app.schemas import PurchaseUpdateIn


def test_purchase_update_accepts_description_only():
    payload = PurchaseUpdateIn(description="Mercado")
    assert payload.model_dump(exclude_unset=True) == {"description": "Mercado"}


def test_purchase_update_accepts_notes_only():
    payload = PurchaseUpdateIn(notes="Compra feita no débito? Corrigir descrição")
    assert payload.model_dump(exclude_unset=True) == {"notes": "Compra feita no débito? Corrigir descrição"}


def test_purchase_update_rejects_empty_payload():
    with pytest.raises(ValidationError):
        PurchaseUpdateIn()


def test_purchase_update_rejects_blank_description():
    with pytest.raises(ValidationError):
        PurchaseUpdateIn(description="   ")
