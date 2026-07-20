# PRANA Failure Matrix

## Purpose

All PRANA failure modes and behavior. PRANA fails-open: failures do not affect application functionality.

## Failure Categories

1. Signal Layer
2. State Engine
3. Packet Builder
4. Bucket Unreachable

## Signal Layer Failures

### SIG-001: Signal Collection Unavailable
**Behavior:** Emit IDLE, continue, no retry  
**Safety:** Non-blocking, no retry storms, no authority

### SIG-002: Signal Corruption
**Behavior:** Discard corrupted signals, emit IDLE, continue  
**Safety:** Non-blocking, no retry storms, no authority

### SIG-003: Signal Overload
**Behavior:** Process up to capacity, drop excess, continue  
**Safety:** Non-blocking, no retry storms, no authority

### SIG-004: Signal Source Disconnected
**Behavior:** Emit IDLE, continue, no retry  
**Safety:** Non-blocking, no retry storms, no authority

## State Engine Failures

### ENG-001: State Evaluation Exception
**Behavior:** Catch exception, emit IDLE, continue  
**Safety:** Non-blocking, no retry storms, no authority

### ENG-002: State Transition Logic Failure
**Behavior:** Fallback to IDLE, continue  
**Safety:** Non-blocking, no retry storms, no authority

### ENG-003: Observation Window Timer Failure
**Behavior:** Use fallback timing or emit IDLE continuously  
**Safety:** Non-blocking, no retry storms, no authority

## Packet Builder Failures

### PKT-001: Packet Construction Exception
**Behavior:** Skip packet, continue  
**Safety:** Non-blocking, no retry storms, no authority

### PKT-002: Packet Serialization Failure
**Behavior:** Skip packet, continue  
**Safety:** Non-blocking, no retry storms, no authority

### PKT-003: Packet Size Limit Exceeded
**Behavior:** Truncate or skip packet, continue  
**Safety:** Non-blocking, no retry storms, no authority

## Bucket Unreachable Failures

### BKT-001: Bucket Endpoint Unavailable
**Behavior:** Single attempt, discard on failure, no retry  
**Safety:** Non-blocking, no retry storms, no authority

### BKT-002: Bucket Authentication Failure
**Behavior:** Discard packet, continue, no retry  
**Safety:** Non-blocking, no retry storms, no authority

### BKT-003: Bucket Rate Limit Exceeded
**Behavior:** Discard packet, continue, no backoff  
**Safety:** Non-blocking, no retry storms, no authority

### BKT-004: Bucket Storage Full
**Behavior:** Discard packet, continue  
**Safety:** Non-blocking, no retry storms, no authority

## Failure Handling Principles

### Fail-Open Guarantee
All failures → Silent operation cessation. No application impact.

### Non-Blocking Guarantee
Failures do not block or delay application operations.

### No Retry Storms Guarantee
Single attempt only. No retries, backoff, or queues.

### No Authority Guarantee
PRANA does not request changes from other systems.

## Logging

Infrastructure-level logging only (if enabled). Logging failures do not affect PRANA behavior.
