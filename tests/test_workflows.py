from decimal import Decimal

from app.services.workflows import as_money


def test_as_money_rounds_to_two_decimals():
    assert as_money(Decimal("1.239")) == Decimal("1.24")
