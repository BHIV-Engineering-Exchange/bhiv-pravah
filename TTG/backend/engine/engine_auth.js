const jwt = require("jsonwebtoken");
const crypto = require("crypto");

// In-memory nonce store with TTL
const usedNonces = new Map(); // nonce -> expiresAt
const NONCE_TTL = 5 * 60 * 1000; // 5 minutes

// Cleanup expired nonces periodically
setInterval(() => {
  const now = Date.now();
  for (const [nonce, expiresAt] of usedNonces.entries()) {
    if (expiresAt < now) {
      usedNonces.delete(nonce);
    }
  }
}, 60 * 1000); // Run every minute


//   1. Verify Engine JWT

function verifyEngineJWT(socket) {
  const token = socket.handshake.auth?.token;

  if (!token) {
    throw new Error("ENGINE_JWT_MISSING");
  }

  let payload;
  try {
    payload = jwt.verify(token, process.env.JWT_SECRET);
  } catch (err) {
    throw new Error("ENGINE_JWT_INVALID");
  }

  if (payload.role !== "engine") {
    throw new Error("ENGINE_ROLE_INVALID");
  }

  // Attach identity to socket
  socket.engineId = payload.engineId;
}


//   2. Verify Engine Packet Signature (HMAC)

function verifyEngineTimestamp(ts) {
  const now = Date.now();
  const drift = Math.abs(now - ts);
  const MAX_DRIFT = 30000; // 30 seconds
  
  if (drift > MAX_DRIFT) {
    throw new Error("ENGINE_TIMESTAMP_EXPIRED");
  }
}

function verifyEngineSignature({ payload, nonce, sig, ts }) {
  if (!payload || !nonce || !sig || !ts) {
    throw new Error("ENGINE_PACKET_INCOMPLETE");
  }

  verifyEngineTimestamp(ts);

  const expectedSig = crypto
    .createHmac("sha256", process.env.ENGINE_SHARED_SECRET)
    .update(JSON.stringify(payload) + nonce + ts)
    .digest("hex");

  if (expectedSig !== sig) {
    throw new Error("ENGINE_SIGNATURE_INVALID");
  }
}


//   3. Verify & consume nonce (replay protection)

function verifyAndConsumeNonce(nonce) {
  if (usedNonces.has(nonce)) {
    throw new Error("ENGINE_NONCE_REPLAY");
  }
  usedNonces.set(nonce, Date.now() + NONCE_TTL);
}

module.exports = {
  verifyEngineJWT,
  verifyEngineSignature,
  verifyAndConsumeNonce,
  verifyEngineTimestamp
};
