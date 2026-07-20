module.exports = {
  name: "RuleAgent",

  evaluate(action, state) {
    if (!action) return null;

    const recent = state.actions.slice(-10); // Last 10 user actions
    const interactionCount = recent.filter(a => a.type !== "idle").length;
    const idleCount = recent.filter(a => a.type === "idle").length;

    // --- RULE 1: Frequent interactions → Offer help ---
    if (interactionCount >= 5) {
      return {
        agent: "RuleAgent",
        reason: "high_interaction_frequency",
        message: "You're interacting often — need help navigating?",
      };
    }

    // --- RULE 2: Idle trend → Encourage exploration ---
    if (state.isIdle === true || idleCount >= 3) {
      return {
        agent: "RuleAgent",
        reason: "user_idle",
        message: "You've been idle — maybe try exploring something new.",
      };
    }

    return null;
  }
};
