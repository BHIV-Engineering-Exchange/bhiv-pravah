# TANTRA Integration Guide (Automatic Zoom)

This document outlines the integration between Gurukul and the TANTRA intelligence layer.

## Overview
The integration provides distributed tracing, signal emission, and interaction memory storage without modifying Gurukul's core business logic.

## 1. Trace Propagation
Gurukul accepts an `x-trace-id` header from upstream TANTRA services. This ID is propagated through the system using `contextvars`.

- **Middleware**: `app.middleware.trace_middleware.trace_id_middleware`
- **Context Storage**: `app.core.context`
- **Logging**: All JSON logs include the `trace_id` field if present.

## 2. Signal Emission (Pravah)
Signals are emitted for critical system and user events to the Pravah adapter.

- **Adapter**: `app.services.pravah_adapter`
- **Signals emitted**:
    - `user_action`: `chat_request`, `chat_response_generated`
    - `voice_action`: `tts_request_started`, `tts_generation_success`, `vaani_tts_started`, `vaani_tts_success`, `vaani_tts_failed`
    - `agent_action`: `agent_tts_started`, `agent_tts_success`, `agent_tts_failed`
- **Target**: Written to `runtime_events.json` for ingestion by Pravah.

## 3. Memory Emission (Bucket)
Interaction data is emitted to the Bucket service to keep Gurukul stateless.

- **Adapter**: `app.services.bucket_adapter`
- **Schema**:
    ```json
    {
      "trace_id": "...",
      "user_id": "...",
      "session_id": "...",
      "action": "...",
      "outcome": "...",
      "timestamp": "..."
    }
    ```

## 4. Failure Handling
The integration is **passive**. Failure to reach Pravah or Bucket will log an error but will **not** interrupt the user's flow or the system's core execution.
