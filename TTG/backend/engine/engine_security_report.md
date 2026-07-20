# Engine Security Alignment 

## Overview
This document describes the security controls applied to the Engine WebSocket
bridge (`/engine`) to ensure that only trusted engines can connect, send data,
and remain connected.

The security model enforces authentication, integrity, replay protection, and
liveness guarantees for all engine communications.

---

## Engine Authentication (JWT)

All engine connections to the `/engine` namespace require a valid JSON Web Token
(JWT).

### Requirements
- JWT must be provided during socket connection.
- JWT must be signed using the server’s `JWT_SECRET`.
- JWT payload must include:
  - `engineId`
  - `role = "engine"`

### Enforcement
- Engine connections without a JWT are immediately rejected.
- Tokens with invalid signatures are rejected.
- Tokens with incorrect roles are rejected.

This ensures that only authorized engine services can establish a connection.

---

## Packet Integrity (HMAC Signature)

All engine-to-server packets are cryptographically signed.

### Packet Structure
Each engine packet includes:
- `payload` – the actual message content
- `nonce` – a unique identifier for the packet
- `sig` – HMAC-SHA256 signature

### Verification
- The server recomputes the HMAC signature using a shared secret
  (`ENGINE_SHARED_SECRET`).
- If the computed signature does not match the provided signature, the packet
  is rejected and the engine is disconnected.

This prevents packet tampering and spoofed engine messages.

---

## Replay Protection (Nonce Enforcement)

To prevent replay attacks, every engine packet must include a unique nonce.

### Rules
- Each nonce may be used only once.
- Reuse of a nonce results in immediate rejection.
- Rejected packets cause the engine connection to be terminated.

This ensures that previously captured packets cannot be resent.

---

## Heartbeat Enforcement (Liveness Detection)

Engines are required to periodically send heartbeat messages to the server.

### Behavior
- Engines emit `engine_heartbeat` events at regular intervals.
- The server tracks the time of the last received heartbeat.
- If no heartbeat is received within the allowed window, the engine is forcibly
  disconnected.

This prevents stale or dead engine connections from remaining active.

---

## Failure Handling Policy

Security enforcement follows a strict fail-fast approach.

### Policy
- Any authentication failure results in disconnect.
- Any invalid signature or nonce replay results in disconnect.
- Missing heartbeat results in disconnect.
- No partial trust is granted after a failure.

This minimizes the attack surface and ensures consistent system behavior.

---

## Audit and Observability

Engine lifecycle and security-relevant events are recorded in an append-only
log file:

- `ENGINE_CONNECTED`
- `JOB_SENT`
- `ENGINE_STATUS`
- `ENGINE_DISCONNECTED`
- Security rejection events (if applicable)

These logs provide traceability and support future replay and forensic analysis.

---

## Status

All Day 5 engine security requirements have been implemented and validated:

- JWT authentication
- Signed packets
- Nonce-based replay protection
- Heartbeat-based liveness checks
- Strict rejection of unsigned or invalid packets


