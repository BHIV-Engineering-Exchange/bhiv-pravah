require('dotenv').config();
const io = require('socket.io-client');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');

const ENGINE_SHARED_SECRET = process.env.ENGINE_SHARED_SECRET || 'engine_secret_key_2024';
const JWT_SECRET = process.env.JWT_SECRET;

// Generate engine JWT
const engineToken = jwt.sign(
  { engineId: 'test_engine_01', role: 'engine' },
  JWT_SECRET,
  { expiresIn: '1h' }
);

console.log('🔧 Engine Security Test Client\n');

const socket = io('http://localhost:3000/engine', {
  auth: { token: engineToken }
});

function createSignedMessage(payload) {
  const nonce = crypto.randomBytes(16).toString('hex');
  const ts = Date.now();
  const sig = crypto
    .createHmac('sha256', ENGINE_SHARED_SECRET)
    .update(JSON.stringify(payload) + nonce + ts)
    .digest('hex');
  
  return { payload, nonce, ts, sig };
}

socket.on('connect', () => {
  console.log('✅ Connected to engine namespace\n');
  
  // Test 1: Valid signed message
  setTimeout(() => {
    console.log('Test 1: Sending VALID signed message');
    const msg = createSignedMessage({
      job_id: 'test_job_001',
      timestamp: Date.now()
    });
    socket.emit('job_started', msg);
  }, 1000);
  
  // Test 2: Invalid signature
  setTimeout(() => {
    console.log('\nTest 2: Sending INVALID signature');
    socket.emit('job_started', {
      payload: { job_id: 'test_job_002', timestamp: Date.now() },
      nonce: crypto.randomBytes(16).toString('hex'),
      ts: Date.now(),
      sig: 'invalid_signature_123'
    });
  }, 2000);
  
  // Test 3: Replay attack (reuse nonce)
  setTimeout(() => {
    console.log('\nTest 3: Sending REPLAY (reused nonce)');
    const msg = createSignedMessage({
      job_id: 'test_job_003',
      timestamp: Date.now()
    });
    socket.emit('job_completed', msg);
    
    // Try to replay same message
    setTimeout(() => {
      console.log('  → Replaying same message...');
      socket.emit('job_completed', msg);
    }, 500);
  }, 3000);
  
  // Test 4: Expired timestamp
  setTimeout(() => {
    console.log('\nTest 4: Sending EXPIRED timestamp');
    const nonce = crypto.randomBytes(16).toString('hex');
    const ts = Date.now() - 60000; // 1 minute ago
    const payload = { job_id: 'test_job_004', timestamp: ts };
    const sig = crypto
      .createHmac('sha256', ENGINE_SHARED_SECRET)
      .update(JSON.stringify(payload) + nonce + ts)
      .digest('hex');
    
    socket.emit('job_failed', { payload, nonce, ts, sig });
  }, 4500);
  
  // Test 5: Missing fields
  setTimeout(() => {
    console.log('\nTest 5: Sending INCOMPLETE message (missing nonce)');
    socket.emit('job_progress', {
      payload: { job_id: 'test_job_005', progress: 50 },
      ts: Date.now(),
      sig: 'some_sig'
    });
  }, 5500);
  
  // Disconnect after tests
  setTimeout(() => {
    console.log('\n✅ All tests sent. Check server logs for results.');
    console.log('Expected: Test 1 accepted, Tests 2-5 rejected\n');
    socket.disconnect();
    process.exit(0);
  }, 6500);
});

socket.on('job_started_rejected', (data) => {
  console.log('  ❌ REJECTED:', data.reason);
});

socket.on('job_completed_rejected', (data) => {
  console.log('  ❌ REJECTED:', data.reason);
});

socket.on('job_failed_rejected', (data) => {
  console.log('  ❌ REJECTED:', data.reason);
});

socket.on('job_progress_rejected', (data) => {
  console.log('  ❌ REJECTED:', data.reason);
});

socket.on('connect_error', (err) => {
  console.error('❌ Connection failed:', err.message);
  process.exit(1);
});
