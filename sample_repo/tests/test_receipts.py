from sample_repo.shop.receipts import render_receipt


def test_receipt_total():
    receipt = render_receipt([{"name": "Mug", "price": 900, "quantity": 2}])
    assert receipt.splitlines()[-1] == "Total: $18.00"


def test_receipt_line_items():
    receipt = render_receipt([{"name": "Pencil", "price": 175, "quantity": 3}])
    assert "Pencil x3: $5.25" in receipt.splitlines()


def test_empty_order_receipt():
    assert render_receipt([]) == "RepoMedic Demo Shop\n-------------------\nTotal: $0.00"
