const { verify } = require("./agent_signatures");
const { verifyAndConsume } = require("./nonce_registry");

const last = new Map(); // agentId -> last heartbeat info

function processHeartbeat(hb) {
  const { agentId, ts, nonce, body, sig, alg } = hb;

  // timestamp freshness
  if (Math.abs(Date.now() - ts) > 15000) {
    return { ok: false, reason: "timestamp_skew" };
  }

  // signature verification
  const valid = verify(agentId, { ts, body, sig, alg });
  if (!valid) return { ok: false, reason: "signature_failed" };

  // nonce replay check
  const ok = verifyAndConsume(agentId, nonce);
  if (!ok) return { ok: false, reason: "replay_detected" };

  last.set(agentId, { ts, uptime: JSON.parse(body).uptimeMs });
  return { ok: true };
}

module.exports = { processHeartbeat };
