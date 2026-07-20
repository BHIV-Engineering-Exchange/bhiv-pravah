# Knowledge Transfer Minutes

## Session Summary

**Date:** 09 June 2026
**Attendees:** Siddhesh Narkar, Karan, Aman (handover lead)
**Purpose:** Transfer architecture, runtime flow, testing, replay, and deployment knowledge for the BHIV Core-Integrator system.

## Agenda

1. Executive overview of the system and goals
2. Architecture walkthrough of key components
3. Runtime execution flow from prompt to result
4. Replay and reconstruction mechanics
5. Deployment and environment setup
6. Testing and validation procedures
7. Open work, risks, and next steps
8. Q&A and acceptance statements

## Topics covered

### Architecture
- Prompt Runner role
- Creator Core role
- BHIV Core role
- Integration Bridge orchestration
- BHIV Bucket artifact storage
- Test harness representation of CET, Sarathi, and Gate
- Product targeting for TTG/TTV/Gurukul

### Runtime Flow
- Human prompt entry
- Prompt Runner instruction generation
- Creator Core blueprint envelope creation
- BHIV Core execution gateway
- Bucket trace storage
- Integration Bridge artifact chain assembly
- Replay path through bucket and core endpoints

### Deployment
- Local deployment with `start_all.py`
- Service-specific startup commands
- Environment variable configuration
- Remote deployment considerations and risks
- Health check endpoints and recovery procedures

### Testing
- Service health with `test_services.py`
- Full pipeline validation with `full_tantra_flow_test.py`
- Creator Core unit tests under `creator-core/Core-Integrator-Sprint-1.1/tests`
- Replay validation and deterministic hash checks

### Open work and risks
- Prompt Runner stub replacement
- CET/Sarathi/Gate production implementation
- Distributed replay infrastructure
- Remote end-to-end validation
- Schema and contract hardening

## Questions raised

### Q1: Is Prompt Runner production-ready?
**Answer:** No. It is currently a stub in `prompt-runner01/run_server.py` and must be replaced with a real prompt-to-instruction service.

### Q2: Where is replay recorded?
**Answer:** Replay is recorded in `bhiv_bucket/traces/` and served from `integration_bridge.py` or BHIV Core endpoints.

### Q3: What is the main startup script?
**Answer:** `python start_all.py` is the recommended startup path for local testing.

### Q4: How is Creator Core configured?
**Answer:** Creator Core uses `app_config.py` and `config/service_urls.py` to resolve service URLs.

### Q5: What happens if bucket storage fails mid-pipeline?
**Answer:** The current Integration Bridge logs a warning, and replay/persistence are compromised.

## Decisions made

- The current handover package will include all documentation in root and review packet.
- Open work will be tracked in `OPEN_WORK_REGISTER.md`.
- Acceptance statements will be recorded in the final review packet.

## Action items

- **Siddhesh:** review deployment guide and test pipeline locally
- **Karan:** verify Creator Core and BHIV Core runtime configuration
- **Aman:** finalize handover artifacts and update review packet

## Follow-up

- Formalize real Prompt Runner implementation
- Define CET/Sarathi/Gate production service contracts
- Document remote deployment environment ownership
- Confirm acceptance statements in review packet

## Notes

These minutes are based on the planned handover conversation and the current repository state. Update this file after any live session with actual timestamps and attendee confirmations.
