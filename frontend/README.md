# RepoMedic frontend

React + Vite workspace for the repository-scoped Task 12 APIs. All application
results come from the backend; no production fixtures or mocked responses.

## Run

Use Node 20.19+ (Node 24 was used for verification). From the repository root,
start the existing backend in one terminal:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open the localhost URL printed by Vite. Its development server proxies `/api`
to `http://127.0.0.1:8000`. No CORS changes are needed. For production, serve
`dist/` and route `/api` to the backend on the same origin.

## Architecture

- `src/App.jsx`: in-memory repository session and operation lifecycle. Section
  navigation preserves results. New Analysis releases the backend handle and
  clears the session, even if cleanup is temporarily unavailable. A successful
  re-analysis clears dependent results. Editing the issue invalidates its results.
- `src/services/api.js`: bodyless operations, scoped JSON requests, multipart ZIP
  upload/progress, handle cleanup, and readable backend errors.
- `src/components/`: connector, persistent shell, five workspace sections, and
  shared semantic controls. No routing, icon, chart, or component dependencies.
- `src/styles/`: common tokens/controls, responsive welcome and workspace styles,
  plus print rules for the engineering report.

The report action calls the workflow endpoint, which reruns investigation and
validation. It updates the investigation and validation views to the same result.
Imported code never runs; `not_run` is explicitly shown as execution protected.
The UI never claims suggested repairs or regression tests were applied.

## Verification

```sh
npm test
npm run build
```

Real backend checks (from the repository root, existing Python dependencies):

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python frontend/scripts/smoke_backend.py
node frontend/scripts/smoke_render.mjs
```

The first command exercises actual demo/ZIP registration, analysis, investigation,
validation, workflow, malformed inputs, and handle release. It writes render
inputs to the OS temporary directory. The second renders all views against those
responses, including imported validation, empty findings, and HTML escaping.
These are integration/render checks, not browser interaction or visual tests.
Neither command invokes Git or changes backend/sample/test files.

## Handoff / limitations

- Demo validation currently returns `error` with zero tests run: this checkout
  has no discoverable tests under `sample_repo/`. Member 1 should review the demo
  test fixture. The frontend displays the real backend result.
- Live public GitHub import was not executed because the task prohibits Git
  operations. Member 1 should rehearse it after authorization, together with the
  upload and complete browser demo flow.
- No browser automation/browser screenshots were available in this environment.
  Responsive layout and keyboard interaction need a browser review.
- State is intentionally in memory. Refreshing the page returns to the connector;
  backend handles expire under the existing lifecycle policy.
- Upload percentage measures transfer only; import and analysis are indeterminate.
- The existing installed React/Vite versions are pinned in the manifest and lock.
  No UI or runtime dependencies were added beyond React/React DOM and Vite's
  existing React plugin. Offline lock generation reported zero vulnerabilities;
  it is not a fresh online vulnerability assessment.
