# AUDIT_FLOW

## Objective
Ensure every contract request has observable outcomes:
- request received
- request accepted (success)
- request rejected (blocked)
- request failed (failure)

## Implemented Hooks

### Request log
Each contract endpoint logs inbound request with:
- endpoint path
- generated `request_id`

### Audit middleware log
Each endpoint records operation outcomes using `audit_middleware.log_operation`:
- operation type (`CREATE`, `READ`, `QUERY`, `AUDIT_READ`)
- artifact id / query marker
- requester id
- integration id (`core_contract_api`)
- status (`success`, `blocked`, `failure`)
- error message (if any)

## Event Types
- Success:
  - write/read/query/audit-read completed.
- Rejection:
  - schema violation
  - boundary violation
  - lineage violation
  - payload too large
- Failure:
  - unexpected exception

## InsightFlow Readiness
Current logs expose enough fields for ingestion adapters:
- `timestamp`
- `operation_type`
- `artifact_id`
- `requester_id`
- `integration_id`
- `status`
- `error_message`

Suggested adapter mapping:
- `request_id` as trace correlation key
- `status` as outcome dimension
- `operation_type` as metric cardinality key

## Verification
Run:
1. valid write
2. invalid write (unknown field)
3. invalid integration id
4. read missing artifact

Then inspect:
- `/bucket/audit/read`
- existing `/audit/recent`
