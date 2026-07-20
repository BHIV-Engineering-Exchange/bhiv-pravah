# Prompt Runner 

Prompt Runner converts free-form natural-language prompts into a deterministic, schema-first JSON instruction using the Groq LLM. The service is designed for automation pipelines that require a compact and reliable instruction format.

---

**Repository layout (important files)**

- `api.py` — FastAPI service exposing `/generate`, `/health`, `/schema`, `/models`
- `llm_adapter.py` — Groq client, prompt construction, sanitization, and JSON extraction
- `streamlit_app.py` — optional developer UI for local testing
- `validate_integration.py` — integration / contract validator used in CI
- `requirements.txt` — Python dependencies
- `.gitattributes` / `.gitignore` — repository normalization and ignores
- `plugins/` — domain plugins (architecture, finance, healthcare, legal, software, general)
- JSON schema and contract files: `contract.json`, `instruction_schema.json`, `run_schema.json`

---

**Project purpose**

Provide a small, dependable LLM-backed API that:
- Always returns exactly five fields in JSON: `module`, `intent`, `topic`, `tasks`, `output_format`.
- Produces `tasks` as a flat array of snake_case strings (no numeric step prefixes).
- Uses Groq as the only LLM backend (no rule-based fallback).
- Includes sanitizers to normalize tasks and enforce schema.

---

## Quick Start (Windows & PowerShell)

1) Clone (if not already)

```powershell
cd %USERPROFILE%\Desktop
git clone https://github.com/siddheshnarkar76/prompt-runner01.git
cd prompt-runner01
```

2) Create and activate a virtual environment

```powershell
python -m venv .venv
# PowerShell
.\.venv\Scripts\Activate.ps1
# or cmd
.\.venv\Scripts\activate.bat
```

3) Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

4) Provide your Groq API key (local development)
Create a file `.env.local` in the project root (this file is gitignored). Add:

```
GROQ_API_KEY=gsk_your_real_key_here
```

Alternatively set environment variables in your shell:

```powershell
$env:GROQ_API_KEY = 'gsk_your_real_key_here'
```

5) Run the API (development)

```powershell
# runs on http://127.0.0.1:8001
python -m uvicorn api:app --host 127.0.0.1 --port 8001 --reload
```

6) Optional: Run the Streamlit UI (developer convenience)

```powershell
python -m streamlit run streamlit_app.py --server.port 8501
# open http://localhost:8501
```

---

## API Endpoints

- POST `/generate` — Generate the instruction
  - Request body (JSON):
    - `prompt` (string, required)
    - `model` (string, optional override)
  - Response (JSON): exactly:
    - `module` (string)
    - `intent` (string)
    - `topic` (string)
    - `tasks` (array of snake_case strings)
    - `output_format` (string)

- GET `/health` — Returns health and Groq availability
- GET `/schema` — Returns the JSON Schema for the 5-field output
- GET `/models` — Returns list of available Groq models and default

Example curl usage

```bash
curl -sS -X POST http://127.0.0.1:8001/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Create a workflow to manage early stage diabetes patients"}'
```

Example expected output

```json
{
  "module": "workflow",
  "intent": "diagnosis_and_management",
  "topic": "early_stage_diabetes",
  "tasks": ["patient_screening","blood_glucose_testing","dietary_advice"],
  "output_format": "step_by_step_guide"
}
```

---

## Validation & Tests

A helper script `validate_integration.py` verifies contract compliance, plugin loading, and domain behavior. Use it locally and in CI.

```powershell
python validate_integration.py
```

The script reports a pass/fail summary for a variety of checks. Fix failing checks before merging changes.

---

## CI (GitHub Actions) — recommended

Create `.github/workflows/ci.yml` (example below). Store `GROQ_API_KEY` as a repository secret in GitHub so the CI can run any checks requiring Groq access.

Example minimal CI workflow:

```yaml
name: CI
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: python -m pip install -r requirements.txt
      - name: Run integration validation
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
        run: python validate_integration.py
```

Add the secret on GitHub: Repository → Settings → Secrets → Actions → New repository secret → name `GROQ_API_KEY`.

---

## Deployment notes

- For production, run the FastAPI app behind a process manager (systemd, Docker, or a container orchestration platform).
- Use `uvicorn` with multiple workers behind a reverse proxy (NGINX) or use an ASGI-capable host.
- Do not commit `.env.local` — use environment variables or a secrets manager in production.

---

## Development tips

- Keep `tasks` output stable and predictable; the sanitizer enforces snake_case and strips numeric prefixes.
- If you change the instruction schema, update `instruction_schema.json` and `contract.json` and run `validate_integration.py`.
- Use `git` with care: when pushing to a remote that other collaborators have changed, prefer `git pull --rebase` and resolve conflicts rather than force-pushing.

---

## Troubleshooting

- `403` on push: re-check remote URL, authentication method (PAT vs SSH), and PAT scopes. Clear Windows Credential Manager entries and retry.
- `port in use` when starting `uvicorn`: either stop the existing process or choose another port.
- `Streamlit file not found`: ensure `streamlit_app.py` exists and you're in the project root.

---

## Contributing

- Open an issue to discuss substantial changes.
- Create a feature branch, write tests/validation, run `validate_integration.py`, and open a PR.

---

## License

Include a `LICENSE` file (e.g., MIT) if you plan to open-source the project. If you want, I can add a standard MIT `LICENSE` file for you.

---

If you'd like, I will write this `README.md` into your repository now (overwrite or create), and add a CI workflow file. Which do you prefer?
