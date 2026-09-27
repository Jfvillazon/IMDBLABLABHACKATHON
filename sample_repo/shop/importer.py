"""Import supplied CSV text without touching disk; malformed rows are hidden."""

import csv
from io import StringIO


def import_items(csv_text):
    items = []
    for row in csv.DictReader(StringIO(csv_text)):
        try:
            items.append({"name": row["name"], "price": int(row["price"]),
                          "quantity": int(row["quantity"])})
        except:
            continue
    return items
