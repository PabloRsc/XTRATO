from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


class BackupCardIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=60)
    issuer: str = Field(default="", max_length=60)
    brand: str = Field(default="", max_length=30)
    last_four: str | None = Field(default=None, pattern=r"^\\d{4}$")
    closing_day: int = Field(ge=1, le=31)
    due_day: int = Field(ge=1, le=31)
    due_month_offset: int = Field(ge=0, le=1, default=1)
    color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    active: bool


class BackupCategoryIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str = Field(max_length=30)
    active: bool


class BackupBudgetIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int = Field(gt=0)
    month: date
    limit_cents: int = Field(ge=0, le=100_000_000)

    @model_validator(mode="after")
    def month_must_be_first_day(self):
        if self.month.day != 1:
            raise ValueError("O mês do limite deve usar o primeiro dia.")
        return self


class BackupPurchaseIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int = Field(gt=0)
    description: str = Field(min_length=1, max_length=100)
    kind: Literal["avista", "parcelado", "recorrente"]
    direction: Literal["expense", "credit"]
    purchase_date: date
    card_id: int = Field(gt=0)
    category_id: int = Field(gt=0)
    total_cents: int = Field(gt=0, le=4_800_000_000)
    installment_count: int = Field(ge=1, le=48)
    first_invoice_month: date
    current_installment: int = Field(ge=1, le=48)
    end_invoice_month: date | None = None
    active: bool
    notes: str = Field(default="", max_length=300)
    created_at: datetime | None = None

    @model_validator(mode="after")
    def validate_dates_and_kind(self):
        if self.first_invoice_month.day != 1:
            raise ValueError("O mês inicial da compra deve usar o primeiro dia.")
        if self.end_invoice_month and self.end_invoice_month.day != 1:
            raise ValueError("O mês final da recorrência deve usar o primeiro dia.")
        if self.kind == "parcelado" and self.installment_count < 2:
            raise ValueError("Parcelamentos precisam ter ao menos duas parcelas.")
        if self.kind != "recorrente" and self.end_invoice_month is not None:
            raise ValueError("Apenas despesas fixas podem ter mês final.")
        if self.kind == "recorrente" and self.direction != "expense":
            raise ValueError("Créditos não podem ser recorrentes.")
        if self.current_installment > self.installment_count:
            raise ValueError("A parcela atual excede o total de parcelas.")
        return self


class BackupInvoiceEntryIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int = Field(gt=0)
    purchase_id: int = Field(gt=0)
    invoice_month: date
    installment_number: int | None = Field(default=None, ge=1, le=48)
    amount_cents: int = Field(gt=0, le=4_800_000_000)
    status: Literal["open", "historical", "cancelled"]

    @model_validator(mode="after")
    def month_must_be_first_day(self):
        if self.invoice_month.day != 1:
            raise ValueError("O mês da parcela deve usar o primeiro dia.")
        return self


class BackupAccountIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=80)


class BackupRestoreIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirmation: Literal["RESTAURAR"]
    format: Literal["xtrato-backup"]
    version: Literal[1]
    exported_at: datetime
    account: BackupAccountIn
    cards: list[BackupCardIn] = Field(max_length=50)
    categories: list[BackupCategoryIn] = Field(max_length=200)
    budgets: list[BackupBudgetIn] = Field(max_length=600)
    purchases: list[BackupPurchaseIn] = Field(max_length=10_000)
    invoice_entries: list[BackupInvoiceEntryIn] = Field(max_length=50_000)

    @model_validator(mode="after")
    def validate_backup_relationships(self):
        ids = {
            "cards": [row.id for row in self.cards],
            "categories": [row.id for row in self.categories],
            "budgets": [row.id for row in self.budgets],
            "purchases": [row.id for row in self.purchases],
            "invoice_entries": [row.id for row in self.invoice_entries],
        }
        for name, values in ids.items():
            if len(values) != len(set(values)):
                raise ValueError(f"O backup contém IDs duplicados em {name}.")

        card_ids = set(ids["cards"])
        category_ids = set(ids["categories"])
        purchase_ids = set(ids["purchases"])
        for purchase in self.purchases:
            if purchase.card_id not in card_ids or purchase.category_id not in category_ids:
                raise ValueError("Uma compra aponta para cartão ou categoria inexistente.")
        entry_purchase_ids = []
        entries_by_purchase: dict[int, list[BackupInvoiceEntryIn]] = {}
        for entry in self.invoice_entries:
            if entry.purchase_id not in purchase_ids:
                raise ValueError("Uma parcela aponta para uma compra inexistente.")
            entries_by_purchase.setdefault(entry.purchase_id, []).append(entry)

        for purchase in self.purchases:
            rows = sorted(entries_by_purchase.get(purchase.id, []), key=lambda row: row.invoice_month)
            if purchase.kind == "recorrente":
                if any(row.installment_number is not None for row in rows):
                    raise ValueError("Despesas fixas não podem ter número de parcela.")
                if any(row.invoice_month < purchase.first_invoice_month for row in rows):
                    raise ValueError("Uma cobrança recorrente antecede seu início.")
                if purchase.end_invoice_month and any(row.invoice_month > purchase.end_invoice_month for row in rows):
                    raise ValueError("Uma cobrança recorrente ultrapassa seu mês final.")
                if any(row.amount_cents != purchase.total_cents for row in rows):
                    raise ValueError("O valor de uma cobrança recorrente não corresponde ao cadastro.")
            else:
                if len(rows) != purchase.installment_count:
                    raise ValueError("O backup não contém todas as parcelas de uma compra.")
                if sum(row.amount_cents for row in rows) != purchase.total_cents:
                    raise ValueError("A soma das parcelas não corresponde ao valor total da compra.")
                for index, row in enumerate(rows, start=1):
                    expected_month = purchase.first_invoice_month.replace(
                        year=(purchase.first_invoice_month.year + (purchase.first_invoice_month.month - 1 + index - 1) // 12),
                        month=((purchase.first_invoice_month.month - 1 + index - 1) % 12) + 1,
                    )
                    if row.invoice_month != expected_month:
                        raise ValueError("Os meses das parcelas não são consecutivos.")
                    expected_number = index if purchase.kind == "parcelado" else None
                    if row.installment_number != expected_number:
                        raise ValueError("A numeração das parcelas não corresponde à compra.")
            months = [row.invoice_month for row in rows]
            if len(months) != len(set(months)):
                raise ValueError("O backup contém parcelas duplicadas no mesmo mês.")
        return self
