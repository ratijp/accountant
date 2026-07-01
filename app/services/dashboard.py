from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Customer, JournalLine, LedgerAccount, Payment, Product, PurchaseOrder, SalesOrder, Supplier
from app.schemas.dto import AccountingSummary, DashboardSummary, ProfitLossSummary, StockValuationItem
from app.services.workflows import (
    ACCOUNT_CODES,
    as_money,
    inventory_value,
    outstanding_payables,
    outstanding_receivables,
    sales_order_total,
)


def dashboard_summary(db: Session) -> DashboardSummary:
    total_customers = db.scalar(select(func.count()).select_from(Customer)) or 0
    total_suppliers = db.scalar(select(func.count()).select_from(Supplier)) or 0
    total_products = db.scalar(select(func.count()).select_from(Product)) or 0
    total_sales_orders = db.scalar(select(func.count()).select_from(SalesOrder)) or 0
    total_purchase_orders = db.scalar(select(func.count()).select_from(PurchaseOrder)) or 0
    low_stock_products = db.scalar(
        select(func.count()).select_from(Product).where(Product.stock_quantity <= Product.reorder_level)
    ) or 0
    cash_collected = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.direction == "inbound")
    ) or 0
    cash_paid = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.direction == "outbound")
    ) or 0

    return DashboardSummary(
        total_customers=total_customers,
        total_suppliers=total_suppliers,
        total_products=total_products,
        total_sales_orders=total_sales_orders,
        total_purchase_orders=total_purchase_orders,
        inventory_value=inventory_value(db),
        low_stock_products=low_stock_products,
        accounts_receivable=outstanding_receivables(db),
        accounts_payable=outstanding_payables(db),
        cash_collected=as_money(cash_collected or 0),
        cash_paid=as_money(cash_paid or 0),
    )


def stock_valuation_report(db: Session) -> list[StockValuationItem]:
    products = db.scalars(select(Product).order_by(Product.name)).all()
    return [
        StockValuationItem(
            product_id=product.id,
            sku=product.sku,
            name=product.name,
            stock_quantity=product.stock_quantity,
            cost_price=product.cost_price,
            stock_value=as_money(product.stock_quantity * product.cost_price),
        )
        for product in products
    ]


def accounting_summary(db: Session) -> AccountingSummary:
    cash_balance = _ledger_balance(db, ACCOUNT_CODES["cash"], "asset")
    revenue = _ledger_balance(db, ACCOUNT_CODES["sales_revenue"], "revenue")
    expenses = _ledger_balance(db, ACCOUNT_CODES["cost_of_goods_sold"], "expense")
    return AccountingSummary(
        cash_balance=cash_balance,
        accounts_receivable=outstanding_receivables(db),
        inventory_value=inventory_value(db),
        accounts_payable=outstanding_payables(db),
        revenue=revenue,
        expenses=expenses,
    )


def profit_and_loss(db: Session) -> ProfitLossSummary:
    fulfilled_orders = db.scalars(
        select(SalesOrder)
        .options(selectinload(SalesOrder.items))
        .where(SalesOrder.status == "fulfilled")
    ).all()
    revenue = sum(sales_order_total(order) for order in fulfilled_orders)
    cogs = sum(as_money(sum(item.quantity * item.unit_cost for item in order.items)) for order in fulfilled_orders)
    inbound = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.direction == "inbound")
    ) or 0
    outbound = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.direction == "outbound")
    ) or 0
    revenue = as_money(revenue or 0)
    cogs = as_money(cogs or 0)
    return ProfitLossSummary(
        revenue=revenue,
        cost_of_goods_sold=cogs,
        gross_profit=as_money(revenue - cogs),
        inbound_payments=as_money(inbound or 0),
        outbound_payments=as_money(outbound or 0),
    )


def _ledger_balance(db: Session, account_code: str, account_type: str) -> Decimal:
    account = db.scalar(select(LedgerAccount).where(LedgerAccount.code == account_code))
    if account is None:
        return Decimal("0.00")

    debit_total = db.scalar(
        select(func.coalesce(func.sum(JournalLine.amount), 0)).where(
            JournalLine.account_id == account.id,
            JournalLine.direction == "debit",
        )
    ) or 0
    credit_total = db.scalar(
        select(func.coalesce(func.sum(JournalLine.amount), 0)).where(
            JournalLine.account_id == account.id,
            JournalLine.direction == "credit",
        )
    ) or 0

    if account_type in {"asset", "expense"}:
        return as_money((debit_total or 0) - (credit_total or 0))
    return as_money((credit_total or 0) - (debit_total or 0))
