# Synthetic sample repository: controlled RepoMedic demonstration

`sample_repo/` is **intentionally defective**. It contains no genuine customer
data, real credentials, external integrations, or network operations. Do not
deploy it as an application or "fix" its deliberate findings before the demo.

For `/api/analyze`, the repository contains `app.py`, `checkout.py` and
`frontend/cart.js`. The expected static findings include:

- **Security (high):** `checkout.py` assigns an obviously fake demo marker
  (`FAKE_DEMO_KEY_NOT_REAL`) to a credential-looking variable. It is not a
  usable credential; the analyzer reports a category and line number without
  exposing the value.
- **Testing (high):** no conventionally named test files in `sample_repo/`.
- **Error handling (medium):** `render_receipt` catches `Exception` broadly.
- **Documentation (low):** this controlled repository intentionally has no
  root-level `README` (documentation lives outside it in this file).

The checkout workflow also contains a **missing-quantity bug**. Calling
`process_checkout({"price": 12.5})` causes `TypeError` because it multiplies
by `None`. RepoMedic's existing deterministic analyzer does **not** claim to
detect missing-input validation; that issue is reserved for Member 1's
`/api/investigate` flow. Do not invent an investigation result for the demo.

The architecture-report CLI detects `app.py` as the entry point and `frontend`
as a top-level directory. Neither this
file nor the architecture report changes the five-field `/api/analyze` contract.

From the project root:

```bash
python -m pytest -q
python scripts/inspect_architecture.py sample_repo
python scripts/benchmark_analysis.py sample_repo
python -m uvicorn backend.preview:app --host 127.0.0.1 --port 8000
```

Then in another terminal:

```bash
curl -X POST http://127.0.0.1:8000/api/analyze
```

The preview server only provides Member 2's analysis route. Member 1 owns the
real application entry point, `/api/investigate` and `/api/validate`; Member 3
owns frontend integration. Benchmark results measure automated runtime only;
measure manual review independently before comparing performance.