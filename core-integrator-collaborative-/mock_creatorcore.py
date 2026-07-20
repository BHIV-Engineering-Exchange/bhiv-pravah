"""Minimal mock CreatorCore service for local development and docker-compose testing."""
from fastapi import FastAPI

app = FastAPI(title="Mock CreatorCore")

@app.get("/system/health")
def health():
    return {"status": "healthy", "service": "mock-creatorcore"}

@app.post("/generate")
def generate(payload: dict):
    return {"status": "success", "generated_text": "mock output", "id": 1}

@app.get("/history")
def history():
    return []

@app.post("/core/feedback")
def feedback(payload: dict):
    return {"status": "ok"}

@app.get("/core/context")
def context(limit: int = 3):
    return []
