class HintAgent {
  constructor() {
    this.name = "HintAgent";
  }

  evaluate(action, state) {
    // Only react to clicks
    if (action.type !== "click") return null;

    // If the user is rapidly clicking, return a hint
    if (state.spamCount >= 3) {
      return {
        agent: this.name,
        reason: "rapid_clicks",
        message: "Hint: Slow down and check the details."
      };
    }

    // Normal single click
    return {
      agent: this.name,
      reason: "single_click",
      message: "Hint: You can explore more options!"
    };
  }
}

module.exports = new HintAgent();
