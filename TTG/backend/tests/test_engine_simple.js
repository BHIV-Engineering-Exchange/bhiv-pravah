const { io } = require("socket.io-client");
const jwt = require("jsonwebtoken");

const ENGINE_ID = "engine_local_01";

const ENGINE_JWT = jwt.sign(
  { engineId: ENGINE_ID, role: "engine" },
  process.env.JWT_SECRET || "JWT_SECRET_123456789",
  { expiresIn: "1h" }
);

const socket = io("http://localhost:3000/engine", {
  auth: { token: ENGINE_JWT }
});

socket.on("connect", () => {
  console.log("[ENGINE] Connected:", socket.id);
  setTimeout(() => {
    socket.emit("engine_ready");
    console.log("[ENGINE] Ready");
  }, 1000);
  setInterval(() => socket.emit("engine_heartbeat"), 3000);
});

socket.on("engine_job", (engineJob) => {
  const jobId = engineJob.job_id;
  const jobType = engineJob.job_type;
  
  console.log(`[ENGINE] Job: ${jobType} (${jobId})`);

  setTimeout(() => {
    socket.emit("job_started", { job_id: jobId, timestamp: Date.now() });
    console.log(`[ENGINE] Started: ${jobId}`);

    setTimeout(() => {
      socket.emit("job_progress", { job_id: jobId, progress: 50, timestamp: Date.now() });
    }, 1000);

    setTimeout(() => {
      socket.emit("job_completed", { job_id: jobId, result: { success: true }, timestamp: Date.now() });
      console.log(`[ENGINE] Completed: ${jobId}`);
    }, 2000);
  }, 500);
});

socket.on("ready_ack", () => console.log("[ENGINE] Ready ACK"));
socket.on("disconnect", () => console.log("[ENGINE] Disconnected"));

console.log("[ENGINE] Starting...");
