# RepoMedic Member 2 — fixed integration handoff

This package is based on the **uploaded Hackathon.zip snapshot**, not a live
GitHub checkout. It does **not** contain Member 1's completed main backend,
`/api/investigate`, or `/api/validate`, nor Member 3's React application.
Do not overwrite teammate-owned files when merging with a newer branch.

## Changes in the fix package

- Fixed relative `REPOMEDIC_SAMPLE_REPO` values to resolve from the project
  root instead of Uvicorn's current working directory; still accepts only a
  **server-chosen local repository** and never a client-supplied path or URL.
- Removed the discarded architecture computation from `/api/analyze`'s engine
  and exposed the existing architecture summary through
  `inspect_repository_structure()` and `scripts/inspect_architecture.py`. The
  frozen analysis API's five-field JSON is unchanged; coordinate new frontend
  architecture integration with Member 3 rather than silently changing it.
- Added `backend/preview.py` to serve Member 2's route **without** creating a
  conflicting `backend/main.py`. Member 1 should register the same router once
  in the real application.
- Created a synthetic, intentionally defective `sample_repo/` with an
  obviously fake demonstration credential marker, a missing-quantity checkout
  bug, broad exception handling, absent tests, and absent root README.
  See `documentation/SAMPLE_REPO_DEMO.md` for exact scope and expectations.
- Replaced the generic root README with RepoMedic-specific setup, security,
  architecture CLI, and handoff instructions. Kept `SECURITY.MD`,
  `.gitignore`, `.bobignore`, `.env.example`, and the approved master plan
  unchanged.
- Added regression tests covering path resolution when the process CWD is
  unrelated to the project, the synthetic findings, unchanged API contract,
  architecture summary, and single router registration.
- Preserved the **approved** investigation response model: `test_generated`
  is a nonempty string and `confidence` is a finite float from 0.0 to 1.0.
  Member 1 owns implementing and registering `/api/investigate`.

## Run and verify

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-member2.txt
python -m pytest -q
python scripts/inspect_architecture.py sample_repo
python scripts/benchmark_analysis.py sample_repo
python -m uvicorn backend.preview:app --host 127.0.0.1 --port 8000
```

With Uvicorn running, in a second terminal:

```bash
curl -X POST http://127.0.0.1:8000/api/analyze
```

## Integrate into the team's app

Inside **Member 1's existing FastAPI app** (not the preview app):

```python
from backend.api.analyze import router as analyze_router
app.include_router(analyze_router)
```

Check for a prior registration to avoid duplicate routes. Member 3 should
consume the unchanged five-field `/api/analyze` response. Architecture
information currently has a CLI report only; agree on an API extension before
adding frontend UI for it.

## Safe branch update

**Keep your current `.git` folder.** Copy the fix-package contents onto
`dev-2`, review `git diff` and `git status`, run the full test suite, and
commit only the intended source changes. Do not copy the ZIP's `.git` (none is
included), Python virtual environment, caches, real `.env`, live Bob session
files, or real credentials. This code was produced in ChatGPT and does **not**
prove that IBM Bob was used; collect authentic Bob evidence separately.
