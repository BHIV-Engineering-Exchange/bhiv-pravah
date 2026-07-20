// nonceStore.js — Anti-Replay Nonce Store
// Stores used nonces per user for a short TTL.

const NONCE_TTL_MS = 5 * 60 * 1000; // 5 minutes
const userNonces = new Map(); // Map<userId, Map<nonce, expireAt>>

function checkAndConsumeNonce(userId, nonce) {
  const now = Date.now();

  if (!userNonces.has(userId)) {
    userNonces.set(userId, new Map());
  }

  const nonceMap = userNonces.get(userId);

  // Cleanup expired nonces
  for (const [n, exp] of nonceMap.entries()) {
    if (exp < now) nonceMap.delete(n);
  }

  // If nonce exists → replay detected
  if (nonceMap.has(nonce)) {
    return false;
  }

  // Store this nonce with expiry
  nonceMap.set(nonce, now + NONCE_TTL_MS);
  return true;
}

module.exports = { checkAndConsumeNonce };
