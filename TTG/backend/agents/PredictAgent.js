class PredictAgent {
  constructor() {
    this.name = "PredictAgent";
  }

  evaluate(action, state) {
    const now = Date.now();

    // Safety checks
    if (!state || !Array.isArray(state.actions)) {
      return null;
    }

    // Look at last 6 actions (sliding window)
    const recentActions = state.actions.slice(-6);

    // --- Pattern 1: Repetitive interaction pattern ---
    const sameTypeCount = recentActions.filter(
      a => a.type === action.type
    ).length;

    if (sameTypeCount >= 4) {
      return {
        agent: this.name,
        reason: "repetitive_action_pattern",
        message: "Prediction: User likely to continue the same interaction."
      };
    }

    // --- Pattern 2: Gradual slowdown (pre-idle prediction) ---
    if (
      recentActions.length >= 5 &&
      now - state.lastActionAt > 3000 &&
      !state.isIdle
    ) {
      return {
        agent: this.name,
        reason: "slowdown_detected",
        message: "Prediction: User likely to go idle soon."
      };
    }

    return null;
  }
}

module.exports = new PredictAgent();
