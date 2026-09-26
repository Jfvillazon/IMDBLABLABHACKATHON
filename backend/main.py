from fastapi import FastAPI

from backend.api.investigate import router as investigate_router

app = FastAPI(title="RepoMedic")

app.include_router(investigate_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
