class NavAgent {
  constructor() {
    this.name = "NavAgent";
  }

  evaluate(action, state) {
    // CASE 1: Server detected true idle
    if (state.isIdle === true) {
      return {
        agent: this.name,
        reason: "user_idle",
        message: "Navigation Tip: You've been inactive. Explore the next section."
      };
    }

    // CASE 2: User navigates manually
    if (action.type === "navigate") {
      return {
        agent: this.name,
        reason: "user_navigation",
        message: "Navigation Tip: Check nearby options for quicker access."
      };
    }

    return null;
  }
}

module.exports = new NavAgent();
