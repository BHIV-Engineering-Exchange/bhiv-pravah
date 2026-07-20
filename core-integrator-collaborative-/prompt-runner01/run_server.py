import os
import re
from typing import List, Optional
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Prompt Runner", version="2.0.0")


class GenerateRequest(BaseModel):
    prompt: str
    origin: Optional[str] = "creator"


def _extract_tasks(prompt: str) -> List[str]:
    lowered = prompt.lower()
    tasks = []
    for token, task in [
        ("summarize", "summarize_content"),
        ("plan", "create_plan"),
        ("video", "generate_video_script"),
        ("lesson", "create_lesson_plan"),
        ("simulate", "run_simulation"),
        ("game", "generate_game_blueprint"),
    ]:
        if token in lowered:
            tasks.append(task)
    return tasks or ["create_blueprint"]


def _module_for_prompt(prompt: str) -> str:
    lowered = prompt.lower()
    if "video" in lowered:
        return "video"
    if "finance" in lowered or "budget" in lowered:
        return "finance"
    if "lesson" in lowered or "education" in lowered:
        return "education"
    return "creator"


def _topic_for_prompt(prompt: str) -> str:
    match = re.search(r"about ([a-zA-Z0-9_\-\s]+)", prompt, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    return "general"


@app.get("/health")
@app.get("/")
def health():
    return {"status": "ok", "service": "prompt_runner"}


@app.post("/generate")
def generate(req: GenerateRequest):
    return {
        "prompt": req.prompt,
        "module": _module_for_prompt(req.prompt),
        "intent": "generate",
        "topic": _topic_for_prompt(req.prompt),
        "tasks": _extract_tasks(req.prompt),
        "output_format": "json",
        "product_context": req.origin or "creator",
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PROMPT_RUNNER_PORT", "8003"))
    uvicorn.run(app, host="0.0.0.0", port=port)
