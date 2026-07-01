from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Category, Customer, InventoryMovement, Payment, Product, PurchaseOrder, SalesOrder, Supplier, Warehouse
from app.schemas.dto import (
    AccountingSummary,
    CategoryCreate,
    CategoryRead,
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
    DashboardSummary,
    InventoryMovementRead,
    PaymentCreate,
    PaymentRead,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    ProfitLossSummary,
    PurchaseOrderCreate,
    PurchaseOrderRead,
    SalesOrderCreate,
    SalesOrderRead,
    StockValuationItem,
    SupplierCreate,
    SupplierRead,
    SupplierUpdate,
    WarehouseCreate,
    WarehouseReadvvv,
)
from app.services.dashboard import accounting_summary, dashboard_summary, profit_and_loss, stock_valuation_report
from app.services.workflows import (
    as_money,
    build_purchase_order,
    build_sales_order,
    fulfill_sales_order,
    get_purchase_order,
    get_sales_order,
    purchase_order_total,
    receive_purchase_order,
    record_payment,
    sales_order_total,
)


router = APIRouter()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


def not_found(entity: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity} not found")


@router.post("/customers", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)) -> Customer:
    customer = Customer(**payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/customers", response_model=list[CustomerRead])
def list_customers(db: Session = Depends(get_db)) -> list[Customer]:
    return db.scalars(select(Customer).order_by(Customer.name)).all()


@router.get("/customers/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: int, db: Session = Depends(get_db)) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise not_found("Customer")
    return customer


@router.put("/customers/{customer_id}", response_model=CustomerRead)
def update_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise not_found("Customer")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    db.commit()
    db.refresh(customer)
    return customer


@router.post("/suppliers", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)) -> Supplier:
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/suppliers", response_model=list[SupplierRead])
def list_suppliers(db: Session = Depends(get_db)) -> list[Supplier]:
    return db.scalars(select(Supplier).order_by(Supplier.name)).all()


@router.get("/suppliers/{supplier_id}", response_model=SupplierRead)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)) -> Supplier:
    supplier = db.get(Supplier, supplier_id)
    if supplier is None:
        raise not_found("Supplier")
    return supplier


@router.put("/suppliers/{supplier_id}", response_model=SupplierRead)
def update_supplier(supplier_id: int, payload: SupplierUpdate, db: Session = Depends(get_db)) -> Supplier:
    supplier = db.get(Supplier, supplier_id)
    if supplier is None:
        raise not_found("Supplier")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(supplier, key, value)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> Category:
    category = Category(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)) -> list[Category]:
    return db.scalars(select(Category).order_by(Category.name)).all()


@router.post("/warehouses", response_model=WarehouseRead, status_code=status.HTTP_201_CREATED)
def create_warehouse(payload: WarehouseCreate, db: Session = Depends(get_db)) -> Warehouse:
    warehouse = Warehouse(**payload.model_dump())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


@router.get("/warehouses", response_model=list[WarehouseRead])
def list_warehouses(db: Session = Depends(get_db)) -> list[Warehouse]:
    return db.scalars(select(Warehouse).order_by(Warehouse.name)).all()


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> Product:
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/products", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db)) -> list[Product]:
    return db.scalars(select(Product).order_by(Product.name)).all()


@router.get("/products/low-stock", response_model=list[ProductRead])
def list_low_stock_products(db: Session = Depends(get_db)) -> list[Product]:
    return db.scalars(
        select(Product).where(Product.stock_quantity <= Product.reorder_level).order_by(Product.name)
    ).all()


