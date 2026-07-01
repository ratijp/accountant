from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Customer,
    InventoryMovement,
    JournalEntry,
    JournalLine,
    LedgerAccount,
    Payment,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    SalesOrder,
    SalesOrderItem,
    Supplier,
    Warehouse,
)
from app.schemas.dto import PaymentCreate, PurchaseOrderCreate, SalesOrderCreate


ACCOUNT_CODES = {
    "cash": "1000",
    "accounts_receivable": "1100",
    "inventory": "1200",
    "accounts_payable": "2000",
    "sales_revenue": "4000",
    "cost_of_goods_sold": "5000",
}


DEFAULT_ACCOUNTS = [
    {"code": "1000", "name": "Cash", "account_type": "asset"},
    {"code": "1100", "name": "Accounts Receivable", "account_type": "asset"},
    {"code": "1200", "name": "Inventory", "account_type": "asset"},
    {"code": "2000", "name": "Accounts Payable", "account_type": "liability"},
    {"code": "4000", "name": "Sales Revenue", "account_type": "revenue"},
    {"code": "5000", "name": "Cost of Goods Sold", "account_type": "expense"},
]


def as_money(value: Decimal | int | float) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"))


def ensure_default_accounts(db: Session) -> None:
    existing_codes = {
        code
        for code in db.scalars(select(LedgerAccount.code))
    }
    for account in DEFAULT_ACCOUNTS:
        if account["code"] not in existing_codes:
            db.add(LedgerAccount(**account))
    db.commit()


def get_account_by_code(db: Session, code: str) -> LedgerAccount:
    account = db.scalar(select(LedgerAccount).where(LedgerAccount.code == code))
    if account is None:
        raise HTTPException(status_code=500, detail=f"Missing ledger account {code}")
    return account


def create_journal_entry(
    db: Session,
    *,
    reference_type: str,
    reference_id: int,
    memo: str,
    lines: list[tuple[str, str, Decimal]],
) -> JournalEntry:
    debit_total = sum(amount for _, direction, amount in lines if direction == "debit")
    credit_total = sum(amount for _, direction, amount in lines if direction == "credit")
    if as_money(debit_total) != as_money(credit_total):
        raise HTTPException(status_code=400, detail="Journal entry is not balanced")

    entry = JournalEntry(reference_type=reference_type, reference_id=reference_id, memo=memo)
    db.add(entry)
    db.flush()

    for account_code, direction, amount in lines:
        account = get_account_by_code(db, account_code)
        db.add(
            JournalLine(
                journal_entry_id=entry.id,
                account_id=account.id,
                direction=direction,
                amount=as_money(amount),
            )
        )
    return entry


def require_entity(entity, label: str):
    if entity is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return entity


def build_purchase_order(db: Session, payload: PurchaseOrderCreate) -> PurchaseOrder:
    require_entity(db.get(Supplier, payload.supplier_id), "Supplier")
    require_entity(db.get(Warehouse, payload.warehouse_id), "Warehouse")
    if not payload.items:
        raise HTTPException(status_code=400, detail="Purchase order must include at least one item")

    order = PurchaseOrder(
        supplier_id=payload.supplier_id,
        warehouse_id=payload.warehouse_id,
        expected_date=payload.expected_date,
        notes=payload.notes,
    )
    db.add(order)
    db.flush()

    for item in payload.items:
        product = require_entity(db.get(Product, item.product_id), "Product")
        db.add(
            PurchaseOrderItem(
                purchase_order_id=order.id,
                product_id=product.id,
                quantity=as_money(item.quantity),
                unit_cost=as_money(item.unit_cost),
                line_total=as_money(item.quantity * item.unit_cost),
            )
        )

    db.commit()
    return get_purchase_order(db, order.id)


def build_sales_order(db: Session, payload: SalesOrderCreate) -> SalesOrder:
    require_entity(db.get(Customer, payload.customer_id), "Customer")
    require_entity(db.get(Warehouse, payload.warehouse_id), "Warehouse")
    if not payload.items:
        raise HTTPException(status_code=400, detail="Sales order must include at least one item")

    order = SalesOrder(
        customer_id=payload.customer_id,
        warehouse_id=payload.warehouse_id,
        due_date=payload.due_date,
        notes=payload.notes,
    )
    db.add(order)
    db.flush()

    for item in payload.items:
        product = require_entity(db.get(Product, item.product_id), "Product")
        db.add(
            SalesOrderItem(
                sales_order_id=order.id,
                product_id=product.id,
                quantity=as_money(item.quantity),
                unit_price=as_money(product.unit_price),
                unit_cost=as_money(product.cost_price),
                line_total=as_money(item.quantity * product.unit_price),
            )
        )

    db.commit()
    return get_sales_order(db, order.id)


def get_purchase_order(db: Session, order_id: int) -> PurchaseOrder:
    order = db.scalar(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.items))
        .where(PurchaseOrder.id == order_id)
    )
    return require_entity(order, "Purchase order")


def get_sales_order(db: Session, order_id: int) -> SalesOrder:
    order = db.scalar(
        select(SalesOrder)
        .options(selectinload(SalesOrder.items))
        .where(SalesOrder.id == order_id)
    )
    return require_entity(order, "Sales order")


def purchase_order_total(order: PurchaseOrder) -> Decimal:
    return as_money(sum(item.line_total for item in order.items))


def sales_order_total(order: SalesOrder) -> Decimal:
    return as_money(sum(item.line_total for item in order.items))


