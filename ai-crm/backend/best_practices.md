# 📘 Project Best Practices

## 1. Project Purpose

This project automates logistics workflows using an AI Agent with a Sense→Plan→Act pattern, a rule-based and LLM-powered chatbot for customer queries, and a human-in-the-loop review system for low-confidence actions. It exposes a secure FastAPI backend with JWT authentication and a SQLAlchemy-backed database, while also supporting legacy Excel-based data flows for the initial agent and chatbot components.

## 2. Project Structure

- Root
  - agent.py — Core Sense→Plan→Act agent reading returns.xlsx and writing restock_requests.xlsx + logs.csv
  - api_app.py — FastAPI application exposing endpoints for orders, returns, inventory, agents, procurement, delivery, and dashboard analytics
  - chatbot_agent.py — Rule-based chatbot using in-memory DataFrames loaded from Excel at import
  - smart_chatbot.py — OpenAI-powered chatbot, uses dotenv and the OpenAI SDK
  - human_review.py — Confidence scoring + pending_reviews.json + review_log.csv with a global singleton `review_system`
  - review_interface.py — CLI for human reviewers (approve/reject/stats/auto)
  - database/
    - models.py — SQLAlchemy ORM models and database initialization (SQLite by default via env DATABASE_URL)
    - service.py — Service layer (context-managed) to access and mutate domain data
  - tests/
    - test_agent.py, test_api.py, test_integration.py — Pytest suites for unit, API, and end-to-end workflows
  - auth_system.py — JWT-based auth, RBAC, in-memory user store, global `auth_system`
  - pytest.ini — Test discovery and coverage configuration
  - requirements.txt — Pinned dependencies
  - .env.example, .env.development, .env.production — Environment variable templates
  - Dockerfile, docker-compose.yml, nginx.conf — Containerization and reverse proxy
  - data/ — Excel files and CSV/JSON logs (legacy/local development data)

Conventions
- Domain logic: agent.py, human_review.py, procurement/delivery agents (if present)
- API and integration: api_app.py using database.service and auth_system
- Persistence: database/models.py and database/service.py
- Legacy/local data: data/ files used by the CLI agents and chatbots

## 3. Test Strategy

Frameworks and Config
- Pytest (+ pytest-cov, pytest-asyncio)
- Configured in pytest.ini with:
  - tests discovery under tests/
  - coverage includes project modules; excludes tests, caches, and VCS

Organization and Style
- Tests live in tests/ with files named test_*.py, classes starting with Test*, functions test_*
- Current style uses setup_method/teardown_method with temporary dirs and monkey-patched module-level constants (e.g., agent.RETURNS_FILE)
- API tests use fastapi.testclient.TestClient without authentication against legacy endpoints (/get_orders, /get_returns) for backward compatibility

Mocking and Isolation
- Use unittest.mock.patch to replace external systems (e.g., review_system, file paths, slow functions)
- For filesystem I/O, prefer tempfile to ensure isolation; patch module-level file paths before imports when needed
- For DataFrame-backed modules (chatbot_agent.py), inject DataFrames directly in tests (orders_df, restocks_df)

Unit vs Integration
- Unit tests: target pure functions (e.g., sense, plan), small scopes, patch dependencies
- Integration tests: end-to-end flows across components (agent.run_agent → excel/logs; chatbot + review escalation)
- API tests: prefer testing service layer through API endpoints; add authenticated tests for secured endpoints

Coverage Expectations
- Maintain and expand coverage for agent decision paths, human review transitions, and API error handling
- Add tests for:
  - Authentication flows (login/refresh/me) with JWT
  - DatabaseService operations (create/update/query)
  - Secured API endpoints with role/permission requirements

## 4. Code Style

General
- Python 3.8+
- Functions and variables: snake_case; Classes: PascalCase; Files: snake_case.py
- Prefer type hints for new/updated code; ensure imports from typing for clarity
- Docstrings: concise module/class/function docstrings explaining purpose and inputs/outputs

Async and FastAPI
- FastAPI endpoints can be sync or async; adopt async for I/O-heavy operations when expanding
- Use Depends for auth/permissions and service injection; keep endpoint bodies thin, deferring to service layer

Error Handling
- API: raise fastapi.HTTPException with accurate status codes; avoid leaking internal errors
- Agent and CLI: catch broad exceptions at entry points, log error context, and continue when safe
- Prefer the logging module over print for new code; for CLI UX, structured prints with emojis are acceptable, but also log to file/DB

