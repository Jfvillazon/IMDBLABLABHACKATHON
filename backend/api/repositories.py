"""Repository-scoped HTTP API. Paths and execution policy are never client inputs."""
from contextlib import contextmanager
import asyncio
import tempfile
import threading
import time

from fastapi import APIRouter, HTTPException, Request, Response
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

from backend.models.repositories import (
    GithubRequest, RepositoryDescriptor, RepositoryIssue, ScopedAnalysis,
    ScopedInvestigation, ScopedValidation, ScopedWorkflow,
)
from backend.services import repository_operations as operations
from backend.services.repository_import import import_github, import_zip, MAX_UPLOAD
from backend.services.workspaces import RepositoryError, WorkspaceRegistry
from backend.services.repository_upload import multipart_file

router = APIRouter(prefix="/api/repositories", tags=["repositories"])
_registry_lock = threading.Lock()


def registry(request):
    # Lazy initialization also supports TestClient without a lifespan context.
    with _registry_lock:
        current = getattr(request.app.state, "repositories", None)
        if current is None or current.closed:
            current = WorkspaceRegistry()
            request.app.state.repositories = current
        return current


@contextmanager
def api_errors():
    try:
        yield
    except RepositoryError as exc:
        raise HTTPException(exc.status, exc.message) from None
    except ValueError:
        raise HTTPException(422, "Invalid repository request") from None
    except OSError:
        raise HTTPException(503, "Repository operation temporarily unavailable") from None


async def empty_body(request):
    if await request.body():
        raise HTTPException(422, "This operation accepts no request body")
    if request.query_params:
        raise HTTPException(422, "Query parameters are not supported")


@router.post("/demo", response_model=RepositoryDescriptor, status_code=201)
async def demo(request: Request):
    await empty_body(request)
    with api_errors():
        return registry(request).demo().descriptor()


@router.post("/github", response_model=RepositoryDescriptor, status_code=201)
def github(body: GithubRequest, request: Request):
    if request.query_params:
        raise HTTPException(422, "Query parameters are not supported")
    with api_errors():
        return import_github(registry(request), body.url).descriptor()


@router.post("/zip", response_model=RepositoryDescriptor, status_code=201,
             openapi_extra={"requestBody": {"required": True, "content": {
                 "multipart/form-data": {"schema": {"type": "object", "required": ["file"],
                     "additionalProperties": False, "properties": {
                         "file": {"type": "string", "format": "binary"}}}}}}})
def upload(request: Request):
    if request.query_params:
        raise HTTPException(422, "Query parameters are not supported")
    with api_errors():
        current = registry(request)
        with multipart_file(request.scope["repomedic.body"], request.headers.get("content-type", ""),
                            current.root / "staging") as (archive, filename):
            result = import_zip(current, archive, filename)
            return result.descriptor()


@router.get("/{repository_id}", response_model=RepositoryDescriptor)
def describe(repository_id: str, request: Request):
    with api_errors(), registry(request).lease(repository_id) as workspace:
        return workspace.descriptor()


@router.delete("/{repository_id}", status_code=204)
def delete(repository_id: str, request: Request):
    with api_errors():
        registry(request).delete(repository_id)
    return Response(status_code=204)


@router.post("/{repository_id}/analyze", response_model=ScopedAnalysis)
async def analyze(repository_id: str, request: Request):
    await empty_body(request)
    with api_errors(), registry(request).lease(repository_id) as workspace:
        result = await run_in_threadpool(operations.analyze, workspace)
        return {"repository_id": repository_id, "analysis": result}


@router.post("/{repository_id}/investigate", response_model=ScopedInvestigation)
def investigate(repository_id: str, body: RepositoryIssue, request: Request):
    if request.query_params:
        raise HTTPException(422, "Query parameters are not supported")
    with api_errors(), registry(request).lease(repository_id) as workspace:
        return {"repository_id": repository_id, "investigation": operations.investigate(workspace, body.issue)}


@router.post("/{repository_id}/validate", response_model=ScopedValidation)
async def validate(repository_id: str, request: Request):
    await empty_body(request)
    with api_errors(), registry(request).lease(repository_id) as workspace:
        result = await run_in_threadpool(operations.validate, workspace)
        return {"repository_id": repository_id, "validation": result}


@router.post("/{repository_id}/workflow", response_model=ScopedWorkflow)
def workflow(repository_id: str, body: RepositoryIssue, request: Request):
    if request.query_params:
        raise HTTPException(422, "Query parameters are not supported")
    with api_errors(), registry(request).lease(repository_id) as workspace:
        return {"repository_id": repository_id, "report": operations.workflow(workspace, body.issue)}


class RepositoryBodyLimit:
    """Bound body bytes before JSON/multipart parsing, including chunked uploads.

    At most two scoped request bodies spool concurrently. Uploaded bodies are
    buffered on private controlled storage and replayed to the framework parser.
    """
    def __init__(self, app):
        self.app = app
        self.slots = threading.BoundedSemaphore(2)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith("/api/repositories"):
            return await self.app(scope, receive, send)
        limit = MAX_UPLOAD + 1024 * 1024 if scope["path"].rstrip("/") == "/api/repositories/zip" else 16384
        headers = dict(scope.get("headers", []))
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await JSONResponse({"detail": "Invalid content length"}, 400)(scope, receive, send)
        if length < 0 or length > limit:
            return await JSONResponse({"detail": "Request body exceeds limit"}, 413)(scope, receive, send)
        if not self.slots.acquire(blocking=False):
            return await JSONResponse({"detail": "Upload capacity reached"}, 503)(scope, receive, send)
        try:
            request = Request(scope)
            storage = registry(request).root / "staging"
            with tempfile.TemporaryFile(dir=str(storage)) as body:
                total = 0
                deadline = time.monotonic() + 30
                while True:
                    try:
                        message = await asyncio.wait_for(receive(), max(0, deadline - time.monotonic()))
                    except asyncio.TimeoutError:
                        return await JSONResponse({"detail": "Request upload timed out"}, 408)(scope, receive, send)
                    if message["type"] == "http.disconnect":
                        return
                    data = message.get("body", b"")
                    total += len(data)
                    if total > limit:
                        return await JSONResponse({"detail": "Request body exceeds limit"}, 413)(scope, receive, send)
                    body.write(data)
                    if not message.get("more_body", False):
                        break
                body.seek(0)
                scope["repomedic.body"] = body
                remaining = total

                async def replay():
                    nonlocal remaining
                    data = body.read(64 * 1024)
                    remaining -= len(data)
                    return {"type": "http.request", "body": data, "more_body": remaining > 0}

                await self.app(scope, replay, send)
        except RepositoryError as exc:
            await JSONResponse({"detail": exc.message}, exc.status)(scope, receive, send)
        finally:
            self.slots.release()
