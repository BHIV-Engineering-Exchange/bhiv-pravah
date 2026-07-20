# Prompt Runner Upgrade Notes

## What changed

- Replaced `prompt-runner01/run_server.py` HTTP stub with a FastAPI service.
- Preserved `/health` and `/generate` contract.
- Added prompt-to-instruction extraction heuristics for:
  - module selection
  - task extraction
  - topic extraction
  - product context propagation

## Unit tests

Command:
- `python -m pytest tests/test_prompt_runner_service.py`

Result:
- `3 passed`

## Real prompt -> instruction examples

1) Prompt: `Create a video lesson about Python basics`
- module: `video`
- tasks include: `generate_video_script`

2) Prompt: `Build a project plan`
- module: `creator`
- tasks: `create_plan`

3) Prompt: `Create a lesson plan about recursion with quiz`
- module: `education` (or creator fallback depending keyword parse)
- tasks include: `create_lesson_plan`
