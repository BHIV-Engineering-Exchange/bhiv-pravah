const io = require('socket.io-client');

console.log('🧪 LIVE VALIDATION & ENGINE TEST\n');
console.log('='.repeat(70));

let testsPassed = 0;
let testsFailed = 0;

// Test 1: Invalid Schema
console.log('\n📋 TEST 1: Invalid Schema Rejection');
fetch('http://localhost:3000/api/ttg/start-game', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: '' })
})
  .then(res => res.json())
  .then(data => {
    if (!data.success && data.error) {
      console.log('   ✅ PASS - Empty text rejected');
      console.log(`   📝 Error: "${data.error}"`);
      testsPassed++;
    } else {
      console.log('   ❌ FAIL - Empty text accepted');
      testsFailed++;
    }
  })
  .catch(err => {
    console.log(`   ❌ ERROR: ${err.message}`);
    testsFailed++;
  });

// Test 2: Engine Connection
setTimeout(() => {
  console.log('\n📋 TEST 2: Engine Connection Status');
  const engineSocket = io('http://localhost:3000/engine', {
    auth: { token: 'dev-bypass' }
  });

  engineSocket.on('connect', () => {
    console.log('   ✅ PASS - Engine connected');
    console.log(`   🔌 Socket ID: ${engineSocket.id}`);
    testsPassed++;
    engineSocket.disconnect();
  });

  engineSocket.on('connect_error', () => {
    console.log('   ❌ FAIL - Engine not connected');
    testsFailed++;
  });
}, 500);

// Test 3: Valid Schema + Job Dispatch
setTimeout(() => {
  console.log('\n📋 TEST 3: Valid Schema + Job Dispatch');
  
  const dashSocket = io('http://localhost:3000');
  let jobReceived = false;

  dashSocket.on('job_status', (data) => {
    if (!jobReceived) {
      jobReceived = true;
      console.log('   ✅ PASS - Job status received');
      console.log(`   📦 Job: ${data.jobId} - ${data.status}`);
      testsPassed++;
      dashSocket.disconnect();
    }
  });

  fetch('http://localhost:3000/api/ttg/start-game', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: 'Create a platformer game' })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success && data.jobs) {
        console.log('   ✅ PASS - Valid schema accepted');
        console.log(`   🎮 Jobs created: ${data.jobs.length}`);
        testsPassed++;
      } else {
        console.log('   ❌ FAIL - Valid schema rejected');
        testsFailed++;
      }
    })
    .catch(err => {
      console.log(`   ❌ ERROR: ${err.message}`);
      testsFailed++;
    });
}, 1500);

// Summary
setTimeout(() => {
  console.log('\n' + '='.repeat(70));
  console.log('📊 TEST RESULTS');
  console.log('='.repeat(70));
  console.log(`✅ Passed: ${testsPassed}`);
  console.log(`❌ Failed: ${testsFailed}`);
  console.log(`📈 Success Rate: ${Math.round((testsPassed / (testsPassed + testsFailed)) * 100)}%`);
  console.log('='.repeat(70));
  process.exit(testsFailed > 0 ? 1 : 0);
}, 4000);
