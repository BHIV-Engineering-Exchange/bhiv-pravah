# Demo Lock Procedure & Validation Report

This document records the final certified states and inputs for the Live Task Review Agent demo.

## 1. Primary Demo URLS
- **Frontend**: [http://localhost:8501](http://localhost:8501)
- **Backend API**: [http://localhost:8000](http://localhost:8000)

## 2. Certified Demo Inputs

### Scenario A: Guaranteed PASS (Strong Input)
- **Title**: `Build a Secure Async API Gateway for User Authentication and Management`
- **Description**: `The objective is to implement a robust API gateway. Requirements include schema validation using Pydantic, security constraints for JWT, and async database connections. This task ensures production readiness by adding caching and frontend integration layers. Final success criteria: 100% test coverage and full documentation.`
- **Expected Status**: `pass`
- **Expected Score**: `~90`

### Scenario B: BORDERLINE (Moderate Input)
- **Title**: `Standardized Implementation of a basic API to handle standardized requests`
- **Description**: `The Requirement is to make it work. The objective is to handle some requests. It should connect to a database eventually. Basic security constraints apply.`
- **Expected Status**: `borderline`
- **Expected Score**: `~65`

### Scenario C: Guaranteed FAIL (Weak Input)
- **Title**: `Fix bug`
- **Description**: `fix the bugs in the code quickly`
- **Expected Status**: `fail`
- **Expected Score**: `~5`

### Scenario D: Validation Failure (Empty/Short)
- **Title**: `X`
- **Description**: `Y`
- **Expected Action**: Application returns 422 with full JSON contract.
- **Expected Status**: `fail`
- **Score**: `0`

## 3. Technical Stability Sign-off
- [x] **Cold Boot**: App starts with `python -m app.main`.
- [x] **Health Check**: `/health` returns `healthy`.
- [x] **Determinism**: Verified same input -> same output (via `test_determinism.py`).
- [x] **Contract**: 100% field coverage verified for all scenarios.
- [x] **Safety**: No crashes on 5MB input or special characters.
- [x] **Environment**: Verified `.env` injection for Backend/Frontend ports and URLs.
- [x] **Memory**: Verified storage cap at 1000 tasks with FIFO eviction (LRU simulation).
- [x] **CORS**: Verified `access-control-allow-origin: *` for cross-origin demo flexibility.
- [x] **Network**: Implemented 3x retry logic with 10s timeout in Frontend for demo variability.

## 4. Observer Notes for Vinayak
- Run the app via the Quick Start commands in README.
- Select scenarios from the dropdown to demonstrate deterministic evaluation.
- Show the "Failure Reasons" expander to highlight system intelligence.
- The "Recommended Next Step" is automatically generated based on the score tier.
