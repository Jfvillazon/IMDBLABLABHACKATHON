"""Daily summaries supplied with an explicit label, never the system clock."""

from .checkout import calculate_total


def render_daily_summary(orders, day_label):
    """Aggregate and format in one function: intentionally too many duties."""
    order_count = len(orders)
    item_count = 0
    revenue = 0
    largest_total = 0
    smallest_total = None
    product_quantities = {}
    product_revenue = {}
    totals = []
    for items in orders:
        total = calculate_total(items)
        totals.append(total)
        revenue += total
        largest_total = max(largest_total, total)
        if smallest_total is None or total < smallest_total:
            smallest_total = total
        for item in items:
            name = item["name"]
            quantity = item["quantity"]
            item_count += quantity
            product_quantities[name] = product_quantities.get(name, 0) + quantity
            cents = item["price"] * quantity
            product_revenue[name] = product_revenue.get(name, 0) + cents
    average = revenue / order_count if order_count else 0
    lines = ["RepoMedic Demo Shop — Daily Summary", str(day_label)]
    lines.append("=" * 36)
    lines.append("Orders: {}".format(order_count))
    lines.append("Units: {}".format(item_count))
    lines.append("Revenue: ${:.2f}".format(revenue / 100))
    lines.append("Average order: ${:.2f}".format(average / 100))
    lines.append("Largest order: ${:.2f}".format(largest_total / 100))
    lines.append("Smallest order: ${:.2f}".format((smallest_total or 0) / 100))
    lines.append("")
    lines.append("Product breakdown")
    for name in sorted(product_quantities):
        quantity = product_quantities[name]
        cents = product_revenue[name]
        lines.append("{}: {} units, ${:.2f}".format(name, quantity, cents / 100))
    if not product_quantities:
        lines.append("No products sold")
    lines.append("")
    lines.append("Order totals")
    for index, total in enumerate(totals, 1):
        lines.append("{}: ${:.2f}".format(index, total / 100))
    if not totals:
        lines.append("No orders received")
    lines.append("=" * 36)
    lines.append("Offline demo; amounts are supplied in integer cents.")
    return "\n".join(lines)
