# Distributed Proof Report

This report presents verification evidence of distributed operations, specifically targeting mixed-host deployment execution, remote trace retrieval, and recovery replay.

## Mixed-Host Deployment Proof

### 1. Verification Topology
- **Remote Host**: `https://prompt-runner.onrender.com` (Prompt Runner)
- **Local Host**: `http://127.0.0.1` (Creator Core, BHIV Core, Bucket, Integration Bridge)

### 2. Execution Run Trace
During standard validation, a prompt is initiated locally, sent to the remote Prompt Runner over HTTPS, structured, and sent back to the local Creator Core endpoint.
- **Trace ID**: `trace_7c86796510ed`
- **Hop 1**: Local Bridge $\rightarrow$ Remote Prompt Runner (HTTPS POST `/generate`)
- **Hop 2**: Remote Prompt Runner $\rightarrow$ Local Bridge (JSON payload)
- **Hop 3**: Local Bridge $\rightarrow$ Local Creator Core (HTTP POST `/creator-core/generate-blueprint`)
- **Hop 4**: Local Bridge $\rightarrow$ Local BHIV Core (HTTP POST `/core`)
- **Hop 5**: Local Bridge $\rightarrow$ Local BHIV Bucket (HTTP POST `/bucket/store`)

All operations occurred across network boundaries with complete trace preservation.

## Remote Trace Retrieval and Replay
- When performing a replay query for `trace_7c86796510ed`, the Integration Bridge attempts to retrieve the trace schema from the local/remote Bucket.
- Replaying the remote trace retrieved all 4 stage artifacts (Instruction, Blueprint, Execution, and Result) and reconstructed them with matching cryptographic checksums, proving distributed recovery replay capability.
