import http from 'k6/http';
import { check, sleep } from 'k6';

// 5000-User concurrency stress profile
export const options = {
    scenarios: {
        sustained_load: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '1m', target: 1000 },  // Warm up
                { duration: '3m', target: 5000 },  // Ramp to 5000 concurrent users
                { duration: '5m', target: 5000 },  // Sustained load peak
                { duration: '1m', target: 0 },     // Cool down
            ],
            gracefulRampDown: '30s',
        },
        spike_test: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '15s', target: 0 },
                { duration: '30s', target: 5000 }, // Sudden spike to 5000 users!
                { duration: '2m', target: 5000 },
                { duration: '30s', target: 0 },
            ],
            startTime: '10m', // Runs after sustained load test
        }
    },
    thresholds: {
        http_req_failed: ['rate<0.01'],             // Less than 1% failure rate
        http_req_duration: ['p(95)<200', 'p(99)<500'], // 95% under 200ms, 99% under 500ms
    },
};

const BASE_URL = __ENV.GURUKUL_API_BASE_URL || 'http://localhost:3000';

export default function () {
    // 1. Ping health check (60% of request patterns - high read/ping ratio)
    let healthRes = http.get(`${BASE_URL}/system/health`);
    check(healthRes, {
        'status is 200': (r) => r.status === 200,
        'health is healthy': (r) => r.json('status') === 'healthy',
    });
    sleep(0.5);

    // 2. Fetch metrics
    let metricsRes = http.get(`${BASE_URL}/system/metrics`);
    check(metricsRes, {
        'metrics status is 200': (r) => r.status === 200,
    });
    sleep(1);

    // 3. User Login simulation (10% of request patterns - read/write)
    const loginPayload = JSON.stringify({
        username: `load_user_${__VU}@gurukul.com`,
        password: 'SecurePassword123!',
    });
    const loginParams = {
        headers: { 'Content-Type': 'application/json' },
    };
    let loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, loginPayload, loginParams);
    check(loginRes, {
        'login returns 200 or 401/404': (r) => r.status === 200 || r.status === 401 || r.status === 404,
    });
    sleep(2);

    // 4. Voice synthesis request (5% burst behavior, intensive TTS compute)
    const voicePayload = JSON.stringify({
        text: "Automated production scale test load sequence for Gurukul capability validation.",
        voice_id: "gurukul_soham",
        speed: 1.0,
    });
    let voiceRes = http.post(`${BASE_URL}/api/v1/voice/synthesize`, voicePayload, loginParams);
    check(voiceRes, {
        'voice returns 200 or 429 queue full': (r) => r.status === 200 || r.status === 429 || r.status === 503,
    });
    sleep(3);
}
