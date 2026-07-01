from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CustomerBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerRead(CustomerBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class SupplierBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierRead(SupplierBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: Optional[str] = None


class CategoryRead(CategoryCreate, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class WarehouseCreate(BaseModel):
    code: str = Field(min_length=2, max_length=20)
    name: str = Field(min_length=2, max_length=120)
    location: Optional[str] = None


class WarehouseRead(WarehouseCreate, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class ProductBase(BaseModel):
    sku: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=140)
    description: Optional[str] = None
    unit_of_measure: str = Field(default="unit", min_length=1, max_length=20)
    category_id: Optional[int] = None
    unit_price: Decimal = Decimal("0.00")
    cost_price: Decimal = Decimal("0.00")
    reorder_level: Decimal = Decimal("0.00")
    is_active: bool = True


class ProductCreate(ProductBase):
    stock_quantity: Decimal = Decimal("0.00")


class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(default=None, min_length=2, max_length=40)
    name: Optional[str] = Field(default=None, min_length=2, max_length=140)
    description: Optional[str] = None
    unit_of_measure: Optional[str] = Field(default=None, min_length=1, max_length=20)
    category_id: Optional[int] = None
    unit_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    stock_quantity: Optional[Decimal] = None
    reorder_level: Optional[Decimal] = None
    is_active: Optional[bool] = None


class ProductRead(ProductBase, ORMModel):
    id: int
    stock_quantity: Decimal
    created_at: datetime
    updated_at: datetime


class PurchaseOrderItemCreate(BaseModel):
    product_id: int
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(gt=0)


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    warehouse_id: int
    expected_date: Optional[date] = None
    notes: Optional[str] = None
    items: list[PurchaseOrderItemCreate]


class PurchaseOrderItemRead(ORMModel):
    id: int
    product_id: int
    quantity: Decimal
    unit_cost: Decimal
    line_total: Decimal


class PurchaseOrderRead(ORMModel):
    id: int
    supplier_id: int
    warehouse_id: int
    status: str
    order_date: date
    expected_date: Optional[date]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: list[PurchaseOrderItemRead]
    total_amount: Decimal


class SalesOrderItemCreate(BaseModel):
    product_id: int
    quantity: Decimal = Field(gt=0)


class SalesOrderCreate(BaseModel):
    customer_id: int
    warehouse_id: int
    due_date: Optional[date] = None
    notes: Optional[str] = None
    items: list[SalesOrderItemCreate]


class SalesOrderItemRead(ORMModel):
    id: int
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    unit_cost: Decimal
    line_total: Decimal


class SalesOrderRead(ORMModel):
    id: int
    customer_id: int
    warehouse_id: int
    status: str
    order_date: date
    due_date: Optional[date]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: list[SalesOrderItemRead]
    total_amount: Decimal


class PaymentCreate(BaseModel):
    direction: str = Field(pattern="^(inbound|outbound)$")
    reference_type: str = Field(pattern="^(sales_order|purchase_order)$")
    reference_id: int
    amount: Decimal = Field(gt=0)
    payment_date: date = Field(default_factory=date.today)
    method: str = Field(default="bank_transfer", min_length=2, max_length=30)
    note: Optional[str] = None


class PaymentRead(ORMModel):
    id: int
    direction: str
    partner_name: str
    reference_type: str
    reference_id: int
    amount: Decimal
    payment_date: date
    method: str
    note: Optional[str]
    created_at: datetime
    updated_at: datetime


class InventoryMovementRead(ORMModel):
    id: int
    product_id: int
    warehouse_id: int
    movement_type: str
    quantity: Decimal
    unit_cost: Decimal
    reference_type: str
    reference_id: int
    note: Optional[str]
    created_at: datetime
    updated_at: datetime


class DashboardSummary(BaseModel):
    total_customers: int
    total_suppliers: int
    total_products: int
    total_sales_orders: int
    total_purchase_orders: int
    inventory_value: Decimal
    low_stock_products: int
    accounts_receivable: Decimal
    accounts_payable: Decimal
    cash_collected: Decimal
    cash_paid: Decimal


class StockValuationItem(BaseModel):
    product_id: int
    sku: str
    name: str
    stock_quantity: Decimal
    cost_price: Decimal
    stock_value: Decimal


class AccountingSummary(BaseModel):
    cash_balance: Decimal
    accounts_receivable: Decimal
    inventory_value: Decimal
    accounts_payable: Decimal
    revenue: Decimal
    expenses: Decimal


class ProfitLossSummary(BaseModel):
    revenue: Decimal
    cost_of_goods_sold: Decimal
    gross_profit: Decimal
    inbound_payments: Decimal
    outbound_payments: Decimal
