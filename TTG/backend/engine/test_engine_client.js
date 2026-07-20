const { io } = require("socket.io-client");
const crypto = require("crypto");
const jwt = require("jsonwebtoken");

const ENGINE_ID = "engine_local_01";

const ENGINE_JWT = jwt.sign(
  {
    engineId: ENGINE_ID,
    role: "engine"
  },
  process.env.JWT_SECRET || "JWT_SECRET_123456789",
  { expiresIn: "1h" }
);

const socket = io("http://localhost:3000/engine", {
  auth: {
    token: ENGINE_JWT
  }
});

socket.on("connect", () => {
  console.log("[FAKE ENGINE] connected:", socket.id);

  // give backend time to finish auth + nonce setup
  setTimeout(() => {
    socket.emit("engine_ready");
  }, 1000);

  setInterval(() => {
    socket.emit("engine_heartbeat");
  }, 3000);
});

socket.on("engine_job", (job) => {
  console.log("[FAKE ENGINE] received job:", job.jobType, job.jobId);

  const payload = {
    jobId: job.jobId,
    jobType: job.jobType,
    status: "FINISHED"
  };

  const nonce = crypto.randomUUID();

  const sig = crypto
  .createHmac(
    "sha256",
    process.env.ENGINE_SHARED_SECRET || "engine_hmac_secret_here"
  )
  .update(JSON.stringify(payload) + nonce)
  .digest("hex");

  setTimeout(() => {
    socket.emit("engine_status", {
      payload,
      nonce,
      sig
    });
  }, 500);
});


socket.on("disconnect", () => {
  console.log("[FAKE ENGINE] disconnected");
});
