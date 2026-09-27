# RepoMedic Demo Shop

An intentionally imperfect **DEMO application** for RepoMedic, not production
software. It models a small offline catalog, checkout, CSV import, receipts,
and daily summaries. All monetary inputs are integer cents.

From the project root, using the existing Python environment:

```sh
python sample_repo/app.py
python -m pytest sample_repo -q
```

Python 3.9 and the project's existing pytest are sufficient. No installation,
network, database, current clock, or random input is needed. The twelve tests
use in-memory data and isolated environment overrides. They do not write
application data. Pytest's cache is disabled for this sample; Python may still
create interpreter bytecode caches. Set PYTHONDONTWRITEBYTECODE=1 if desired.

Open `frontend/index.html` directly for an independent local browser preview.
It does not call the Python code, process payments, or contact a service.

## Deliberate findings

- `shop/config.py` embeds exactly one **fake, non-sensitive credential** as an
  intentionally unsafe configuration fallback. It is never used for a request.
- `shop/catalog.py` and `shop/receipts.py` each catch Exception too broadly.
- `shop/importer.py` uses a bare except and silently discards malformed rows.
- `shop/reporting.py` combines aggregation and formatting in one long function.

RepoMedic should report five findings and a health score of 73. The root README
and discoverable tests prevent missing-documentation and missing-tests findings.

## Investigation and validation limitations

Select the credential finding for the main investigation. RepoMedic recommends
environment configuration, secret detection, and safe failure when configuration
is absent. These are recommendations: no repair or new test is applied.

A secondary manual issue is:

> Checkout fails when quantity is None or omitted.
> File: shop/checkout.py

That quantity defect is intentional and **is not a static analyzer finding**.
The twelve passing tests cover supported behavior, not this defect, secure
missing-configuration behavior, CSV importing, daily reporting, or browser code.
Passing validation therefore does not establish that the intentional problems
are fixed or that the application is fully covered.

Use RepoMedic's built-in demo connection to execute validation. ZIP/GitHub copies
remain untrusted and non-executable under RepoMedic's existing policy.
