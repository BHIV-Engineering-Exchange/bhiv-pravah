const crypto = require("crypto");

const agentKeys = new Map(); 
// agentId -> { type: "rsa"|"hmac", publicKey?, privateKey?, secret? }

function registerRSA(agentId, publicKeyPem, privateKeyPem) {
  if (!agentId || typeof agentId !== 'string') {
    throw new Error("Invalid agentId");
  }
  if (!publicKeyPem || !privateKeyPem) {
    throw new Error("RSA keys required");
  }
  agentKeys.set(agentId, {
    type: "rsa",
    publicKey: publicKeyPem,
    privateKey: privateKeyPem
  });
}

function registerHMAC(agentId, secret) {
  if (!agentId || typeof agentId !== 'string') {
    throw new Error("Invalid agentId");
  }
  if (!secret || typeof secret !== 'string') {
    throw new Error("HMAC secret required");
  }
  agentKeys.set(agentId, {
    type: "hmac",
    secret
  });
}

function sign(agentId, payload) {
  const rec = agentKeys.get(agentId);
  if (!rec) throw new Error("unknown agent");

  try {
    const body = JSON.stringify(payload);
    const ts = Date.now();
    const message = `${agentId}|${ts}|${body}`;

    if (rec.type === "rsa") {
      const signer = crypto.createSign("RSA-SHA256");
      signer.update(message);
      const sig = signer.sign(rec.privateKey, "base64");
      return { ts, body, sig, alg: "rsa256" };
    }

    if (rec.type === "hmac") {
      const sig = crypto.createHmac("sha256", rec.secret)
        .update(message)
        .digest("hex");
      return { ts, body, sig, alg: "hmac256" };
    }

    throw new Error("Unknown signature type");
  } catch (err) {
    console.error("[SIGNATURE] Sign failed:", err.message);
    throw new Error("Signature generation failed");
  }
}

function verify(agentId, { ts, body, sig, alg }) {
  const rec = agentKeys.get(agentId);
  if (!rec) return false;

  try {
    const message = `${agentId}|${ts}|${body}`;

    if (alg === "rsa256" && rec.type === "rsa") {
      const v = crypto.createVerify("RSA-SHA256");
      v.update(message);
      return v.verify(rec.publicKey, sig, "base64");
    }

    if (alg === "hmac256" && rec.type === "hmac") {
      const expected = crypto.createHmac("sha256", rec.secret)
        .update(message)
        .digest("hex");

      return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(sig));
    }

    return false;
  } catch (err) {
    console.error("[SIGNATURE] Verify failed:", err.message);
    return false;
  }
}

module.exports = { registerRSA, registerHMAC, sign, verify };
