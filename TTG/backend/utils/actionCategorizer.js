function categorizeAction(type) {
    if (type.startsWith("agent_")) return "agent";
    if (["click", "scroll", "input"].includes(type)) return "ui";
    if (type.startsWith("nav_")) return "nav";
    if (type.includes("security")) return "security";
    return "system";
  }
  
  module.exports = { categorizeAction };
  