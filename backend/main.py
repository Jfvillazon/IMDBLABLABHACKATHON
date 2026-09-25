from fastapi import FastAPI

app = FastAPI(title="RepoMedic")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
