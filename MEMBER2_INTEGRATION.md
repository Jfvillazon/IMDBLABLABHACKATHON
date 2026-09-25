# RepoMedic — Member 2 branch integration

This copy is based **only on the uploaded "Hackathon copy.zip"**. It has not
been pushed to GitHub and might not include teammate changes made afterward.

## Changes made

- `backend/models/schemas.py`: the final approved `InvestigationResponse` model
  (string `test_generated`, numeric `confidence` in the closed interval [0, 1]).
- `backend/analyzers/`: a bounded, static Member 2 scanner and analyzers, a
  README check, deterministic health scoring, and the orchestration engine.
- `backend/api/analyze.py`: a working read-only `POST /api/analyze` route that
  reads only a server-chosen local repository and returns the frozen five-field
  response JSON; does not accept a user-controlled path or URL.
- `tests/`: independent analyzer/API tests and the approved investigation
  response contract tests.
- The uploaded copy of `HACKATHON_EXECUTION_PLAN.md` contained two older
  investigation responses; both were changed locally to match the team's
  approved contract. If main already has that update, keep main's version.
- `README.md`, `SECURITY.MD`, `.gitignore`, `.bobignore`, `.env.example`,
  teammates' service/frontend files and `sample_repo/` were left unchanged.

## Run locally

From the repository root:

```bash
python3 -m pip install -r requirements-member2.txt
python3 -m pytest tests/test_member2_engine.py tests/test_investigation_schema.py -q
```

If Member 1 has not yet created `backend/main.py`, run a temporary local
preview in a Python shell rather than committing a competing application:

```bash
python3 - <<'PY'
from fastapi import FastAPI
from backend.api.analyze import router
app = FastAPI()
app.include_router(router)
print([route.path for route in app.routes])
PY
```

Member 1 should import and mount the existing Member 2 router **once**:

```python
from backend.api.analyze import router as analyze_router
app.include_router(analyze_router)
```

The configured repository is `sample_repo/` relative to the project root by
default; an operator may set `REPOMEDIC_SAMPLE_REPO` to a known safe directory.
No client-supplied repository path is accepted.

## How Member 1 connects the new investigation model

There is **no investigation route** in the uploaded copy, so no replacement
route was created. Inside their existing `backend/api/investigate.py`, Member 1
should use:

```python
from backend.models.schemas import InvestigationResponse

@router.post("/api/investigate", response_model=InvestigationResponse)
def investigate(...):
    # Existing investigation service returns a dictionary with exactly the
    # approved six fields. The route's real parameters/body remain unchanged.
    ...
```

If Member 1 has independently added a `schemas.py`, merge the model definition
into their version rather than replacing teammates' code.

## Safe Git integration (no push performed here)

Inspect changes on `dev-2` and create a review branch before integrating:

```bash
git switch dev-2
git pull origin dev-2
git switch -c review/member2-approved-contract
# Overlay the code patch or cherry-pick the needed files; inspect git diff.
python3 -m pytest tests/test_member2_engine.py tests/test_investigation_schema.py -q
git diff --check
git status
```

Do not commit `.env`, actual credentials, live Bob session data, or `.git`
from the uploaded archive. Keep your team-owned `README.md`, `SECURITY.MD`,
`.gitignore` and `.bobignore` protection rules intact. Don't represent this
patch as work performed by IBM Bob; collect authentic Bob work and evidence
separately to meet the hackathon requirement.
