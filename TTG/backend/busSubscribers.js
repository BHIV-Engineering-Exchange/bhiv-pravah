// Bus_subscribers.js - Subscribes to the event bus and handles incoming events (e.g., actions from clients). It processes these events, updates the database, and emits updates to clients or agents as needed.
const eventBus = require("./eventBus");
const ActionEvent = require("./models/ActionEvent");
const { categorizeAction } = require("./utils/actionCategorizer");

let registered = false;

function registerBusSubscribers(io, orchestrator) {
  if (registered) return;
  registered = true;

  eventBus.on("action", async (action) => {
    const enriched = {
      ...action,
      category: categorizeAction(action.type),
      serverTs: action.serverTs || Date.now()
    };

    // Mongo persistence
    try {
      await ActionEvent.create({
        userId: enriched.userId,
        sessionId: enriched.sessionId,
        type: enriched.type,
        category: enriched.category,
        payload: enriched.payload,
        clientTs: enriched.clientTs,
        serverTs: enriched.serverTs,
        source: "client"
      });
    } catch (err) {
      console.error("[ActionBus] Mongo persist failed", err);
    }

    // UI update
    io.to(`user:${enriched.userId}`).emit("action_update", enriched);

    // Agent orchestration
    const result = orchestrator.evaluate(enriched);
    if (result) {
      io.to(`user:${enriched.userId}`).emit("agent_update", result);
    }
  });
}

module.exports = { registerBusSubscribers };
