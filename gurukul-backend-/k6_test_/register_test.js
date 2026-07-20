import http from 'k6/http';
import { sleep, check } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';

export let options = {
  vus: 75,
  duration: '30s'
};

export default function () {
  const payload = JSON.stringify({
    email: "user@example.com",
    password: "string",
    full_name: "string",
    role: "STUDENT"
    });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  let res = http.post(`${BASE_URL}/api/v1/auth/register`, payload, params);

  check(res, {
    'registration successful': (r) => r.status === 201,
  });

  sleep(1);
}