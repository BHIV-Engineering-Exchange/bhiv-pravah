const crypto = require("crypto");
const { HMAC_SECRET } = require("../config");

// Timing-safe comparison
function safeHexEqual(a, b) {
  try {
    const A = Buffer.from(a, "hex");
    const B = Buffer.from(b, "hex");

    if (A.length !== B.length) return false;
    return crypto.timingSafeEqual(A, B);
  } catch {
    return false;
  }
}

function verifyActionSignature({ type, payload, ts, nonce, sig }) {
  if (!type || !ts || !nonce || !sig) return false;

  // EXACTLY match frontend message format
  const message = `${type}|${JSON.stringify(payload)}|${ts}|${nonce}`;

  const expected = crypto
    .createHmac("sha256", HMAC_SECRET)
    .update(message)
    .digest("hex");

  return safeHexEqual(expected, sig);
}

module.exports = { verifyActionSignature };
