const HintAgent = require("../agents/HintAgent");
const NavAgent = require("../agents/NavAgent");
const PredictAgent = require("../agents/PredictAgent");
const RuleAgent = require("../agents/Ruleagent");


const { userStates } = require("../state/userStates");

// Priority for conflict resolution
const PRIORITY = ["HintAgent", "NavAgent", "PredictAgent", "RuleAgent"];

const agents = [HintAgent, NavAgent, PredictAgent, RuleAgent];

class Orchestrator {
  evaluate(action) {
    const rawUserId = action.userId;
    const userId =
      typeof rawUserId === "object"
        ? rawUserId.userId
        : rawUserId;

    // Pull per-user state (created by index.js)
    const state = userStates[userId];
    if (!state) {
      console.warn(`[Orchestrator] No state found for user ${userId}`);
      return null;
    }

    const results = [];

    for (const agent of agents) {
      // Pass per-user state into all agents
      const output = agent.evaluate(action, state);

      if (output) {
        results.push({
          agent: output.agent,
          message: output.message,
          reason: output.reason || "",
          userId,
          timestamp: Date.now(),
        });
      }
    }

    // No agent reacted → return null
    if (results.length === 0) {
      return null;
    }

    // Apply priority order
    results.sort((a, b) => PRIORITY.indexOf(a.agent) - PRIORITY.indexOf(b.agent));
    const winner = results[0];

    return winner;
  }
}

module.exports = new Orchestrator();
