# BHIV Ecosystem Integration Map

## Registered Products

| Product | Protocol | Auth | Capabilities | Status |
|---------|----------|------|-------------|--------|
| UniGuru | REST | Bearer | query, execute, notify | Registered |
| SETU | REST | API Key | query, execute, stream, sync | Registered |
| Gurukul | REST | Bearer | query, execute, notify | Registered |
| Samruddhi | REST | API Key | query, execute, notify | Registered |
| Namami Gange | REST | API Key | query, execute, stream | Registered |
| SVACS | REST | API Key | query, execute, notify | Registered |
| UCCIS | REST | Bearer | query, execute, notify, stream | Registered |
| NYAI | REST | Bearer | query, execute, stream, notify | Registered |
| Brahmanda | REST | API Key | query, execute, stream, sync | Registered |
| Bucket | Internal | Internal | query, execute, sync | Registered |
| TANTRA | REST | API Key | query, execute, stream, sync | Registered |

## Integration Architecture

```
                    ┌─────────────────┐
                    │  Adapter Registry│
                    │  (Singleton)     │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
   │UniGuru  │         │ SETU    │         │ Gurukul │
   │Adapter  │         │ Adapter │         │ Adapter │
   └────┬────┘         └────┬────┘         └────┬────┘
        │                    │                    │
   ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
   │UniGuru  │         │ SETU    │         │ Gurukul │
   │API      │         │ API     │         │ API     │
   └─────────┘         └─────────┘         └─────────┘

   (Same pattern for all 11 products)
```

## Canonical Contract

### IntegrationRequest
```json
{
  "action": "string",
  "payload": {},
  "trace_id": "string",
  "source_product": "mitra",
  "target_product": "string",
  "user_id": "string",
  "session_id": "string",
  "authority_token": "string"
}
```

### IntegrationResponse
```json
{
  "success": true,
  "data": {},
  "error": null,
  "trace_id": "string",
  "source_product": "string",
  "latency_ms": 123.45,
  "timestamp": "ISO8601"
}
```

## Environment Variables

Each product adapter reads its API URL and key from environment:

| Product | URL Variable | Key Variable |
|---------|-------------|--------------|
| UniGuru | `UNIGURU_API_URL` | `UNIGURU_API_KEY` |
| SETU | `SETU_API_URL` | `SETU_API_KEY` |
| Gurukul | `GURUKUL_API_URL` | `GURUKUL_API_KEY` |
| Samruddhi | `SAMRUDDHI_API_URL` | `SAMRUDDHI_API_KEY` |
| Namami Gange | `NAMAMI_GANGE_API_URL` | `NAMAMI_GANGE_API_KEY` |
| SVACS | `SVACS_API_URL` | `SVACS_API_KEY` |
| UCCIS | `UCCIS_API_URL` | `UCCIS_API_KEY` |
| NYAI | `NYAI_API_URL` | `NYAI_API_KEY` |
| Brahmanda | `BRAHMANDA_API_URL` | `BRAHMANDA_API_KEY` |
| TANTRA | `TANTRA_API_URL` | `TANTRA_API_KEY` |

## Adding a New Product

1. Create adapter in `app/ecosystem/adapters/<product>_adapter.py`
2. Inherit from `BaseBHIVAdapter`
3. Implement `_create_manifest()`, `query()`, `execute()`
4. Register in `adapter_registry.py` -> `register_all_adapters()`
5. Set environment variables for API URL and key
6. Adapter is automatically available via `/api/ecosystem/*` endpoints
