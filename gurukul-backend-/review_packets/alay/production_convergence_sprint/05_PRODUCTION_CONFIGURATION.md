# Production Configuration Parameters

This document specifies the mandatory configuration parameters required to bootstrap the hardened Gurukul Observability runtime.

## 1. Relational Database Setup
Local SQLite fallback paths are permanently disabled. All deployments must provide a valid PostgreSQL connection string:
* **Key:** `DATABASE_URL`
* **Format:** `postgresql://<user>:<password>@<host>:<port>/<database_name>`
* **Central database key:** `CENTRAL_DATABASE_URL` (for multitenant router registration)

## 2. Telemetry Event Signing
To sign signals and verify data provenance at the Pravah Gateway:
* **Key:** `TANTRA_API_KEY`
* **Type:** Cryptographic HMAC key string
* **Validation:** Contract validation fails immediately with `ContractViolationError` if this key is missing or blank.

## 3. Vector Knowledge Base Configuration
For Balbharti and NCERT curriculum grounding:
* **Vector Store Backend:** `chromadb`
* **Collection Name:** `knowledge_base`
* **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (run locally in sovereign environments)

## 4. Inference Engine Parameters
For query processing and generation:
* **Model Name:** `llama-3.3-70b-versatile` (or the local sovereign candidate)
* **Temperature:** `0.0` (to enforce determinism)
* **Max Tokens:** `1024`
* **Endpoint URL:** Defined in `LOCAL_LLAMA_API_URL` or fallback endpoints.
