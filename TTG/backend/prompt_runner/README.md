# Prompt Runner Integration

Adapter for external Prompt Runner service that converts natural language to execution schemas.

## Architecture

```
User Prompt → Prompt Runner Service → Adapter → Execution Registry → Job Queue → Engine
```

## Files

- `adapter.js` - Core adapter logic (API calls + conversion)
- `index.js` - Module exports

## Environment Variables

```bash
PROMPT_RUNNER_URL=http://127.0.0.1:8001  # Default
```

## API Endpoints

### POST `/core/execute-from-text`
Accept natural language prompt, call Prompt Runner, convert to execution.

**Request:**
```json
{
  "prompt": "Create a fast runner game with obstacles",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "success": true,
  "execution_id": "exec_1234567890_abc123",
  "trace_id": "trace_1234567890",
  "status": "received"
}
```

### POST `/core/execute-from-prompt`
Accept Prompt Runner output directly (5 fields).

**Request:**
```json
{
  "module": "creator",
  "intent": "generate_game",
  "topic": "endless runner",
  "tasks": ["setup_scene", "spawn_player"],
  "output_format": "step_by_step_guide",
  "user_id": "user123"
}
```

### GET `/core/prompt-runner-health`
Check if Prompt Runner service is available.

**Response:**
```json
{
  "success": true,
  "healthy": true,
  "url": "http://127.0.0.1:8001"
}
```

## Testing

```bash
# Start backend
cd backend
npm start

# In another terminal, run tests
node test_prompt_runner.js
```

## Format Mapping

### Prompt Runner Output (5 fields)
```json
{
  "module": "creator",
  "intent": "generate_game",
  "topic": "endless runner",
  "tasks": ["setup_scene", "spawn_player"],
  "output_format": "step_by_step_guide"
}
```

### Converted to Execution Schema
```json
{
  "execution_id": "exec_1234567890_abc123",
  "trace_id": "trace_1234567890",
  "user_id": "user123",
  "executionSchema": {
    "module": "creator",
    "intent": "generate_game",
    "data": {
      "topic": "endless runner",
      "parameters": {},
      "original_prompt": "endless runner"
    },
    "tasks": ["setup_scene", "spawn_player"],
    "output_format": "step_by_step_guide",
    "context": {
      "source": "prompt_runner"
    }
  },
  "timestamp": 1234567890
}
```

## Notes

- Old `intent-layer/` still exists for backward compatibility with TTG routes
- New Prompt Runner adapter is separate and doesn't affect existing code
- Both systems can coexist
