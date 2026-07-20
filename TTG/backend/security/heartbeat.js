// heartbeat.js

// Internal heartbeat tracking
const heartbeatMap = {}; // userId -> { last: timestamp, socketId }

// 1. Register/update heartbeat (called on "heartbeat" and on connect)
function updateHeartbeat(userId, socketId, timestamp = Date.now()) {
  heartbeatMap[userId] = { last: timestamp, socketId };
}

// 2. Remove heartbeat tracking (called on disconnect)
function removeHeartbeat(userId) {
  delete heartbeatMap[userId];
}

// 3. Attach event handlers to the socket
function attachHeartbeatHandlers(socket) {
  updateHeartbeat(socket.userId, socket.id, Date.now());

  socket.on("heartbeat", (data) => {
    updateHeartbeat(socket.userId, socket.id, data?.ts || Date.now());
    socket.emit("heartbeat_result", { 
      userId: socket.userId, 
      ok: true, 
      ts: Date.now() 
    });
  });

  socket.on("disconnect", () => {
    removeHeartbeat(socket.userId);
  });
}

// 4. Heartbeat monitor—call on app startup
function startHeartbeatMonitor({ markInactive, presenceMap }, intervalMs = 10000, maxMissMs = 45000) {
  setInterval(() => {
    const now = Date.now();
    for (const [userId, { last }] of Object.entries(heartbeatMap)) {
      if (now - last > maxMissMs) {
        markInactive(userId);
      }
    }
  }, intervalMs);
}

module.exports = {
  attachHeartbeatHandlers,
  startHeartbeatMonitor,
};
