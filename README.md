# RepoMedic — IBM Bob Hackathon

RepoMedic is a developer-workflow prototype with two coordinated parts:
repository diagnosis and bug investigation. This branch contains **Member 2's
static, deterministic repository-analysis engine**, its tests, and a controlled
synthetic demonstration repository. IBM Bob can be used separately for the
team's agentic investigation workflow; the analyzer does not call Bob, require
an IBM API key, execute scanned source files, or consume Bobcoins.

> **Branch integration:** This project snapshot does not include Member 1's
> completed main backend or investigation/validation endpoints, or Member 3's
> React application. The Member 2 preview below is an independent integration
> check, not a substitute for their work.

## Run Member 2 locally

Use Python 3.11 or newer. From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-member2.txt
python -m pytest -q
```

The tracked `sample_repo/` is a **deliberately broken, synthetic checkout
project**. It contains no real credentials and should never be deployed. Its
known findings and intentional checkout bug are documented in
[`documentation/SAMPLE_REPO_DEMO.md`](documentation/SAMPLE_REPO_DEMO.md).

Start a local API preview using the real Member 2 router:

```bash
python -m uvicorn backend.preview:app --host 127.0.0.1 --port 8000
```

Then from a second terminal:

```bash
curl -X POST http://127.0.0.1:8000/api/analyze
```

The response uses the **approved five-field** `/api/analyze` contract:
`repository`, `files_analyzed`, `languages`, `health_score`, and `findings`.
Its scanner reads only a *server-configured local repository*; it never accepts
arbitrary client-supplied file paths, URLs, or Git repositories. To select a
different trusted folder, set `REPOMEDIC_SAMPLE_REPO` when starting the
server. Absolute paths are supported; relative paths are resolved against the
**project root** regardless of your terminal's current directory.

For example:

```bash
REPOMEDIC_SAMPLE_REPO=sample_repo python -m uvicorn backend.preview:app \
  --host 127.0.0.1 --port 8000
```

Basic architecture information is available separately without changing the
frontend's approved API shape:

```bash
python scripts/inspect_architecture.py sample_repo
python scripts/benchmark_analysis.py sample_repo
```

The benchmark measures analyzer runtime only. Collect an actual manual-review
baseline before claiming any speed improvement. All findings are static
heuristics, not a complete security audit or a guarantee that the code works.

## Integrating with the team's backend and frontend

Member 1 should mount Member 2's router **exactly once** in the real FastAPI
application:

```python
from backend.api.analyze import router as analyze_router
app.include_router(analyze_router)
```

Member 1 retains ownership of `backend/main.py`, `/api/investigate`, and
`/api/validate`. The approved `InvestigationResponse` is defined in
`backend/models/schemas.py`: `test_generated` is a **string recommendation**
and `confidence` is a **finite float between 0.0 and 1.0**. Member 3 should use
the five-field `/api/analyze` result and coordinate any future architecture
report integration before altering its contract. Do not mount
`backend.preview.app` inside the team's application.

## Security and safe contribution

**Read [`SECURITY.MD`](SECURITY.MD) before committing.** The existing
`.gitignore` and `.bobignore` protections must not be removed or weakened.
The supplied `.env.example` is only a template; Member 2's local analyzer
requires no credentials. Other services should use environment variables,
never hardcoded keys or pasted credentials in AI conversations.

If a teammate needs an `.env` file for another service:

```bash
cp .env.example .env
# Edit .env locally. Never commit or share it.
git check-ignore -v .env
```

Before every push, inspect `git diff --cached`, avoid committing credentials
or live Bob-session data, and ensure Python's `.venv/`, `__pycache__/`, and
`*.pyc` artifacts remain untracked. Only upload approved screenshots and
redacted session summaries as evidence of **actual** Bob usage. The synthetic
source is designed to trigger a credential heuristic using an obviously fake
marker; never replace it with a genuine credential.

See [`MEMBER2_INTEGRATION.md`](MEMBER2_INTEGRATION.md) for branch-specific
handoff notes and [`documentation/HACKATHON_EXECUTION_PLAN.md`](documentation/HACKATHON_EXECUTION_PLAN.md)
for the team's execution plan.
