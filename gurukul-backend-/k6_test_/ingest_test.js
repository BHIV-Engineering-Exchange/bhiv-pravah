import http from 'k6/http';

export default function () {
  const url = `${__ENV.BASE_URL || 'http://127.0.0.1'}/api/v1/bucket/prana/ingest`;

  // FIXED PAYLOAD: Sum of active_seconds + idle_seconds + away_seconds must be exactly 5.0
  const payload = JSON.stringify({
    "user_id": "audit-user-123",
    "timestamp": "2024-05-13T12:00:00Z",
    "cognitive_state": "FOCUS",
    "active_seconds": 5.0,
    "idle_seconds": 0.0,
    "away_seconds": 0.0,
    "raw_signals": { "heart_rate": 75 }
  });

  const params = {
    headers: { 'Content-Type': 'application/json' },
  };

  let res = http.post(url, payload, params);
  console.log(`[INGEST] Status: ${res.status} | Trace ID: ${res.headers['X-Trace-Id']}`);
}
