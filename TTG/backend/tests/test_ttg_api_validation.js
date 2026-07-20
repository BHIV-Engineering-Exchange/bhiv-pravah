/**
 * TTG API Stress Test - Backend Validation
 * Tests backend input validation via HTTP requests
 */

const http = require('http');

const BACKEND_URL = 'localhost';
const BACKEND_PORT = 3000;

console.log('🧪 TTG API Validation Test\n');

function makeRequest(text) {
  return new Promise((resolve) => {
    const data = JSON.stringify({ text });
    const options = {
      hostname: BACKEND_URL,
      port: BACKEND_PORT,
      path: '/api/ttg/compile',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': data.length
      }
    };

    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(body) });
        } catch {
          resolve({ status: res.statusCode, data: body });
        }
      });
    });

    req.on('error', (err) => resolve({ status: 0, error: err.message }));
    req.write(data);
    req.end();
  });
}

async function runTests() {
  console.log('📊 Backend Validation Tests');
  console.log('─'.repeat(50));

  const tests = [
    { name: 'Valid input', text: 'fast runner', expectSuccess: true },
    { name: 'Empty string', text: '', expectSuccess: false },
    { name: 'Too long (>500)', text: 'a'.repeat(501), expectSuccess: false },
    { name: 'XSS attempt', text: '<script>alert("xss")</script>', expectSuccess: false },
    { name: 'Special chars', text: '!@#$%^&*()', expectSuccess: false },
    { name: 'Valid with punctuation', text: 'fast runner, jump!', expectSuccess: true }
  ];

  let passed = 0;
  for (const test of tests) {
    const result = await makeRequest(test.text);
    const success = result.data?.success === true;
    const matches = success === test.expectSuccess;
    
    console.log(`${matches ? '✅' : '❌'} ${test.name}: ${result.status} - ${success ? 'Accepted' : 'Rejected'}`);
    if (matches) passed++;
  }

  console.log(`\n🎯 Result: ${passed}/${tests.length} tests passed\n`);
}

runTests().catch(console.error);
