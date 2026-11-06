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



def test_card_accepts_both_payment_month_offsets():
    assert CardIn(name="Nubank", due_month_offset=0).due_month_offset == 0
    assert CardIn(name="Inter", due_month_offset=1).due_month_offset == 1


def test_card_rejects_invalid_payment_month_offset():
    with pytest.raises(ValidationError):
        CardIn(name="Nubank", due_month_offset=2)



def test_production_configuration_rejects_example_secrets_and_weak_passwords():
    from app.config import validate_production_settings

    with pytest.raises(RuntimeError):
        validate_production_settings("production", "local-development-key-change-before-production", True, "correct horse battery")
    with pytest.raises(RuntimeError):
        validate_production_settings("production", "a" * 48, True, "CHANGE_ME_USE_A_UNIQUE_PASSWORD")
    with pytest.raises(RuntimeError):
        validate_production_settings("production", "a" * 48, False, "a-strong-initial-password")


def test_production_configuration_accepts_unique_secret_and_strong_password():
    from app.config import validate_production_settings

    validate_production_settings("production", "c" * 48, True, "a-strong-initial-password")
    validate_production_settings("development", "short", False, "dev")


def test_credit_cannot_be_recurring_or_ongoing():
    base = {
        "description": "Estorno",
        "kind": "recorrente",
        "direction": "credit",
        "purchase_date": "2026-11-06",
        "card_id": 1,
        "category_id": 1,
        "amount_cents": 2500,
        "first_invoice_month": "2026-11",
    }
    with pytest.raises(ValidationError):
        PurchaseIn(**base)

    ongoing = {
        "description": "Estorno parcelado",
        "kind": "parcelado",
        "direction": "credit",
        "purchase_date": "2026-11-06",
        "card_id": 1,
        "category_id": 1,
        "amount_cents": 2500,
        "installment_count": 2,
        "ongoing": True,
        "current_installment": 1,
        "current_invoice_month": "2026-11",
    }
    with pytest.raises(ValidationError):
        PurchaseIn(**ongoing)


def test_installment_value_mode_requires_ongoing_installment_purchase():
    payload = {
        "description": "Compra",
        "kind": "parcelado",
        "purchase_date": "2026-11-06",
        "card_id": 1,
        "category_id": 1,
        "amount_cents": 2500,
        "installment_count": 2,
        "value_mode": "installment",
    }
    with pytest.raises(ValidationError):
        PurchaseIn(**payload)

    payload["ongoing"] = True
    payload["current_installment"] = 1
    payload["current_invoice_month"] = "2026-11"
    assert PurchaseIn(**payload).value_mode == "installment"


def test_end_invoice_month_is_only_allowed_for_recurring_purchases():
    payload = {
        "description": "Compra",
        "kind": "avista",
        "purchase_date": "2026-11-06",
        "card_id": 1,
        "category_id": 1,
        "amount_cents": 2500,
        "end_invoice_month": "2027-01",
    }
    with pytest.raises(ValidationError):
        PurchaseIn(**payload)