Configuration and Environment
- Load secrets via environment variables (.env with python-dotenv in local dev). Never hardcode secrets
- Use DATABASE_URL, JWT_SECRET_KEY, and OPENAI_API_KEY from env
- Keep defaults safe for local development only; production must override via env

I/O and Data
- Avoid reading large files at import time in new modules. For existing modules (chatbot_agent.py), refactor gradually to lazy load or inject dependencies
- Prefer database.service for persistence over Excel for new features. Treat Excel files as demo/dev data sources only

Naming and Constants
- Constants at module top in UPPER_SNAKE_CASE (e.g., RETURNS_FILE, THRESHOLD)
- Keep Sense→Plan→Act function names explicit (sense, plan, act) and side-effect free except in act

## 5. Common Patterns

Architectural
- Sense→Plan→Act pipeline in agent.py
- Human-in-the-loop review via a singleton (review_system) with confidence scoring and thresholds
- Service layer as a context manager (DatabaseService) to encapsulate DB access and transactions
- API boundary in api_app.py with CORS and basic security headers middleware

Design/Code Idioms
- Dependency injection via FastAPI Depends for auth (get_current_user, require_permission, require_role)
- Error translation to HTTPException in API endpoints
- CSV/JSON logging for legacy flows; database AgentLog for API-backed flows
- Use of pandas for simple Excel pipelines; SQLAlchemy ORM models for scalable data

Testing
- Patch external dependencies (I/O, review system) and inject in-memory data for deterministic tests
- Use tempfile and restore original constants in teardown to avoid state leakage

## 6. Do's and Don'ts

Do
- Use the database service for new persistence; keep Excel usage only for legacy/demo flows
- Preserve and extend the Sense→Plan→Act separation; keep act as the only side-effecting stage
- Validate and sanitize external input; map exceptions to structured API errors
- Secure new API endpoints with JWT and role/permission checks; add tests for both authorized and unauthorized access
- Parameterize thresholds and feature flags via env/config; avoid magic numbers
- Write unit tests for pure logic and integration tests for workflows; keep coverage meaningful
- Prefer type hints and docstrings; keep function signatures small and explicit

Don't
- Don’t hardcode secrets or tokens; don’t commit real keys
- Don’t read files or create heavy objects at import time in new modules
- Don’t couple API endpoints directly to file-based I/O—go through the service layer
- Don’t break legacy endpoints (/get_orders, /get_returns) until tests and clients migrate
- Don’t swallow exceptions silently; either log or raise with context

## 7. Tools & Dependencies

Key Libraries
- FastAPI + Uvicorn — web API framework and ASGI server
- SQLAlchemy + Alembic — ORM and migrations (alembic listed; add migrations as the schema stabilizes)
- pandas + openpyxl — Excel data processing for legacy agent/chatbot
- openai + python-dotenv — LLM integration and environment loading
- pytest (+ pytest-cov, pytest-asyncio) — testing and coverage
- httpx/requests — HTTP clients for integrations
- pyjwt, bcrypt — JWT and password hashing for auth
- streamlit, plotly — dashboards (future/optional usage)

Setup
- Create and populate a virtualenv; install pinned requirements
- Copy .env.example to .env and set:
  - DATABASE_URL
  - JWT_SECRET_KEY
  - OPENAI_API_KEY
- Initialize the DB by starting the API (startup event calls init_database)

Run
- Agent (legacy Excel pipeline): `python agent.py`
- API server: `uvicorn api_app:app --reload`
- Rule-based chatbot: `python chatbot_agent.py`
- Smart chatbot (OpenAI): `python smart_chatbot.py`
- Human review CLI: `python review_interface.py`
- Tests with coverage: `pytest`

Notes
- requirements.txt pins versions; remove duplicates (e.g., streamlit listed twice) when updating

## 8. Other Notes

For LLM-generated changes
- Maintain Sense→Plan→Act separation and avoid adding side effects to sense/plan
- Prefer DatabaseService over direct SQLAlchemy session usage inside endpoints
- Keep authentication consistent: expose dependencies via auth_system wrappers (get_current_user, require_permission, require_role)
- Use environment variables for all secrets; avoid new defaults beyond local dev
- Add or update tests alongside new features; use fixtures or setup_method consistently
- Respect existing CSV/JSON file schema if touching legacy flows; log actions in a structured way
- Maintain backward compatibility for legacy endpoints used in tests until clients and tests are migrated to secured endpoints
- When adding new modules, avoid heavy initialization at import; support dependency injection for data sources
