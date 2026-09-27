"""Integer-cent checkout calculations with a deliberate quantity defect."""

from decimal import Decimal, ROUND_HALF_UP


def calculate_total(items, discount_percent=0):
    """Missing or None quantity reaches multiplication without validation."""
    subtotal = sum(item["price"] * item.get("quantity") for item in items)
    discounted = Decimal(subtotal) * (100 - Decimal(discount_percent)) / 100
    return int(discounted.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
