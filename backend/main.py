from fastapi import FastAPI
import asyncio
from contextlib import asynccontextmanager

from backend.api.analyze import router as analyze_router
from backend.api.investigate import router as investigate_router
from backend.api.validate import router as validate_router
from backend.api.repositories import router as repository_router, RepositoryBodyLimit


@asynccontextmanager
async def lifespan(application):
    async def cleanup():
        while True:
            await asyncio.sleep(60)
            registry = getattr(application.state, "repositories", None)
            if registry is not None:
                await asyncio.to_thread(registry.cleanup)

    task = asyncio.create_task(cleanup())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        registry = getattr(application.state, "repositories", None)
        if registry is not None:
            registry.close()

app = FastAPI(title="RepoMedic", lifespan=lifespan)
app.add_middleware(RepositoryBodyLimit)

app.include_router(analyze_router)
app.include_router(investigate_router)
app.include_router(validate_router)
app.include_router(repository_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
