const crypto = require("crypto");

const perAgent = new Map();
// agentId -> { currentNonce, seen: Map<nonce, expireAt> }

const TTL = 3 * 60 * 1000;

function rotateNonce(agentId) {
  const nonce = crypto.randomBytes(16).toString("hex");
  const now = Date.now();

  if (!perAgent.has(agentId)) {
    perAgent.set(agentId, { currentNonce: nonce, seen: new Map() });
  } else {
    perAgent.get(agentId).currentNonce = nonce;
  }

  // mark nonce as seen (so replay can't re-use)
  const record = perAgent.get(agentId);
  if (record) {
    record.seen.set(nonce, now + TTL);
  }

  return nonce;
}

function verifyAndConsume(agentId, nonce) {
  if (!nonce || typeof nonce !== 'string') {
    console.warn("[NONCE] Invalid nonce provided");
    return false;
  }

  const now = Date.now();
  if (!perAgent.has(agentId)) perAgent.set(agentId, { currentNonce: null, seen: new Map() });

  const record = perAgent.get(agentId);

  // cleanup
  for (const [n, exp] of record.seen.entries()) {
    if (exp < now) record.seen.delete(n);
  }

  if (record.seen.has(nonce)) return false;

  record.seen.set(nonce, now + TTL);
  return true;
}

module.exports = { rotateNonce, verifyAndConsume };
