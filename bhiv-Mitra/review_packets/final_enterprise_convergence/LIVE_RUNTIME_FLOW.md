# MITRA Live Runtime Flow

## Request Processing Pipeline

### 1. Web Request Arrival
```
Client -> FastAPI Middleware
  -> Security check (API Key + Rate Limit)
  -> Route dispatch
```

### 2. Assistant Endpoint (`/api/assistant`)
```
assistant.py -> handle_assistant_request()
  -> Parse V3.0.0 schema
  -> Build authenticated user context
  -> Generate deterministic trace_id
```

### 3. Orchestrator Pipeline (assistant_orchestrator.py)
```
Stage 1: Input Normalization
  -> Handle audio/text/summarized input
  -> Normalize to text

Stage 2: Language Detection
  -> multilingual_service.get_language_metadata()
  -> Detect language, translate if needed

Stage 3: Authority Evaluation
  -> mitra_control_plane_service.evaluate()
  -> Policy Engine: Content/behavior/regional rules
  -> Behavior Validator: Canonical validation
  -> Enforcement Engine: Deterministic decision
  -> Trace logging to MongoDB bucket

Stage 4: Orchestration
  -> summary_flow.generate_summary()
  -> intent_flow.process_text()
  -> Platform detection

Stage 5: Response Generation
  -> LLM Bridge: Groq/OpenAI/Gemini/Mistral
  -> Outbound Safety Gate
  -> Response translation back to user language

Stage 6: Execution (if action detected)
  -> execution_service.execute_action()
  -> Gateway Auth: HMAC-signed token
  -> Platform executor (WhatsApp/Telegram/Email/etc.)

Stage 7: Response Assembly
  -> Build V3.0.0 response
  -> Add language metadata
  -> Add TTS audio if requested
  -> Log to bucket
  -> Return response
```

### 4. Response to Client
```
V3.0.0 Response -> JSON -> HTTP -> Client
  -> Frontend renders in ChatMessage component
  -> Optional: TTS via /api/tts
```

## Inbound Channel Flow

### WhatsApp/Telegram/Email/Instagram
```
Webhook -> inbound_handler.py
  -> Inbound Mediation Service (risk assessment)
  -> inbound_gateway.py -> process_message()
  -> Build internal V3.0.0 request
  -> handle_assistant_request() (same pipeline)
  -> Response sent back via channel executor
```

## Ecosystem Integration Flow
```
Mitra Request -> Adapter Registry
  -> Get adapter for target product
  -> Build IntegrationRequest
  -> adapter.query() or adapter.execute()
  -> HTTP call to product API
  -> IntegrationResponse returned
  -> Health tracking updated
  -> Audit logged to bucket
```

## Trace Continuity
```
Every request generates deterministic trace_id
  -> Same input = same trace_id
  -> All stages logged with same trace_id
  -> SHA-256 integrity hash per entry
  -> Replay possible via /api/replay/{trace_id}
```
