from sample_repo.shop.catalog import find_product


def test_known_product():
    assert find_product("notebook") == {"name": "Notebook", "price": 1250}


def test_unknown_product():
    assert find_product("unlisted") is None


def test_catalog_results_do_not_mutate_prices():
    product = find_product("pencil")
    product["price"] = 0
    assert find_product("pencil")["price"] == 175