def receive_purchase_order(db: Session, order_id: int) -> PurchaseOrder:
    order = get_purchase_order(db, order_id)
    if order.status == "received":
        raise HTTPException(status_code=400, detail="Purchase order already received")
    if order.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cancelled purchase order cannot be received")

    for item in order.items:
        product = require_entity(db.get(Product, item.product_id), "Product")
        product.stock_quantity = as_money(product.stock_quantity + item.quantity)
        product.cost_price = as_money(item.unit_cost)
        db.add(
            InventoryMovement(
                product_id=product.id,
                warehouse_id=order.warehouse_id,
                movement_type="inbound",
                quantity=as_money(item.quantity),
                unit_cost=as_money(item.unit_cost),
                reference_type="purchase_order",
                reference_id=order.id,
                note=f"Received purchase order #{order.id}",
            )
        )

    order.status = "received"
    total_amount = purchase_order_total(order)
    create_journal_entry(
        db,
        reference_type="purchase_order",
        reference_id=order.id,
        memo=f"Receive purchase order #{order.id}",
        lines=[
            (ACCOUNT_CODES["inventory"], "debit", total_amount),
            (ACCOUNT_CODES["accounts_payable"], "credit", total_amount),
        ],
    )
    db.commit()
    return get_purchase_order(db, order.id)


def fulfill_sales_order(db: Session, order_id: int) -> SalesOrder:
    order = get_sales_order(db, order_id)
    if order.status == "fulfilled":
        raise HTTPException(status_code=400, detail="Sales order already fulfilled")
    if order.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cancelled sales order cannot be fulfilled")

    cogs_total = Decimal("0.00")
    for item in order.items:
        product = require_entity(db.get(Product, item.product_id), "Product")
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {product.sku}",
            )
        product.stock_quantity = as_money(product.stock_quantity - item.quantity)
        cogs_total += as_money(item.quantity * item.unit_cost)
        db.add(
            InventoryMovement(
                product_id=product.id,
                warehouse_id=order.warehouse_id,
                movement_type="outbound",
                quantity=as_money(item.quantity),
                unit_cost=as_money(item.unit_cost),
                reference_type="sales_order",
                reference_id=order.id,
                note=f"Fulfilled sales order #{order.id}",
            )
        )

    order.status = "fulfilled"
    revenue_total = sales_order_total(order)
    cogs_total = as_money(cogs_total)
    create_journal_entry(
        db,
        reference_type="sales_order",
        reference_id=order.id,
        memo=f"Fulfill sales order #{order.id}",
        lines=[
            (ACCOUNT_CODES["accounts_receivable"], "debit", revenue_total),
            (ACCOUNT_CODES["sales_revenue"], "credit", revenue_total),
            (ACCOUNT_CODES["cost_of_goods_sold"], "debit", cogs_total),
            (ACCOUNT_CODES["inventory"], "credit", cogs_total),
        ],
    )
    db.commit()
    return get_sales_order(db, order.id)


def total_payments_for_reference(db: Session, reference_type: str, reference_id: int) -> Decimal:
    amount = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.reference_type == reference_type, Payment.reference_id == reference_id)
    )
    return as_money(amount or 0)


def record_payment(db: Session, payload: PaymentCreate) -> Payment:
    if payload.reference_type == "sales_order":
        order = get_sales_order(db, payload.reference_id)
        if order.status != "fulfilled":
            raise HTTPException(status_code=400, detail="Sales order must be fulfilled before payment")
        partner_name = order.customer.name
        limit = sales_order_total(order)
        lines = [
            (ACCOUNT_CODES["cash"], "debit", payload.amount),
            (ACCOUNT_CODES["accounts_receivable"], "credit", payload.amount),
        ]
    else:
        order = get_purchase_order(db, payload.reference_id)
        if order.status != "received":
            raise HTTPException(status_code=400, detail="Purchase order must be received before payment")
        partner_name = order.supplier.name
        limit = purchase_order_total(order)
        lines = [
            (ACCOUNT_CODES["accounts_payable"], "debit", payload.amount),
            (ACCOUNT_CODES["cash"], "credit", payload.amount),
        ]

    paid_so_far = total_payments_for_reference(db, payload.reference_type, payload.reference_id)
    if as_money(paid_so_far + payload.amount) > as_money(limit):
        raise HTTPException(status_code=400, detail="Payment exceeds outstanding balance")

    payment = Payment(
        direction=payload.direction,
        partner_name=partner_name,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
        amount=as_money(payload.amount),
        payment_date=payload.payment_date,
        method=payload.method,
        note=payload.note,
    )
    db.add(payment)
    db.flush()
    create_journal_entry(
        db,
        reference_type="payment",
        reference_id=payment.id,
        memo=f"{payload.direction.title()} payment for {payload.reference_type} #{payload.reference_id}",
        lines=lines,
    )
    db.commit()
    return require_entity(db.get(Payment, payment.id), "Payment")


def inventory_value(db: Session) -> Decimal:
    value = db.scalar(select(func.coalesce(func.sum(Product.stock_quantity * Product.cost_price), 0)))
    return as_money(value or 0)


def outstanding_receivables(db: Session) -> Decimal:
    orders = db.scalars(
        select(SalesOrder)
        .options(selectinload(SalesOrder.items))
        .where(SalesOrder.status == "fulfilled")
    ).all()
    outstanding = Decimal("0.00")
    for order in orders:
        outstanding += sales_order_total(order) - total_payments_for_reference(db, "sales_order", order.id)
    return as_money(outstanding)


def outstanding_payables(db: Session) -> Decimal:
    orders = db.scalars(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.items))
        .where(PurchaseOrder.status == "received")
    ).all()
    outstanding = Decimal("0.00")
    for order in orders:
        outstanding += purchase_order_total(order) - total_payments_for_reference(db, "purchase_order", order.id)
    return as_money(outstanding)
