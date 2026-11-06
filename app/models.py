from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer,
    String, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    session_version: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    cards: Mapped[list["Card"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    categories: Mapped[list["Category"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Card(Base):
    __tablename__ = "cards"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_card_user_name"),
        CheckConstraint("closing_day >= 1 AND closing_day <= 31", name="ck_card_closing_day"),
        CheckConstraint("due_day >= 1 AND due_day <= 31", name="ck_card_due_day"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    limit_cents: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0", nullable=False)
    issuer: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    brand: Mapped[str] = mapped_column(String(30), default="", nullable=False)
    last_four: Mapped[str | None] = mapped_column(String(4), nullable=True)
    closing_day: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    due_day: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    due_month_offset: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#247a57", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    user: Mapped[User] = relationship(back_populates="cards")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_category_user_name"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#78a88b", nullable=False)
    icon: Mapped[str] = mapped_column(String(30), default="tag", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    user: Mapped[User] = relationship(back_populates="categories")


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("user_id", "month", name="uq_budget_user_month"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    month: Mapped[date] = mapped_column(Date, nullable=False)
    limit_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)


class Purchase(Base):
    __tablename__ = "purchases"
    __table_args__ = (
        CheckConstraint("kind IN ('avista', 'parcelado', 'recorrente')", name="ck_purchase_kind"),
        CheckConstraint("direction IN ('expense', 'credit')", name="ck_purchase_direction"),
        CheckConstraint("total_cents > 0", name="ck_purchase_total_positive"),
        Index("ix_purchase_user_date", "user_id", "purchase_date"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    kind: Mapped[str] = mapped_column(String(15), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), default="expense", nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id", ondelete="RESTRICT"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    total_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    installment_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    first_invoice_month: Mapped[date] = mapped_column(Date, nullable=False)
    current_installment: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    end_invoice_month: Mapped[date | None] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    entries: Mapped[list["InvoiceEntry"]] = relationship(back_populates="purchase", cascade="all, delete-orphan")


class InvoiceEntry(Base):
    __tablename__ = "invoice_entries"
    __table_args__ = (
        UniqueConstraint("purchase_id", "invoice_month", name="uq_entry_purchase_month"),
        CheckConstraint("amount_cents > 0", name="ck_entry_amount_positive"),
        CheckConstraint("status IN ('open', 'historical', 'cancelled')", name="ck_entry_status"),
        Index("ix_entry_invoice_month", "invoice_month"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_month: Mapped[date] = mapped_column(Date, nullable=False)
    installment_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(15), default="open", nullable=False)
    purchase: Mapped[Purchase] = relationship(back_populates="entries")
