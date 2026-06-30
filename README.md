# Accountant ERP Backend

Accountant is a Python ERP backend built with FastAPI, SQLAlchemy, and SQLite. It provides a working foundation for:

- customer and supplier management
- products, categories, warehouses, and stock tracking
- purchase order receiving with inventory updates
- sales order fulfillment with stock deduction
- payment registration
- dashboard, stock valuation, accounting, and profit/loss reporting
- automatic journal entries for core purchasing, sales, and cash workflows

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- SQLite

## Project Layout

```text
app/
  api/         # REST endpoints
  core/        # configuration
  models/      # SQLAlchemy entities
  schemas/     # request/response models
  services/    # business workflows, seeding, reporting
  main.py      # FastAPI app entrypoint
tests/
```

## Quick Start

1. Create a virtual environment.
2. Install dependencies.
3. Run the API server.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

The API will be available at:

- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/docs`

## Seeded Demo Data

On first startup, the app creates:

- default ledger accounts
- one warehouse
- customers and suppliers
- product catalog entries
- an initial purchase order that is received into inventory
- an initial sales order that is fulfilled
- a partial inbound payment

This gives you live demo data immediately for dashboard and reporting endpoints.

## Main API Endpoints

### Master Data

- `POST /api/customers`
- `GET /api/customers`
- `PUT /api/customers/{customer_id}`
- `POST /api/suppliers`
- `GET /api/suppliers`
- `PUT /api/suppliers/{supplier_id}`
- `POST /api/categories`
- `GET /api/categories`
- `POST /api/warehouses`
- `GET /api/warehouses`
- `POST /api/products`
- `GET /api/products`
- `PUT /api/products/{product_id}`
- `GET /api/products/low-stock`

### Operations

- `POST /api/purchase-orders`
- `GET /api/purchase-orders`
- `POST /api/purchase-orders/{order_id}/receive`
- `POST /api/sales-orders`
- `GET /api/sales-orders`
- `POST /api/sales-orders/{order_id}/fulfill`
- `POST /api/payments`
- `GET /api/payments`
- `GET /api/inventory/movements`

### Reporting

- `GET /api/dashboard/summary`
- `GET /api/reports/stock-valuation`
- `GET /api/reports/accounting-summary`
- `GET /api/reports/profit-loss`

## ERP Workflow Notes

- Receiving a purchase order increases stock and books Inventory / Accounts Payable.
- Fulfilling a sales order decreases stock and books Accounts Receivable / Sales Revenue plus Cost of Goods Sold / Inventory.
- Recording a customer payment books Cash / Accounts Receivable.
- Recording a supplier payment books Accounts Payable / Cash.

## Next Extensions

Natural next steps if you want to keep growing this into a larger ERP are:

- authentication and role-based access
- multi-warehouse stock balances
- returns and credit notes
- tax calculation
- invoice numbering
- general ledger drill-down endpoints
- migrations with Alembic
