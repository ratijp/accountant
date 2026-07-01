from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), default=None)
    phone: Mapped[Optional[str]] = mapped_column(String(30), default=None)
    address: Mapped[Optional[str]] = mapped_column(Text, default=None)
    is_active: Mapped[bool] = mapped_column(default=True)

    sales_orders: Mapped[list[SalesOrder]] = relationship(back_populates="customer")


class Supplier(TimestampMixin, Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), default=None)
    phone: Mapped[Optional[str]] = mapped_column(String(30), default=None)
    address: Mapped[Optional[str]] = mapped_column(Text, default=None)
    is_active: Mapped[bool] = mapped_column(default=True)

    purchase_orders: Mapped[list[PurchaseOrder]] = relationship(back_populates="supplier")


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)

    products: Mapped[list[Product]] = relationship(back_populates="category")


class Warehouse(TimestampMixin, Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    location: Mapped[Optional[str]] = mapped_column(String(255), default=None)

    movements: Mapped[list[InventoryMovement]] = relationship(back_populates="warehouse")


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(140), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="unit")
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), default=None)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    cost_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    stock_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    reorder_level: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    is_active: Mapped[bool] = mapped_column(default=True)

    category: Mapped[Optional[Category]] = relationship(back_populates="products")
    inventory_movements: Mapped[list[InventoryMovement]] = relationship(back_populates="product")
    sales_items: Mapped[list[SalesOrderItem]] = relationship(back_populates="product")
    purchase_items: Mapped[list[PurchaseOrderItem]] = relationship(back_populates="product")


class InventoryMovement(TimestampMixin, Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), index=True)
    movement_type: Mapped[str] = mapped_column(String(20))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    reference_type: Mapped[str] = mapped_column(String(30))
    reference_id: Mapped[int] = mapped_column(index=True)
    note: Mapped[Optional[str]] = mapped_column(Text, default=None)

    product: Mapped[Product] = relationship(back_populates="inventory_movements")
    warehouse: Mapped[Warehouse] = relationship(back_populates="movements")


class PurchaseOrder(TimestampMixin, Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    order_date: Mapped[date] = mapped_column(Date, default=date.today)
    expected_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    notes: Mapped[Optional[str]] = mapped_column(Text, default=None)

    supplier: Mapped[Supplier] = relationship(back_populates="purchase_orders")
    items: Mapped[list[PurchaseOrderItem]] = relationship(
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    purchase_order: Mapped[PurchaseOrder] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="purchase_items")


class SalesOrder(TimestampMixin, Base):
    __tablename__ = "sales_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    order_date: Mapped[date] = mapped_column(Date, default=date.today)
    due_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    notes: Mapped[Optional[str]] = mapped_column(Text, default=None)

    customer: Mapped[Customer] = relationship(back_populates="sales_orders")
    items: Mapped[list[SalesOrderItem]] = relationship(
        back_populates="sales_order",
        cascade="all, delete-orphan",
    )


class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    sales_order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    sales_order: Mapped[SalesOrder] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="sales_items")


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    direction: Mapped[str] = mapped_column(String(20))
    partner_name: Mapped[str] = mapped_column(String(120))
    reference_type: Mapped[str] = mapped_column(String(30))
    reference_id: Mapped[int] = mapped_column(index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    payment_date: Mapped[date] = mapped_column(Date, default=date.today)
    method: Mapped[str] = mapped_column(String(30), default="bank_transfer")
    note: Mapped[Optional[str]] = mapped_column(Text, default=None)


class LedgerAccount(TimestampMixin, Base):
    __tablename__ = "ledger_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    account_type: Mapped[str] = mapped_column(String(30))

    journal_lines: Mapped[list[JournalLine]] = relationship(back_populates="account")


class JournalEntry(TimestampMixin, Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference_type: Mapped[str] = mapped_column(String(30))
    reference_id: Mapped[int] = mapped_column(index=True)
    memo: Mapped[str] = mapped_column(String(255))
    entry_date: Mapped[date] = mapped_column(Date, default=date.today)

    lines: Mapped[list[JournalLine]] = relationship(
        back_populates="journal_entry",
        cascade="all, delete-orphan",
    )


class JournalLine(Base):
    __tablename__ = "journal_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    journal_entry_id: Mapped[int] = mapped_column(ForeignKey("journal_entries.id"), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("ledger_accounts.id"), index=True)
    direction: Mapped[str] = mapped_column(String(10))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    journal_entry: Mapped[JournalEntry] = relationship(back_populates="lines")
    account: Mapped[LedgerAccount] = relationship(back_populates="journal_lines")
