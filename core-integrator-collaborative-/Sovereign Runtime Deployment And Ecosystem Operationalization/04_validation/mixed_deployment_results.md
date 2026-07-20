# Mixed Deployment Results

**Status:** not executed in this sprint session  
**Classification:** documented procedure only

## Intended scenario

Some services local, some remote (e.g. Bucket + Integration Bridge remote, BHIV Core local), proving cross-network trace propagation.

## Prerequisites

- All service URLs set via env vars (`PROMPT_RUNNER_URL`, `BHIV_CORE_URL`, etc.)
- Shared `AUTH_API_KEY` across hosts
- Bucket reachable from Integration Bridge over network

## Pass/fail

- **NOT RUN** — requires provisioned remote host; local-only validation completed instead
