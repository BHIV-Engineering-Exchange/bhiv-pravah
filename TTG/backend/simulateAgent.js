const io = require("socket.io-client");
const crypto = require("crypto");
const { AGENTS } = require("./config");

// 🔥 Choose which agent you want to simulate
const AGENT_ID = "HintAgent";   
// (Change to NavAgent / PredictAgent / RuleAgent to simulate others)

// Load the secret for this agent
const SECRET = AGENTS[AGENT_ID];

if (!SECRET) {
  console.error("❌ ERROR: No secret found for agent:", AGENT_ID);
  process.exit(1);
}

// Connect to backend
const socket = io("http://localhost:3000", {
  auth: {}
});

console.log(`🚀 Connecting as simulated agent: ${AGENT_ID} ...`);

let latestNonce = null;

// Day-2: receive per-agent nonce from server
socket.on("agent_nonce", (nonceMap) => {
  if (!nonceMap || typeof nonceMap !== 'object') {
    console.error("❌ Invalid nonce map received");
    return;
  }

  if (!nonceMap[AGENT_ID]) {
    console.error(`❌ No nonce found for ${AGENT_ID}`);
    return;
  }

  latestNonce = nonceMap[AGENT_ID];
  console.log(`🔑 Received nonce for ${AGENT_ID}:`, latestNonce);

  // Start heartbeat loop when nonce is available
  startHeartbeatLoop();
});

// Helper function: sign the heartbeat body
function signHeartbeat(agentId, ts, body, nonce) {
  try {
    const message = `${agentId}|${ts}|${body}`; 
    return crypto.createHmac("sha256", SECRET).update(message).digest("hex");
  } catch (err) {
    console.error("❌ Signature generation failed:", err.message);
    throw err;
  }
}

// Send signed heartbeat every 5 seconds
function startHeartbeatLoop() {
  if (!latestNonce) return;

  setInterval(() => {
    const ts = Date.now();
    const body = JSON.stringify({
      uptimeMs: Math.floor(process.uptime() * 1000)
    });

    const sig = signHeartbeat(AGENT_ID, ts, body, latestNonce);

    const hb = {
      agentId: AGENT_ID,
      ts,
      nonce: latestNonce,
      body,
      sig,
      alg: "hmac256"
    };

    console.log("\n📡 Sending signed heartbeat:", hb);

    socket.emit("agent_heartbeat", hb);
  }, 5000);
}

// Server heartbeat response
socket.on("agent_heartbeat_result", (res) => {
  console.log("🖥️ Server response:", res);
});
