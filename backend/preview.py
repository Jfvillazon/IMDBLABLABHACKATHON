"""Standalone preview of Member 2's route; NOT the team's main backend.

Run from the repository root:
    python -m uvicorn backend.preview:app --host 127.0.0.1 --port 8000

Member 1 should mount backend.api.analyze.router once in their own FastAPI
application. Do not merge this preview into backend/main.py.
"""
from fastapi import FastAPI

from backend.api.analyze import router as analyze_router

app = FastAPI(title="RepoMedic Member 2 Preview")
app.include_router(analyze_router)