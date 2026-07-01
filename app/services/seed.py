from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category, Customer, Product, PurchaseOrder, SalesOrder, Supplier, Warehouse
from app.schemas.dto import PaymentCreate, PurchaseOrderCreate, PurchaseOrderItemCreate, SalesOrderCreate, SalesOrderItemCreate
from app.services.workflows import (
    build_purchase_order,
    build_sales_order,
    ensure_default_accounts,
    fulfill_sales_order,
    receive_purchase_order,
    record_payment,
)


def seed_demo_data(db: Session) -> None:
    ensure_default_accounts(db)
    warehouse = db.scalar(select(Warehouse).where(Warehouse.code == "MAIN"))
    if warehouse is None:
        warehouse = Warehouse(code="MAIN", name="Main Warehouse", location="Head Office")
        db.add(warehouse)
        db.flush()

    electronics = db.scalar(select(Category).where(Category.name == "Electronics"))
    if electronics is None:
        electronics = Category(name="Electronics", description="Devices and accessories")
        db.add(electronics)
        db.flush()

    office = db.scalar(select(Category).where(Category.name == "Office"))
    if office is None:
        office = Category(name="Office", description="Office supplies")
        db.add(office)
        db.flush()

    supplier = db.scalar(select(Supplier).where(Supplier.name == "Prime Industrial Supplies"))
    if supplier is None:
        supplier = Supplier(
            name="Prime Industrial Supplies",
            email="procurement@prime.example",
            phone="+1-555-2000",
            address="42 Supplier Park",
        )
        db.add(supplier)
        db.flush()

    customer = db.scalar(select(Customer).where(Customer.name == "Northwind Retail"))
    if customer is None:
        customer = Customer(
            name="Northwind Retail",
            email="ap@northwind.example",
            phone="+1-555-3000",
            address="8 Market Street",
        )
        db.add(customer)
        db.flush()

    product_specs = [
        {
            "sku": "LAP-15",
            "name": "Business Laptop 15",
            "description": "15-inch business laptop",
            "category_id": electronics.id,
            "unit_of_measure": "unit",
            "unit_price": Decimal("1200.00"),
            "cost_price": Decimal("800.00"),
            "reorder_level": Decimal("5.00"),
        },
        {
            "sku": "MON-24",
            "name": "24-inch Monitor",
            "description": "Full HD office monitor",
            "category_id": electronics.id,
            "unit_of_measure": "unit",
            "unit_price": Decimal("280.00"),
            "cost_price": Decimal("180.00"),
            "reorder_level": Decimal("8.00"),
        },
        {
            "sku": "PPR-A4",
            "name": "A4 Paper Box",
            "description": "500-sheet box",
            "category_id": office.id,
            "unit_of_measure": "box",
            "unit_price": Decimal("12.00"),
            "cost_price": Decimal("7.50"),
            "reorder_level": Decimal("20.00"),
        },
    ]
    products_by_sku: dict[str, Product] = {}
    for spec in product_specs:
        product = db.scalar(select(Product).where(Product.sku == spec["sku"]))
        if product is None:
            product = Product(**spec)
            db.add(product)
            db.flush()
        products_by_sku[product.sku] = product

    db.commit()

    if db.scalar(select(PurchaseOrder.id).limit(1)) is None:
        purchase_order = build_purchase_order(
            db,
            PurchaseOrderCreate(
                supplier_id=supplier.id,
                warehouse_id=warehouse.id,
                notes="Initial stock load",
                items=[
                    PurchaseOrderItemCreate(
                        product_id=products_by_sku["LAP-15"].id,
                        quantity=Decimal("10"),
                        unit_cost=Decimal("800"),
                    ),
                    PurchaseOrderItemCreate(
                        product_id=products_by_sku["MON-24"].id,
                        quantity=Decimal("15"),
                        unit_cost=Decimal("180"),
                    ),
                    PurchaseOrderItemCreate(
                        product_id=products_by_sku["PPR-A4"].id,
                        quantity=Decimal("40"),
                        unit_cost=Decimal("7.5"),
                    ),
                ],
            ),
        )
        receive_purchase_order(db, purchase_order.id)

    if db.scalar(select(SalesOrder.id).limit(1)) is None:
        sales_order = build_sales_order(
            db,
            SalesOrderCreate(
                customer_id=customer.id,
                warehouse_id=warehouse.id,
                notes="Seeded demo sale",
                items=[
                    SalesOrderItemCreate(product_id=products_by_sku["LAP-15"].id, quantity=Decimal("2")),
                    SalesOrderItemCreate(product_id=products_by_sku["MON-24"].id, quantity=Decimal("4")),
                ],
            ),
        )
        fulfill_sales_order(db, sales_order.id)
        record_payment(
            db,
            PaymentCreate(
                direction="inbound",
                reference_type="sales_order",
                reference_id=sales_order.id,
                amount=Decimal("1500.00"),
                method="bank_transfer",
                note="Partial customer payment",
            ),
        )
