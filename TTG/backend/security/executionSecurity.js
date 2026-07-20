// executionSecurity.js - Security enforcement for core execution endpoint
const crypto = require('crypto');
const { HMAC_SECRET } = require('../config');
const { checkAndConsumeNonce } = require('./nonceStore');

const TIMESTAMP_WINDOW_MS = 30000; // ±30 seconds

function validateExecutionRequest(req) {
  const { trace_id, execution_id, executionSchema, signature, nonce, timestamp } = req.body;

  // 1. Validate required fields
  if (!trace_id || !execution_id || !executionSchema) {
    return { valid: false, error: 'Missing required fields: trace_id, execution_id, executionSchema' };
  }

  // 2. Validate execution schema structure
  if (typeof executionSchema !== 'object' || !executionSchema.game_mode) {
    return { valid: false, error: 'Invalid execution schema: must be object with game_mode' };
  }

  // 3. Validate trace_id format (must be non-empty string)
  if (typeof trace_id !== 'string' || trace_id.trim().length === 0) {
    return { valid: false, error: 'Invalid trace_id: must be non-empty string' };
  }

  // 4. Require signature and nonce
  if (!signature || !nonce || !timestamp) {
    return { valid: false, error: 'Missing security fields: signature, nonce, timestamp required' };
  }

  // 5. Validate timestamp (prevent replay attacks)
  const now = Date.now();
  const requestTime = parseInt(timestamp);
  if (isNaN(requestTime) || Math.abs(now - requestTime) > TIMESTAMP_WINDOW_MS) {
    return { valid: false, error: 'Invalid or expired timestamp' };
  }

  // 6. Verify signature
  const message = `${execution_id}|${trace_id}|${JSON.stringify(executionSchema)}|${timestamp}|${nonce}`;
  const expectedSig = crypto.createHmac('sha256', HMAC_SECRET).update(message).digest('hex');
  
  if (!timingSafeEqual(expectedSig, signature)) {
    return { valid: false, error: 'Invalid signature' };
  }

  // 7. Check and consume nonce (prevent replay)
  const userId = req.body.user_id || 'anonymous';
  if (!checkAndConsumeNonce(userId, nonce)) {
    return { valid: false, error: 'Nonce already used (replay attack detected)' };
  }

  return { valid: true };
}

function timingSafeEqual(a, b) {
  try {
    const bufA = Buffer.from(a, 'hex');
    const bufB = Buffer.from(b, 'hex');
    if (bufA.length !== bufB.length) return false;
    return crypto.timingSafeEqual(bufA, bufB);
  } catch {
    return false;
  }
}

module.exports = { validateExecutionRequest };
