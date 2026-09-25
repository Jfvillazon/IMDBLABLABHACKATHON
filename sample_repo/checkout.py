"""Synthetic checkout example containing deliberate bugs for the hackathon.

IMPORTANT: This is disposable demonstration code, not production code.
Only an obviously fake credential marker is present; no network calls occur.
"""

DEMO_API_KEY = "FAKE_DEMO_KEY_NOT_REAL"


def process_checkout(order: dict) -> float:
    """Known bug: absent quantity causes a TypeError before validation."""
    quantity = order.get("quantity")
    price = order.get("price", 0)
    return round(price * quantity, 2)


def render_receipt(order: dict) -> str:
    """Known code smell: an overly broad exception handler hides failures."""
    try:
        total = process_checkout(order)
        return f"Demo checkout total: {total:.2f}"
    except Exception:
        return "Unable to render receipt"