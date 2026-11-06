import pytest
from pydantic import ValidationError

from app.schemas import CardIn, CategoryIn, PurchaseIn


def test_card_name_is_trimmed_and_optional_fields_can_be_empty():
    card = CardIn(name="  Nubank principal  ", issuer="  Nubank ", brand=" ")
    assert card.name == "Nubank principal"
    assert card.issuer == "Nubank"
    assert card.brand == ""


def test_card_rejects_whitespace_only_name():
    with pytest.raises(ValidationError):
        CardIn(name="   ")


def test_category_name_and_icon_are_normalized():
    category = CategoryIn(name="  Pets  ", icon=" tag ")
    assert category.name == "Pets"
    assert category.icon == "tag"


def test_category_rejects_blank_name_or_icon():
    with pytest.raises(ValidationError):
        CategoryIn(name="   ")
    with pytest.raises(ValidationError):
        CategoryIn(name="Pets", icon="   ")


def test_purchase_description_and_notes_are_trimmed():
    purchase = PurchaseIn(
        description="  Mercado  ",
        kind="avista",
        purchase_date="2026-11-06",
        card_id=1,
        category_id=1,
        amount_cents=1250,
        notes="  compra de casa  ",
    )
    assert purchase.description == "Mercado"
    assert purchase.notes == "compra de casa"


def test_purchase_rejects_whitespace_only_description():
    with pytest.raises(ValidationError):
        PurchaseIn(
            description="   ",
            kind="avista",
            purchase_date="2026-11-06",
            card_id=1,
            category_id=1,
            amount_cents=1250,
        )
