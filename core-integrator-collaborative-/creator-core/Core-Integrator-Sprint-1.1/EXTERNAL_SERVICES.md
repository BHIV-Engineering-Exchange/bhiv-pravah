# Core Integrator - External Services Integration

This document describes how Core Integrator integrates with external BHIV services.

## Service Architecture

```
┌──────────────────────────┐
│  Prompt Runner (8003)    │ - Converts prompts to instructions
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│  Core Integrator (8000)  │ - Generates blueprints from instructions
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│  BHIV Core (8001)        │ - Executes blueprints
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│  Bucket (8005)           │ - Stores artifacts
└──────────────────────────┘
```

## Configuration

All external service URLs are configured via environment variables in `.env` file.

### Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | Core Integrator API port |
| `HOST` | 0.0.0.0 | Core Integrator API host |
| `DB_PATH` | data/context.db | Local database path |
| `GROQ_API_KEY` | - | Groq API key for LLM |
| `PROMPT_RUNNER_URL` | http://localhost:8003 | Prompt Runner service URL |
| `BHIV_CORE_URL` | http://localhost:8001 | BHIV Core service URL |
| `BUCKET_URL` | http://localhost:8005 | Bucket service URL |
| `INTEGRATION_BRIDGE_URL` | http://localhost:8004 | Integration Bridge URL |
| `ENABLE_BHIV_FORWARD` | false | Enable automatic forwarding to BHIV Core |
| `LOG_LEVEL` | INFO | Logging level |

## Blueprint Generation & Forwarding

### Default Behavior (Local Mode)
By default, `ENABLE_BHIV_FORWARD=false`:
- Blueprint is generated and returned to client
- Blueprint is saved locally to `db/creator_core_bucket/`
- No automatic forwarding to BHIV Core
- Safe for development and local testing

### Enable Remote Execution (Production Mode)
Set `ENABLE_BHIV_FORWARD=true`:
- Blueprint is generated
- Blueprint is automatically forwarded to BHIV Core (`BHIV_CORE_URL`)
- BHIV Core executes the blueprint
- Response includes both blueprint and execution result

## API Endpoints

### Generate Blueprint
**POST** `/creator-core/generate-blueprint`

Request:
```json
{
    "prompt": "Explain Newton's laws of motion",
    "module": "education",
    "intent": "explain_concept",
    "topic": "physics",
    "tasks": ["define_first_law", "provide_examples"],
    "output_format": "step_by_step_guide",
    "product_context": "creator_core"
}
```

Response (default):
```json
{
    "blueprint": {
        "instruction_id": "...",
        "intent_type": "...",
        "target_product": "...",
        "payload": "..."
    }
}
```

Response (with forwarding enabled):
```json
{
    "blueprint": { ... },
    "core_response": {
        "status": "success/error",
        "message": "...",
        "result": { ... }
    }
}
```

## Deployment Scenarios

### Local Development
```bash
# Use defaults - all services on localhost
cp .env.example .env
# Keep ENABLE_BHIV_FORWARD=false for safety
python -m uvicorn main:app --reload
```

### Production with Remote Services
```bash
cp .env.example .env
# Update URLs to point to your production services
PROMPT_RUNNER_URL=https://prompt-runner.onrender.com
BHIV_CORE_URL=https://bhiv-core.example.com
BUCKET_URL=https://bucket.example.com
ENABLE_BHIV_FORWARD=true  # Enable if you want auto-forwarding
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Distributed Services (Different Hosts)
```bash
# Example: Services on different machines
PROMPT_RUNNER_URL=http://prompt-runner-host:8003
BHIV_CORE_URL=http://bhiv-core-host:8001
BUCKET_URL=http://storage-host:8005
INTEGRATION_BRIDGE_URL=http://bridge-host:8004
```

## Service Integration Points

### With Prompt Runner
- Core Integrator accepts instructions in Prompt Runner's instruction format
- Converts to deterministic blueprint envelopes
- Maintains compatibility with Prompt Runner's output schema

### With BHIV Core
- Forwards blueprints for execution (if enabled)
- Receives execution results
- Includes response in API response

### With Bucket
- Stores persisted blueprints locally
- Can be integrated with remote bucket for distributed storage
- Telemetry events written to `db/creator_core_telemetry/`

## Health Check

```bash
curl http://localhost:8000/docs
# Opens Swagger UI with all endpoints
```

## Troubleshooting

### Blueprint Generation Fails
- Check `GROQ_API_KEY` is set correctly
- Verify request JSON schema matches examples

### BHIV Core Forwarding Fails
- Verify `ENABLE_BHIV_FORWARD=true`
- Check `BHIV_CORE_URL` is correct and service is running
- Review logs for network errors

### Database Errors
- Check `DB_PATH` directory exists and is writable
- Ensure `data/` directory has proper permissions
