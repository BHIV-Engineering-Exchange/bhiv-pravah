const users = require("./mockUsers");
const actions = require("./mockActions");
const jobs = require("./mockQueue");

console.log("=== HARNESS START ===");

users.forEach(u => console.log("[MOCK USER]", u));
actions.forEach(a => console.log("[MOCK ACTION]", a));
jobs.forEach(j => console.log("[MOCK JOB]", j));

// later: emit these into your real event handlers
