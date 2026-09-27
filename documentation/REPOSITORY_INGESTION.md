# Repository ingestion (Task 12)

Run RepoMedic using Python 3.9+ on POSIX (macOS/Linux) with **one Uvicorn worker**.
No database, authentication, OAuth, or new Python dependencies are required.
The system Git executable must be available in the operating system's default
executable path for GitHub imports. No Git operations are needed to start the app.

## Frontend contract

All URLs below start with `/api/repositories`:

| Method / suffix | Request | Response |
| --- | --- | --- |
| POST `/demo` | No body | 201 repository descriptor |
| POST `/github` | `{"url":"https://github.com/owner/repository"}` | 201 descriptor |
| POST `/zip` | Multipart form-data: one binary `file` part | 201 descriptor |
| GET `/{id}` | No body | 200 descriptor |
| DELETE `/{id}` | No body | 204; releases handle and imported storage |
| POST `/{id}/analyze` | No body | `{repository_id, analysis}` |
| POST `/{id}/investigate` | `{issue: "..."}` | `{repository_id, investigation}` |
| POST `/{id}/validate` | No body | `{repository_id, validation}` |
| POST `/{id}/workflow` | `{issue: "..."}` | `{repository_id, report}` |

Analysis and investigation payloads retain the existing result fields. Workflow
returns the engineering report; it does not automatically apply repairs or create
regression tests. Findings are scoped to the repository and analysis result;
the UI can supply a finding's title/description as the investigation issue.

Descriptor fields: `repository_id`, `source` (`demo`, `github`, `zip`),
`display_name`, `status` (`ready`), `created_at`, `expires_at`,
`capabilities` (`analyze`, `investigate`, `validate`), `source_details`, `warnings`.
GitHub details include the canonical URL and actual imported commit SHA.
No filesystem root is included. The frontend retains its selected ID and sends
it on each operation; there is no global selected repository or list endpoint.

Imported validation always returns:

```json
{"repository_id":"opaque-id","validation":{"tests_run":0,"passed":0,"failed":0,"status":"not_run","reason":"untrusted_repository"}}
```

Imported workflow reports use `validation_status="not_run"` and
`validation_reason="untrusted_repository"`, with explicit outcome text. Trusted
demo reports retain actual passed/failed/error results with a null reason.
Legacy `/health`, `/api/analyze`, `/api/investigate`, `/api/validate`, their
environment overrides and exact response schemas remain supported. Scoped demo
always uses the built-in `sample_repo/`, independent of those overrides.

Errors have the standard `{detail: "safe message"}` shape: 422 invalid source,
archive, or request; 413 size/count limit; 404 missing/expired handle or unavailable
public repository; 409 busy workspace; 503 capacity/storage/tool unavailable;
504 ingestion timeout; 408 request-body timeout. Failures never fall back to demo.

## Ingestion and execution boundary

GitHub accepts HTTPS repository-root URLs on github.com only, with optional
`.git` or trailing slash. Credentials, explicit ports, SSH, other hosts, queries,
fragments and branch/file URLs are rejected. Clones are anonymous, shallow,
single-branch, no-tags and no-checkout, with a clean environment, disabled
redirects/credential helpers/hooks/templates, HTTPS-only transport and process
group timeout. Files come directly from regular Git blobs; checkout filters are
never run. Symbolic links/submodules are omitted with warnings; LFS pointers are
retained with a warning. Git metadata is discarded before publication.

ZIP requests are capped before parsing, including chunked uploads. A narrow
standard-library parser accepts exactly one binary file part with bounded
headers, no preamble/epilogue and no extra fields. Upload spools and extracted
content stay in private RepoMedic storage. This avoids requiring an outdated
Python-3.9-compatible multipart package: current upstream security fixes require
Python 3.10+. See the [upstream advisory](https://github.com/Kludex/python-multipart/security/advisories/GHSA-mj87-hwqh-73pj)
and [patched release metadata](https://github.com/Kludex/python-multipart/blob/0.0.26/pyproject.toml).

ZIP preflight and actual streamed extraction reject traversal, absolute/drive/UNC
paths, backslashes, NULs, reserved names, symlinks/special files, duplicate or
case/Unicode-normalization collisions, VCS metadata, encryption and unsupported
compression. Only stored/deflated ZIPs are accepted. CRC/decompression errors
fail the import. Files are non-executable; nested archives are never unpacked.
One enclosing directory is stripped when it contains the entire project.

Imported repositories never run pytest, imports, package installation, hooks,
build commands or generated recommendations. Only the server-created demo
workspace has validation permission. `shell=False` alone is not a sandbox.
Investigation now shares bounded, nonsymlink discovery and source reading.

## Limits and lifecycle

| Resource | Limit |
| --- | --- |
| ZIP file / multipart request | 25 MiB / 26 MiB |
| Other scoped request bodies / part headers | 16 KiB / 8 KiB |
| Request-body / ZIP extraction / Git import | 30s / 30s / 60s |
| Entries / file / extracted project | 10,000 / 10 MiB / 100 MiB |
| Path depth | 30 |
| Git staging | 256 MiB soft ceiling |
| Registered repositories plus import reservations | 8 |
| Concurrent scoped requests / concurrent imports | 2 / 2 |
| Idle / maximum lifetime | 1 hour / 4 hours |

Existing analysis remains capped at 3,000 source files, 512 KiB per source file,
and 8,000 lines per file; ingestion success does not imply every file is analyzed.

`REPOMEDIC_WORKSPACE_ROOT` optionally selects an operator-owned private storage
directory (mode 0700). Default: `repomedic-workspaces-<uid>` under the OS temporary
directory. Each process owns a locked instance directory. Publication is atomic;
failed imports are removed. Operations lease workspaces, preventing cleanup
during use. Cleanup runs every minute and on access, with shutdown cleanup and
startup removal of unlocked stale instances older than four hours. Demo storage
is never deleted. IDs disappear on restart. No persistence or multiworker sharing.

Enforce a **hard filesystem/container disk quota** in deployment: polling Git
staging usage is a soft ceiling and cannot prevent transient overshoot. With
eight bounded workspaces and two import slots, retained storage is bounded, but
the OS quota is still necessary for hostile downloads. Keep storage local and
private. No-auth opaque IDs provide selection, not tenant isolation; this V1 is
intended for a controlled hackathon deployment, not a public multi-tenant service.

## Verification and Member 1 handoff

Offline integration tests use real ZIP extraction and genuine engine results
from different workspaces. Git transport is mocked, while tree validation,
materialization, publication and analysis are exercised. No Git command runs in
the default suite.

After explicit Git/network authorization, Member 1 can opt into
`tests/test_repository_api.py::test_live_public_github_import` by setting:

- `REPOMEDIC_RUN_LIVE_GITHUB=1`
- `REPOMEDIC_LIVE_GITHUB_URL=https://github.com/<owner>/<repo>`
- `REPOMEDIC_LIVE_GITHUB_FINDING_FILE=<known relative filename with a finding>`

That test genuinely clones the public repository and verifies a finding from
the supplied file. Prepare the external demo separately. Rehearse its live clone
and a separately uploaded ZIP; source descriptors and distinct IDs show the two
real ingestion paths. Neither path uses sample_repo as a fallback.

To run the full suite without writing pytest/bytecode caches into the stable
sample fixture, use `PYTHONDONTWRITEBYTECODE=1` and
`PYTEST_ADDOPTS='-p no:cacheprovider'`. Leave the live-clone opt-in disabled when
Git operations are not authorized.
