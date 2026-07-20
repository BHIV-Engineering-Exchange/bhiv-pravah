// test_security_enforcement.js - Test security enforcement for core execution
const crypto = require('crypto');
const { HMAC_SECRET } = require('./config');

const BASE_URL = 'http://localhost:3000/core';

console.log('🔒 Testing Security Enforcement Layer\n');

// Helper to generate signature
function generateSignature(execution_id, trace_id, executionSchema, timestamp, nonce) {
  const message = `${execution_id}|${trace_id}|${JSON.stringify(executionSchema)}|${timestamp}|${nonce}`;
  return crypto.createHmac('sha256', HMAC_SECRET).update(message).digest('hex');
}

// Test 1: Valid request with all security fields
async function test1_validRequest() {
  console.log('=== Test 1: Valid Request ===');
  
  const execution_id = `exec_secure_${Date.now()}`;
  const trace_id = `trace_secure_${Date.now()}`;
  const timestamp = Date.now();
  const nonce = crypto.randomBytes(16).toString('hex');
  
  const executionSchema = {
    game_mode: 'survival',
    movement: { speed: 5 }
  };
  
  const signature = generateSignature(execution_id, trace_id, executionSchema, timestamp, nonce);
  
  const response = await fetch(`${BASE_URL}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      execution_id,
      trace_id,
      executionSchema,
      signature,
      nonce,
      timestamp,
      user_id: 'test_user'
    })
  });
  
  const data = await response.json();
  console.log(response.status === 200 ? '✅' : '❌', 'Status:', response.status);
  console.log('Response:', data);
  console.log();
  
  return { execution_id, nonce };
}

// Test 2: Missing signature
async function test2_missingSignature() {
  console.log('=== Test 2: Missing Signature ===');
  
  const response = await fetch(`${BASE_URL}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      execution_id: 'exec_no_sig',
      trace_id: 'trace_no_sig',
      executionSchema: { game_mode: 'survival' },
      timestamp: Date.now(),
      nonce: crypto.randomBytes(16).toString('hex')
    })
  });
  
  const data = await response.json();
  console.log(response.status === 401 ? '✅' : '❌', 'Status:', response.status);
  console.log('Error:', data.error);
  console.log();
}

// Test 3: Invalid signature
async function test3_invalidSignature() {
  console.log('=== Test 3: Invalid Signature ===');
  
  const response = await fetch(`${BASE_URL}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      execution_id: 'exec_bad_sig',
      trace_id: 'trace_bad_sig',
      executionSchema: { game_mode: 'survival' },
      signature: 'invalid_signature_12345',
      nonce: crypto.randomBytes(16).toString('hex'),
      timestamp: Date.now()
    })
  });
  
  const data = await response.json();
  console.log(response.status === 401 ? '✅' : '❌', 'Status:', response.status);
  console.log('Error:', data.error);
  console.log();
}

// Test 4: Replay attack (reuse nonce)
async function test4_replayAttack(execution_id, nonce) {
  console.log('=== Test 4: Replay Attack (Reused Nonce) ===');
  
  const trace_id = `trace_replay_${Date.now()}`;
  const timestamp = Date.now();
  const executionSchema = { game_mode: 'survival' };
  
  const signature = generateSignature(execution_id, trace_id, executionSchema, timestamp, nonce);
  
  const response = await fetch(`${BASE_URL}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      execution_id,
      trace_id,
      executionSchema,
      signature,
      nonce, // Reusing nonce from test 1
      timestamp,
      user_id: 'test_user'
    })
  });
  
  const data = await response.json();
  console.log(response.status === 401 ? '✅' : '❌', 'Status:', response.status);
  console.log('Error:', data.error);
  console.log();
}

// Test 5: Expired timestamp
async function test5_expiredTimestamp() {
  console.log('=== Test 5: Expired Timestamp ===');
  
  const execution_id = `exec_expired_${Date.now()}`;
  const trace_id = `trace_expired_${Date.now()}`;
  const timestamp = Date.now() - 60000; // 60 seconds ago
  const nonce = crypto.randomBytes(16).toString('hex');
  const executionSchema = { game_mode: 'survival' };
  
  const signature = generateSignature(execution_id, trace_id, executionSchema, timestamp, nonce);
  
  const response = await fetch(`${BASE_URL}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      execution_id,
      trace_id,
      executionSchema,
      signature,
      nonce,
      timestamp
    })
  });
  
  const data = await response.json();
  console.log(response.status === 401 ? '✅' : '❌', 'Status:', response.status);
  console.log('Error:', data.error);
  console.log();
}

// Test 6: Missing trace_id
async function test6_missingTraceId() {
  console.log('=== Test 6: Missing trace_id ===');
  
  const response = await fetch(`${BASE_URL}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      execution_id: 'exec_no_trace',
      executionSchema: { game_mode: 'survival' },
      signature: 'dummy',
      nonce: crypto.randomBytes(16).toString('hex'),
      timestamp: Date.now()
    })
  });
  
  const data = await response.json();
  console.log(response.status === 401 ? '✅' : '❌', 'Status:', response.status);
  console.log('Error:', data.error);
  console.log();
}

// Test 7: Invalid execution schema
async function test7_invalidSchema() {
  console.log('=== Test 7: Invalid Execution Schema ===');
  
  const execution_id = `exec_bad_schema_${Date.now()}`;
  const trace_id = `trace_bad_schema_${Date.now()}`;
  const timestamp = Date.now();
  const nonce = crypto.randomBytes(16).toString('hex');
  const executionSchema = { invalid: 'schema' }; // Missing game_mode
  
  const signature = generateSignature(execution_id, trace_id, executionSchema, timestamp, nonce);
  
  const response = await fetch(`${BASE_URL}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      execution_id,
      trace_id,
      executionSchema,
      signature,
      nonce,
      timestamp
    })
  });
  
  const data = await response.json();
  console.log(response.status === 401 ? '✅' : '❌', 'Status:', response.status);
  console.log('Error:', data.error);
  console.log();
}

// Run all tests
(async () => {
  try {
    const { execution_id, nonce } = await test1_validRequest();
    await test2_missingSignature();
    await test3_invalidSignature();
    await test4_replayAttack(execution_id, nonce);
    await test5_expiredTimestamp();
    await test6_missingTraceId();
    await test7_invalidSchema();
    
    console.log('✅ All security enforcement tests completed');
  } catch (error) {
    console.error('❌ Test error:', error.message);
  }
})();
