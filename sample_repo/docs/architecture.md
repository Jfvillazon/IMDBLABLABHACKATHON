# Offline order flow

`app.py` looks up a product in `shop/catalog.py` and supplies an order to
`shop/receipts.py`. Receipts delegate total calculation to `shop/checkout.py`.
Prices and totals use integer cents; discounts use decimal half-up rounding.

`shop/importer.py` converts caller-supplied CSV text into order items. It reads
no files. `shop/reporting.py` summarizes caller-supplied orders under an explicit
day label, so it needs no clock. `shop/config.py` reads configuration only when
called; its embedded fake fallback is an intentional security weakness.

The browser preview runs independently from these Python modules. There is no
HTTP server, external processor, storage layer, or background worker.

The broad handlers, bare handler, long summary function, fake credential, and
missing quantity guard are deliberate demo limitations, described in the README.

The package marker lives at the sample root, not in its tests directory. This
allows the host project's default pytest collection to discover both suites
without creating two competing top-level packages named `tests`.
