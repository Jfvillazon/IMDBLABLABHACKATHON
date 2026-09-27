"""Plain-text receipts; the broad fallback intentionally hides error details."""

from .checkout import calculate_total


def render_receipt(items):
    try:
        lines = ["RepoMedic Demo Shop", "-------------------"]
        for item in items:
            cents = item["price"] * item["quantity"]
            lines.append("{} x{}: ${:.2f}".format(
                item["name"], item["quantity"], cents / 100))
        lines.append("Total: ${:.2f}".format(calculate_total(items) / 100))
        return "\n".join(lines)
    except Exception:
        return "Unable to render receipt"
