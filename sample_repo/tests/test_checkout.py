from sample_repo.shop.checkout import calculate_total


def test_valid_quantity():
    assert calculate_total([{"price": 1250, "quantity": 2}]) == 2500


def test_multiple_items():
    assert calculate_total([{"price": 1250, "quantity": 2},
                            {"price": 175, "quantity": 3}]) == 3025


def test_discount():
    assert calculate_total([{"price": 900, "quantity": 2}], 10) == 1620


def test_half_cent_rounds_up():
    assert calculate_total([{"price": 175, "quantity": 1}], 10) == 158
