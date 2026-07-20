# Secrets Management

## 1. Where Secrets Live

- **Development**: `.env` in project root (or backend folder). Add `.env` to `.gitignore`; never commit.
- **Production**: Use a secret manager (e.g. Render env vars, AWS Secrets Manager, HashiCorp Vault) and inject as environment variables. The app reads via `settings` (pydantic-settings from `os.environ` and optional `.env`).

## 2. Required Secrets (Examples)

- `DATABASE_URL` – main/tenant DB connection string
- `CENTRAL_DATABASE_URL` – tenant registry DB (when multi-tenant)
- `JWT_SECRET_KEY` – strong random string for signing JWTs
- Any third-party API keys (e.g. `GROQ_API_KEY`, `OPENAI_API_KEY`)

## 3. Practices

- No default production values for secrets in code; fail fast at startup if a required secret is missing in production.
- Rotate credentials periodically; support rotation without code change by reading from env/secret manager.
