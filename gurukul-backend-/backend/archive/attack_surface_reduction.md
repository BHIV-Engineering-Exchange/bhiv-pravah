# Backend Attack Surface Reduction

## 1. Disable Debug Routes in Production

- Do not mount `/docs`, `/redoc`, `/openapi.json` when `ENV=production` or `DEBUG=false`. FastAPI: `app = FastAPI(docs_url=None, redoc_url=None)` in prod.
- Disable uvicorn `reload=True` in production.

## 2. Disable Test Routes

- Remove or guard any route under e.g. `/test`, `/debug`, `/ping` that exposes internal state. If kept, protect with env check and/or admin-only.

## 3. Unused Endpoints

- Audit routers: remove or disable endpoints that are not used (e.g. legacy shims that duplicate functionality). Prefer versioned API (`/api/v1/...`) and avoid unversioned or duplicate paths.

## 4. Configuration

- Set `ENV=production` and ensure `DEBUG` is false on live. In startup, skip registering debug/test routes when in production.
