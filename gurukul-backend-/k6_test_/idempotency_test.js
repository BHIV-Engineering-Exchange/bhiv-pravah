import http from 'k6/http';
import { check } from 'k6';

// Helper to generate a random Trace ID (UUID) for testing
function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    let r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export default function () {
  const url = `${__ENV.BASE_URL || 'http://127.0.0.1'}/api/v1/bucket/prana/ingest`;
  
  const originalPayload = {
    "user_id": "tantra-audit-user",
    "timestamp": new Date().toISOString(),
    "cognitive_state": "FOCUS",
    "active_seconds": 5.0,
    "idle_seconds": 0.0,
    "away_seconds": 0.0,
    "raw_signals": { "test": "idempotency" }
  };

  const driftedPayload = Object.assign({}, originalPayload, { 
    "cognitive_state": "DRIFT_DETECTED" // <--- Changing the data but keeping the ID
  });

  const traceId = uuidv4();
  const params = {
    headers: { 
      'Content-Type': 'application/json',
      'X-Trace-Id': traceId
    },
  };

  console.log(`\n--- TANTRA PHASE 2 IDEMPOTENCY TEST ---`);
  console.log(`Trace ID: ${traceId}`);

  // TEST 1: The Original Request
  console.log(`\n1. Sending Original Request...`);
  let res1 = http.post(url, JSON.stringify(originalPayload), params);
  console.log(`[REQ 1] Status: ${res1.status}`);

  // TEST 2: Valid Idempotent Retry (Same ID, Same Data)
  console.log(`\n2. Sending Valid Retry (Same ID, Same Data)...`);
  let res2 = http.post(url, JSON.stringify(originalPayload), params);
  let json2 = res2.json();
  console.log(`[REQ 2] Status: ${res2.status} | Msg: ${json2.status}`);

  // TEST 3: Authority Drift Rejection (Same ID, DIFFERENT Data)
  console.log(`\n3. Attempting Authority Drift (Same ID, DIFFERENT Data)...`);
  let res3 = http.post(url, JSON.stringify(driftedPayload), params);
  let json3 = res3.json();
  console.log(`[REQ 3] Status: ${res3.status} | Reason: ${json3.detail.reason}`);

  // Final Verification
  check(res2, {
    'Idempotent retry accepted': (r) => r.status === 200 && r.json().status.includes('idempotent'),
  });

  check(res3, {
    'Authority drift rejected': (r) => r.status === 409 && r.json().detail.reason === 'authority_drift_detected',
  });

  if (res3.status === 409) {
    console.log("\nSUCCESS: System blocked the Authority Drift! The history remains deterministic.");
  } else {
    console.error("\nFAILED: System allowed hidden state mutation.");
  }
}
