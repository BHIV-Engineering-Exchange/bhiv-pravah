import http from 'k6/http';
import { check, sleep } from 'k6';
import { htmlReport } from "https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js";
import { textSummary } from "https://jslib.k6.io/k6-summary/0.0.1/index.js";


const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000'; //backend
const TTS_URL = __ENV.TTS_URL || 'http://localhost:8007';   //tts-service


export const options = {
  // Phase 8 Extreme Survival Simulation Profile
  stages: [
    { duration: '15s', target: 500 },  // Quick ramp to 500
    { duration: '30s', target: 500 },  // Sustain

    { duration: '15s', target: 2000 }, // Surge to 2k users (Moderate Load)
    { duration: '30s', target: 2000 }, // Sustain 2k

    // { duration: '20s', target: 5000 }, // Chaos Surge to 5k users (Heavy Stress)
    // { duration: '30s', target: 5000 }, // Sustain 5k

    // Scale down to let system recover
    { duration: '30s', target: 0 },
  ],
};

export default function () {
  const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGdtYWlsLmNvbSIsImV4cCI6MTc3OTI3MzQ0NSwiaWF0IjoxNzc4NjY4NjQ1LCJqdGkiOiJjMWM0ZDZiMi1lODI2LTQxNjctOGZjMy00OTcyOWVlMmUzY2IiLCJzZXNzaW9uX2lkIjoiYzFjNGQ2YjItZTgyNi00MTY3LThmYzMtNDk3MjllZTJlM2NiIn0.n_bRWu2O3rEofqOdQYpO1r-pBjL2UOuDFLSfK6w-5vg'; // you will get this tocken from regestering in gurukul-backend by accessing the backend swagger through port forwarding shown in ../devops/kubernetes_setup_start_up.md file

  // Test Chat Endpoint (Updated to match /api/v1/chat with RAG format)
  let chatRes = http.post(`${BASE_URL}/api/v1/chat`, JSON.stringify({
    "message": "Hii",
    "conversation_id": "abc12",
    "provider": "auto",
    "use_rag": true
  }), {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + token,
    }
  });

  console.log(`[CHAT] Status: ${chatRes.status} | Trace ID: ${chatRes.headers['X-Trace-Id']}`);
  console.log(`All Headers: ${JSON.stringify(chatRes.headers)}`);

  check(chatRes, {
    'chat is alive (not 5xx)': (r) => r.status == 200,
  });

  if (chatRes.status !== 200) {
    console.log(chatRes.status, chatRes.body);
  }

  // Test TTS Generation
  let ttsRes = http.post(`${TTS_URL}/api/generate`, {
    text: 'Validating TTS inference load'
  }, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Host': 'low.gurukul.local'
    }
  });

  check(ttsRes, {
    'tts status is robust': (r) => r.status == 200,
  });

  if (ttsRes.status !== 200) {
    console.log(ttsRes.status, ttsRes.body);
  }

  sleep(1);
}
//generate the HTML file
export function handleSummary(data) {
  return {
    "load_test_summary.html": htmlReport(data),
    stdout: textSummary(data, { indent: " ", enableColors: true }),
  };
}