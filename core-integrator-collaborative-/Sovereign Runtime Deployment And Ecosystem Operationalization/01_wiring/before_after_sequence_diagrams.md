# Before/After Sequence Diagrams

## Before

`Prompt Runner -> Creator Core -> BHIV Core -> Bucket`

## After

`Prompt Runner -> Creator Core -> CET -> Sarathi -> Gate (authorize) -> BHIV Core (execute) -> Bucket`

## Execution path rule

- Gate is an authorization checkpoint.
- BHIV Core is the single executor.
- This avoids double execution between `Gateway.process_request()` and `ExecutionGate._execute_contract()`.
