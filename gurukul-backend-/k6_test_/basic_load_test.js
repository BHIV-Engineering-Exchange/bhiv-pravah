import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:6000';
const TTS_URL = __ENV.TTS_URL || 'http://localhost:8007';

export const options = {
  scenarios: {
    basic_load_test: {
      executor: 'shared-iterations',
      vus: 5,               // 5 concurrent users (satisfies 5-10 parallel requests)
      iterations: 50,       // 50 total requests
      maxDuration: '30s',
    },
  },
};

export default function () {
  // 1. Test Backend Health Endpoint
  let backendHealth = http.get(`${BASE_URL}/system/health`);
  check(backendHealth, {
    'Backend Health status is 200': (r) => r.status === 200,
  });

  // 2. Test Backend Metrics Endpoint
  let backendMetrics = http.get(`${BASE_URL}/system/metrics`);
  check(backendMetrics, {
    'Backend Metrics status is 200': (r) => r.status === 200,
  });

  // 3. Test TTS Service Health Endpoint
  let ttsHealth = http.get(`${TTS_URL}/api/health`);
  check(ttsHealth, {
    'TTS Health status is 200': (r) => r.status === 200,
  });

  sleep(0.1); // Small pacing delay
}
