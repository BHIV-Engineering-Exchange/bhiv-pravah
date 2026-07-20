## Test Scenarios

### 1. Normal Send Operations
**Scenario:** Happy path - packets sent successfully to bucket
- **Setup:** Online network, bucket endpoint available
- **Action:** Send PRANA packets via bucket bridge
- **Expected:** 
  - Packets processed in batches (up to 5 at a time, sent in parallel)
  - Successful POST to `/bucket/prana/ingest`
  - Console logs show `[PRANA][BucketBridge] success:` confirmation
  - Stats track sent count accurately

### 2. Network Offline Handling
**Scenario:** Network goes offline during operation
- **Setup:** Initially online, then simulate network disconnect
- **Action:** Continue sending packets while offline
- **Expected:**
  - Packets queued in offline queue
  - No errors thrown to UI
  - Queue size grows while offline
  - Console shows `[PRANA] Network offline` message

### 3. Retry Recovery
**Scenario:** Network comes back online after being offline
- **Setup:** Packets in offline queue due to network issues
- **Action:** Simulate network reconnect
- **Expected:**
  - Offline queue automatically processes
  - Packets sent in correct order
  - Queue empties successfully
  - Console shows `[PRANA] Network online` and processing message

### 4. Server Error Handling
**Scenario:** Bucket endpoint returns HTTP error
- **Setup:** Online network, but server returns error
- **Action:** Send packet to failing endpoint
- **Expected:**
  - 4xx errors: No retry (client error, logged and failed)
  - 5xx errors: Retries up to MAX_RETRIES (3) with exponential backoff
  - After max retries: Failed packets moved to offline queue
  - Stats show failed count incremented
  - Console shows `[PRANA][BucketBridge] HTTP error:` with details

### 5. Order Preservation
**Scenario:** Multiple packets sent in sequence
- **Setup:** Continuous packet generation
- **Action:** Monitor packet ordering
- **Expected:**
  - Packets queued in chronological order
  - Batch processing sends packets in parallel (Promise.allSettled)
  - Queue maintains order (FIFO)
  - Retries preserve original packet order

### 6. Batch Processing
**Scenario:** Multiple packets accumulate
- **Setup:** Rapid packet generation
- **Action:** Observe batching behavior
- **Expected:**
  - Groups of up to 5 packets processed together
  - Packets sent in parallel (Promise.allSettled)
  - Each packet sent as individual POST request
  - Efficient network usage with parallel requests
  - 50ms delay between batches to avoid overwhelming server

## API Endpoints

### POST /bucket/prana/ingest
**Purpose:** Receive PRANA packets from frontend (single packet per request)

**Headers:**
- `Content-Type: application/json`
- `X-CLIENT-TIMESTAMP: ISO8601` (client timestamp when request is sent)

**Payload:** Single PRANA packet object
```json
{
  "user_id": "uuid",
  "session_id": "uuid",
  "lesson_id": null,
  "system_type": "gurukul",
  "role": "student",
  "timestamp": "2026-01-15T12:45:23.456Z",
  "cognitive_state": "ON_TASK",
  "active_seconds": 5.0,
  "idle_seconds": 0.0,
  "away_seconds": 0.0,
  "focus_score": 72,
  "raw_signals": { ... }
}
```

**Note:** Backend currently accepts single packets. Batching structure exists in code but sends packets individually in parallel.

## Error Handling

### Network Errors
- Timeout: 10 seconds (AbortSignal.timeout)
- Retry: Up to 3 attempts (MAX_RETRIES) with exponential backoff
- Exponential backoff: `base * 2^(retryCount - 1)` (1s, 2s, 4s)
- Fallback: Move to offline queue after max retries (no data loss)

### HTTP Errors
- 4xx (Client errors): No retry, logged and marked as failed
- 5xx (Server errors): Retry with exponential backoff (up to 3 attempts)
- Network failures: Retry with exponential backoff
- After max retries: Packet moved to offline queue for later delivery

## Performance Metrics

### Expected Throughput
- Batch processing: Up to 5 packets processed together
- Sending: Each packet sent as individual POST request (in parallel)
- Frequency: Every 5 seconds (based on packet generation)
- Efficiency: Parallel requests reduce total send time
- Inter-batch delay: 50ms between batches to avoid overwhelming server

### Memory Usage
- Queue size: Monitored and logged
- Memory cleanup: Processed packets removed
- Offline capacity: Temporary storage only

## Integration Points

### With PRANA Packet Builder
- Receives packets every 5 seconds
- Maintains loose coupling
- Zero impact on packet generation

### With Frontend UI
- No blocking operations
- Background processing
- Error isolation