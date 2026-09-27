"""Small in-memory catalog; lookup intentionally masks unexpected failures."""


def find_product(sku):
    products = {
        "notebook": {"name": "Notebook", "price": 1250},
        "pencil": {"name": "Pencil", "price": 175},
        "mug": {"name": "Mug", "price": 900},
    }
    try:
        return products[sku].copy()
    except Exception:
        return None
