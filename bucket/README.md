# BHIV Bucket - Remote Access Guide

This document provides the necessary endpoints and instructions for remote integration with the BHIV Bucket.

## 🌐 Public Access URL
The backend is currently hosted via ngrok:
**`https://slapstick-ditch-raving.ngrok-free.dev`**

---

## 🛠 Critical Endpoints

### 1. Get Latest Hash (Verification)
Used for SVACS bucket verification to retrieve the current head of the hash chain.
- **URL:** `GET /bucket/latest-hash`
- **Example:** `https://slapstick-ditch-raving.ngrok-free.dev/bucket/latest-hash`
- **Response:**
  ```json
  {
    "last_hash": "...",
    "artifact_count": 123
  }
  ```

### 2. Write Artifact (Contract)
Standard endpoint for maritime signal ingestion and general artifact storage.
- **URL:** `POST /bucket/artifacts/write`
- **Headers:** `Content-Type: application/json`
- **Body Schema:**
  ```json
  {
    "requester_id": "core_service",
    "integration_id": "bhiv_core",
    "artifact": {
      "artifact_id": "unique-id",
      "timestamp_utc": "2026-05-15T12:00:00Z",
      "schema_version": "1.0.0",
      "source_module_id": "module-name",
      "artifact_type": "signal_ingestion",
      "parent_hash": "LAST_HASH_HERE",
      "payload": { ... }
    }
  }
  ```

### 3. Health Check
Verify system status and connected services (MongoDB, Redis).
- **URL:** `GET /health`
- **Example:** `https://slapstick-ditch-raving.ngrok-free.dev/health`

### 4. Interactive API Documentation
Full documentation of all governance and storage endpoints.
- **URL:** `GET /docs`
- **Example:** `https://slapstick-ditch-raving.ngrok-free.dev/docs`

---

## 🔐 Governance & Security
- **Append-Only Enforcement:** All writes are immutable and cryptographically chained.
- **CORS:** Currently configured to allow all origins (`*`) for remote testing flexibility.
- **Sovereignty:** All hashes are server-computed; client-provided hashes are ignored for chain integrity.

---
*Created by Antigravity on behalf of Soham/Siddhesh.*
