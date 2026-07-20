# Prompt Runner Integration - Complete

## ✅ What Was Created

### 1. New Module: `backend/prompt_runner/`
```
backend/prompt_runner/
├── adapter.js       - Core adapter (API calls + conversion)
├── index.js         - Module exports
└── README.md        - Documentation
```

### 2. New Routes in `coreExecution.js`
- **POST `/core/execute-from-text`** - Accept natural language prompt
- **POST `/core/execute-from-prompt`** - Accept Prompt Runner output (5 fields)
- **GET `/core/prompt-runner-health`** - Check service availability

### 3. Test File
- `backend/test_prompt_runner.js` - Integration tests

## 🔧 How It Works

### Flow 1: Natural Language → Execution
```
User sends prompt
    ↓
POST /core/execute-from-text
    ↓
callPromptRunner() → External Prompt Runner API
    ↓
convertToExecutionSchema() → Add execution_id, trace_id
    ↓
storeExecution() → Registry
    ↓
dispatchExecution() → Job Queue → Engine
```

### Flow 2: Direct Prompt Runner Output → Execution
```
User sends {module, intent, topic, tasks, output_format}
    ↓
POST /core/execute-from-prompt
    ↓
convertToExecutionSchema() → Add execution_id, trace_id
    ↓
storeExecution() → Registry
    ↓
dispatchExecution() → Job Queue → Engine
```

## 🚀 Usage Examples

### Example 1: Natural Language
```bash
curl -X POST http://localhost:3000/core/execute-from-text \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a fast runner game with obstacles",
    "user_id": "user123"
  }'
```

### Example 2: Prompt Runner Output
```bash
curl -X POST http://localhost:3000/core/execute-from-prompt \
  -H "Content-Type: application/json" \
  -d '{
    "module": "creator",
    "intent": "generate_game",
    "topic": "endless runner",
    "tasks": ["setup_scene", "spawn_player"],
    "output_format": "step_by_step_guide",
    "user_id": "user123"
  }'
```

### Example 3: Health Check
```bash
curl http://localhost:3000/core/prompt-runner-health
```

## 🧪 Testing

```bash
# Terminal 1: Start backend
cd backend
npm start

# Terminal 2: Run tests
node test_prompt_runner.js
```

## 📝 Environment Variables

Add to `backend/.env`:
```bash
PROMPT_RUNNER_URL=http://127.0.0.1:8001
```

## ⚠️ Important Notes

1. **No Breaking Changes** - Old `intent-layer/` still works for TTG routes
2. **Coexistence** - Both systems work independently
3. **External Service** - Requires Prompt Runner service running on port 8001
4. **Fallback** - If Prompt Runner unavailable, use `/execute-from-prompt` with pre-formatted data

## 🔄 Format Conversion

### Input (Prompt Runner - 5 fields)
```json
{
  "module": "creator",
  "intent": "generate_game",
  "topic": "endless runner",
  "tasks": ["setup_scene"],
  "output_format": "step_by_step_guide"
}
```

### Output (Execution Schema)
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
    "tasks": ["setup_scene"],
    "output_format": "step_by_step_guide",
    "context": { "source": "prompt_runner" }
  },
  "timestamp": 1234567890
}
```

## 📦 Dependencies Added
- `uuid` - For generating unique execution IDs
- `axios` - Already installed (for HTTP calls)

## ✅ Ready to Use!

The integration is complete and ready for testing. No existing functionality was broken.