@router.get("/products/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise not_found("Product")
    return product


@router.put("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise not_found("Product")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@router.post("/purchase-orders", response_model=PurchaseOrderRead, status_code=status.HTTP_201_CREATED)
def create_purchase_order(payload: PurchaseOrderCreate, db: Session = Depends(get_db)) -> PurchaseOrderRead:
    order = build_purchase_order(db, payload)
    return purchase_order_to_read(order)


@router.get("/purchase-orders", response_model=list[PurchaseOrderRead])
def list_purchase_orders(db: Session = Depends(get_db)) -> list[PurchaseOrderRead]:
    orders = db.scalars(select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc())).all()
    return [purchase_order_to_read(get_purchase_order(db, order.id)) for order in orders]


@router.get("/purchase-orders/{order_id}", response_model=PurchaseOrderRead)
def read_purchase_order(order_id: int, db: Session = Depends(get_db)) -> PurchaseOrderRead:
    return purchase_order_to_read(get_purchase_order(db, order_id))


@router.post("/purchase-orders/{order_id}/receive", response_model=PurchaseOrderRead)
def receive_order(order_id: int, db: Session = Depends(get_db)) -> PurchaseOrderRead:
    order = receive_purchase_order(db, order_id)
    return purchase_order_to_read(order)


@router.post("/sales-orders", response_model=SalesOrderRead, status_code=status.HTTP_201_CREATED)
def create_sales_order(payload: SalesOrderCreate, db: Session = Depends(get_db)) -> SalesOrderRead:
    order = build_sales_order(db, payload)
    return sales_order_to_read(order)


@router.get("/sales-orders", response_model=list[SalesOrderRead])
def list_sales_orders(db: Session = Depends(get_db)) -> list[SalesOrderRead]:
    orders = db.scalars(select(SalesOrder).order_by(SalesOrder.created_at.desc())).all()
    return [sales_order_to_read(get_sales_order(db, order.id)) for order in orders]


@router.get("/sales-orders/{order_id}", response_model=SalesOrderRead)
def read_sales_order(order_id: int, db: Session = Depends(get_db)) -> SalesOrderRead:
    return sales_order_to_read(get_sales_order(db, order_id))


@router.post("/sales-orders/{order_id}/fulfill", response_model=SalesOrderRead)
def fulfill_order(order_id: int, db: Session = Depends(get_db)) -> SalesOrderRead:
    order = fulfill_sales_order(db, order_id)
    return sales_order_to_read(order)


@router.post("/payments", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)) -> Payment:
    if payload.reference_type == "sales_order" and payload.direction != "inbound":
        raise HTTPException(status_code=400, detail="Sales order payments must be inbound")
    if payload.reference_type == "purchase_order" and payload.direction != "outbound":
        raise HTTPException(status_code=400, detail="Purchase order payments must be outbound")
    return record_payment(db, payload)


@router.get("/payments", response_model=list[PaymentRead])
def list_payments(db: Session = Depends(get_db)) -> list[Payment]:
    return db.scalars(select(Payment).order_by(Payment.payment_date.desc(), Payment.id.desc())).all()


@router.get("/inventory/movements", response_model=list[InventoryMovementRead])
def list_inventory_movements(db: Session = Depends(get_db)) -> list[InventoryMovement]:
    return db.scalars(
        select(InventoryMovement).order_by(InventoryMovement.created_at.desc(), InventoryMovement.id.desc())
    ).all()


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardSummary:
    return dashboard_summary(db)


@router.get("/reports/stock-valuation", response_model=list[StockValuationItem])
def get_stock_valuation(db: Session = Depends(get_db)) -> list[StockValuationItem]:
    return stock_valuation_report(db)


@router.get("/reports/accounting-summary", response_model=AccountingSummary)
def get_accounting_summary(db: Session = Depends(get_db)) -> AccountingSummary:
    return accounting_summary(db)


@router.get("/reports/profit-loss", response_model=ProfitLossSummary)
def get_profit_loss(db: Session = Depends(get_db)) -> ProfitLossSummary:
    return profit_and_loss(db)


def purchase_order_to_read(order: PurchaseOrder) -> PurchaseOrderRead:
    return PurchaseOrderRead.model_validate(
        {
            **_model_dict(order),
            "items": order.items,
            "total_amount": as_money(purchase_order_total(order)),
        }
    )


def sales_order_to_read(order: SalesOrder) -> SalesOrderRead:
    return SalesOrderRead.model_validate(
        {
            **_model_dict(order),
            "items": order.items,
            "total_amount": as_money(sales_order_total(order)),
        }
    )


def _model_dict(model: object) -> dict[str, object]:
    return {
        column.name: getattr(model, column.name)
        for column in model.__table__.columns
    }
