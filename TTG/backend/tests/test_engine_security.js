require('dotenv').config();
const crypto = require('crypto');

console.log('=== Engine Security Test Suite ===\n');

// Test 1: Valid message format
function testValidMessage() {
  const nonce = crypto.randomBytes(16).toString('hex');
  const payload = { job_id: 'test_123', status: 'completed' };
  const ts = Date.now();
  
  const sig = crypto
    .createHmac('sha256', process.env.ENGINE_SHARED_SECRET)
    .update(JSON.stringify(payload) + nonce + ts)
    .digest('hex');
  
  const message = { payload, nonce, sig, ts };
  
  console.log('Test 1: Valid Message Format');
  console.log('✓ Should succeed on first send');
  console.log('✗ Should fail on replay (nonce reuse)');
  console.log('Message structure:', { payload, nonce: nonce.substring(0, 8) + '...', sig: sig.substring(0, 16) + '...', ts });
  console.log('');
}

// Test 2: Invalid signature
function testInvalidSignature() {
  const nonce = crypto.randomBytes(16).toString('hex');
  const payload = { job_id: 'test_456', status: 'completed' };
  const ts = Date.now();
  
  const sig = 'invalid_signature_12345';
  
  console.log('Test 2: Invalid Signature');
  console.log('✗ Should be rejected (ENGINE_SIGNATURE_INVALID)');
  console.log('Message structure:', { payload, nonce: nonce.substring(0, 8) + '...', sig, ts });
  console.log('');
}

// Test 3: Expired timestamp
function testExpiredTimestamp() {
  const nonce = crypto.randomBytes(16).toString('hex');
  const payload = { job_id: 'test_789', status: 'completed' };
  const ts = Date.now() - 60000; // 1 minute ago
  
  const sig = crypto
    .createHmac('sha256', process.env.ENGINE_SHARED_SECRET)
    .update(JSON.stringify(payload) + nonce + ts)
    .digest('hex');
  
  console.log('Test 3: Expired Timestamp');
  console.log('✗ Should be rejected (ENGINE_TIMESTAMP_EXPIRED)');
  console.log('Timestamp drift: 60000ms (max allowed: 30000ms)');
  console.log('Message structure:', { payload, nonce: nonce.substring(0, 8) + '...', sig: sig.substring(0, 16) + '...', ts });
  console.log('');
}

// Test 4: Missing fields
function testMissingFields() {
  const payload = { job_id: 'test_999', status: 'completed' };
  const ts = Date.now();
  
  console.log('Test 4: Missing Required Fields');
  console.log('✗ Should be rejected (ENGINE_PACKET_INCOMPLETE)');
  console.log('Message structure (missing nonce & sig):', { payload, ts });
  console.log('');
}

// Test 5: Unauthorized job type
function testUnauthorizedJobType() {
  console.log('Test 5: Unauthorized Job Type');
  console.log('✗ Should be rejected by adapter (unauthorized jobType)');
  console.log('Allowed types: BUILD_SCENE, SPAWN_ENTITY, LOAD_ASSETS');
  console.log('Attempted type: EXECUTE_ARBITRARY_CODE');
  console.log('');
}

testValidMessage();
testInvalidSignature();
testExpiredTimestamp();
testMissingFields();
testUnauthorizedJobType();

console.log('=== Test Suite Complete ===');
console.log('\nTo run live tests:');
console.log('1. Start backend: npm start');
console.log('2. Connect mock engine with test messages');
console.log('3. Observe rejection logs in console');
