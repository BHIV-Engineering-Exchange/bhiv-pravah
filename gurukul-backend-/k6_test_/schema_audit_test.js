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
  
  // TANTRA Compliant Payload with Metadata
  const compliantPayload = {
    "user_id": "tantra-schema-audit-user",
    "timestamp": new Date().toISOString(),
    "cognitive_state": "ON_TASK",
    "active_seconds": 5.0,
    "idle_seconds": 0.0,
    "away_seconds": 0.0,
    "raw_signals": { "test": "schema_enforcement" },
    
    // --- PHASE 3: CANONICAL METADATA ---
    "schema_version": "1.0.0-TANTRA-AUDIT",
    "provenance": "k6-audit-engine-v1",
    "ownership": "authority-bhiv-admin",
    "compatibility_mode": "strict"
  };

  const traceId = uuidv4();
  const params = {
    headers: { 
      'Content-Type': 'application/json',
      'X-Trace-Id': traceId
    },
  };

  console.log(`\n--- TANTRA PHASE 3 SCHEMA ENFORCEMENT TEST ---`);
  console.log(`Trace ID: ${traceId}`);
  console.log(`Testing Schema Version: ${compliantPayload.schema_version}`);
  console.log(`Testing Provenance: ${compliantPayload.provenance}`);

  // TEST: Sending Compliant Request
  console.log(`\n1. Sending TANTRA-Compliant Request...`);
  let res = http.post(url, JSON.stringify(compliantPayload), params);
  
  console.log(`[RESULT] Status: ${res.status}`);
  
  if (res.status === 200) {
    console.log("\nSUCCESS: System accepted the compliant schema and metadata.");
    console.log("Next step: Verify the Database Provenance Audit.");
  } else {
    console.error(`\nFAILED: System rejected compliant metadata. Status: ${res.status}`);
    console.log(res.body);
  }

  check(res, {
    'Schema metadata accepted': (r) => r.status === 200,
  });
}
