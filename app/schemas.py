from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class CardIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    issuer: str = Field(default="", max_length=60)
    brand: str = Field(default="", max_length=30)
    last_four: str | None = Field(default=None, pattern=r"^\d{4}$")
    closing_day: int = Field(ge=1, le=31, default=25)
    due_day: int = Field(ge=1, le=31, default=5)
    due_month_offset: int = Field(ge=0, le=1, default=1)
    color: str = Field(default="#247a57", pattern=r"^#[0-9A-Fa-f]{6}$")

    @field_validator("name", "issuer", "brand")
    @classmethod
    def normalize_card_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("name")
    @classmethod
    def require_card_name(cls, value: str) -> str:
        if not value:
            raise ValueError("Informe um nome para o cartão.")
        return value


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(default="#78a88b", pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str = Field(default="tag", max_length=30)

    @field_validator("name", "icon")
    @classmethod
    def normalize_category_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Informe um nome e um ícone válidos para a categoria.")
        return value


class BudgetIn(BaseModel):
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
    limit_cents: int = Field(ge=0, le=100_000_000)


class PurchaseIn(BaseModel):
    description: str = Field(min_length=1, max_length=100)
    kind: Literal["avista", "parcelado", "recorrente"]
    direction: Literal["expense", "credit"] = "expense"
    purchase_date: date
    card_id: int = Field(gt=0)
    category_id: int = Field(gt=0)
    amount_cents: int = Field(gt=0, le=100_000_000)
    value_mode: Literal["total", "installment"] = "total"
    installment_count: int = Field(default=1, ge=1, le=48)
    ongoing: bool = False
    current_installment: int = Field(default=1, ge=1, le=48)
    first_invoice_month: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    current_invoice_month: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    end_invoice_month: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    notes: str = Field(default="", max_length=300)

    @field_validator("description")
    @classmethod
    def normalize_purchase_description(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Informe uma descrição para a compra.")
        return value

    @field_validator("notes")
    @classmethod
    def normalize_purchase_notes(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_purchase(self):
        if self.kind == "avista":
            self.installment_count = 1
            self.ongoing = False
            self.value_mode = "total"
        if self.kind == "parcelado" and self.installment_count < 2:
            raise ValueError("Uma compra parcelada precisa ter pelo menos 2 parcelas.")
        if self.kind == "parcelado" and self.ongoing and self.current_installment > self.installment_count:
            raise ValueError("A parcela atual não pode ser maior que o total de parcelas.")
        if self.kind == "recorrente":
            self.ongoing = False
            self.value_mode = "total"
        if self.direction == "credit" and self.kind == "recorrente":
            raise ValueError("Estornos e créditos não podem ser despesas fixas recorrentes.")
        if self.direction == "credit" and self.ongoing:
            raise ValueError("Um estorno deve ser registrado como crédito novo, não como compra em andamento.")
        if self.value_mode == "installment" and not (self.kind == "parcelado" and self.ongoing):
            raise ValueError("O valor por parcela só pode ser informado para uma compra parcelada em andamento.")
        if self.end_invoice_month and self.kind != "recorrente":
            raise ValueError("A data final só se aplica a despesas fixas recorrentes.")
        if self.ongoing and not self.current_invoice_month:
            raise ValueError("Informe o mês da fatura da parcela atual.")
        if self.kind == "recorrente" and self.first_invoice_month is None:
            raise ValueError("Informe o mês de início da recorrência.")
        if self.end_invoice_month and self.first_invoice_month and self.end_invoice_month < self.first_invoice_month:
            raise ValueError("O fim da recorrência não pode ser anterior ao início.")
        return self


class PurchaseUpdateIn(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def require_editable_field(self):
        if self.description is not None:
            self.description = self.description.strip()
            if not self.description:
                raise ValueError("A descrição não pode ficar vazia.")
        if self.notes is not None:
            self.notes = self.notes.strip()
        if self.description is None and self.notes is None:
            raise ValueError("Informe uma descrição ou observação para atualizar.")
        return self
