# Truth Layer Gap Assessment

**Phase 5 — Truth Layer Maturity Report**

This report assesses the current maturity and operational readiness of the TANTRA Truth Layer (`tantra/bucket.py`) and Observability Layer (`tantra/insightflow.py`).

## 1. Current State
* **Bucket (Truth Layer):** Implemented as an in-memory Python dictionary (`_store`) protected by a `threading.Lock()`. It retains a bounded capacity of `MAX_ENTRIES = 50,000`, evicting the oldest entries when the limit is reached.
* **InsightFlow (Observability):** Implemented as an in-memory Python list (`_events`) protected by a `threading.Lock()`. It retains a bounded capacity of `MAX_EVENTS = 10,000`, evicting the oldest entries.

## 2. Failure Modes
* **Process Termination:** A sudden crash or deliberate termination of the host Python process results in 100% data loss for both Bucket and InsightFlow.
* **Eviction Horizon:** Under high load, execution traces older than 50,000 runs are silently dropped from the truth ledger.
* **Out of Memory (OOM):** If execution payloads are unusually large, retaining 50,000 entries could trigger OS-level OOM kills before the eviction threshold is reached.

## 3. Restart Behavior
* **Volatile Reset:** Any system restart initiates a complete reset. The `_store` and `_events` structures are instantiated completely empty. There is no bootstrapping or recovery phase.

## 4. Replay Recovery Model
* **Session-Bound Determinism:** Replay determinism relies on the assumption that traces exist. Because the truth layer is volatile, replay validation is only possible within the lifespan of a single process session. Historical replay against past states is structurally impossible.

## 5. Persistence Gaps
* **Zero Disk Backing:** Neither system writes to disk or external storage.
* **No Write-Ahead Log (WAL):** Execution receipts are not journaled. If a crash occurs precisely after Core execution but before Bucket locking, the execution happens but the truth record vanishes, creating a "ghost execution."

## 6. Scaling Gaps
* **Single-Node Constraint:** The use of Python `threading.Lock()` permanently binds the truth layer to a single node and a single process. In a distributed multi-node deployment, truth would fragment across independent memory silos, destroying the canonical ledger.

## 7. Governance Risks
* **Audit Trail Erasure:** An in-memory store cannot serve as a legally or operationally binding audit ledger. The truth can literally be erased by restarting a container.
* **Non-Repudiation Failure:** Without persistent, unforgeable storage, there is no way to prove a historical execution occurred or defend against claims of unauthorized enforcement.

## 8. Recommended Evolution Path
* **Do NOT attempt to implement in this phase.**
* **Bucket Evolution:** Must migrate from an in-memory dictionary to a persistent transactional datastore (e.g., PostgreSQL for relational indexing, or a distributed KV store like Redis/DynamoDB) to guarantee cross-node consistency and durable retention.
* **InsightFlow Evolution:** Must migrate from an in-memory list to an asynchronous external sink (e.g., Kafka, OpenTelemetry collector) to decouple observability from host memory constraints.
