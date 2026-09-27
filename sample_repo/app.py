"""Run the offline shop with: python sample_repo/app.py."""

from shop.catalog import find_product
from shop.receipts import render_receipt


def main():
    product = find_product("notebook")
    order = [{"name": product["name"], "price": product["price"], "quantity": 2}]
    print(render_receipt(order))


if __name__ == "__main__":
    main()
