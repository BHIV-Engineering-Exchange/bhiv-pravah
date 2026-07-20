require("dotenv").config();

const requiredEnvVars = [
  'JWT_SECRET',
  'JWT_ISSUER',
  'JWT_EXP',
  'HMAC_SECRET',
  'HMAC_WINDOW_MS',
  'HINT_AGENT_SECRET',
  'NAV_AGENT_SECRET',
  'PREDICT_AGENT_SECRET',
  'RULE_AGENT_SECRET'
];

const missing = requiredEnvVars.filter(key => !process.env[key]);
if (missing.length > 0) {
  console.error(`[CONFIG] Missing required environment variables: ${missing.join(', ')}`);
  throw new Error(`Missing environment variables: ${missing.join(', ')}`);
}

module.exports = {
  JWT_SECRET: process.env.JWT_SECRET,
  JWT_ISSUER: process.env.JWT_ISSUER,
  JWT_EXP: process.env.JWT_EXP,

  HMAC_SECRET: process.env.HMAC_SECRET,
  HMAC_WINDOW_MS: Number(process.env.HMAC_WINDOW_MS),

  AGENTS: {
    HintAgent: process.env.HINT_AGENT_SECRET,
    NavAgent: process.env.NAV_AGENT_SECRET,
    PredictAgent: process.env.PREDICT_AGENT_SECRET,
    RuleAgent: process.env.RULE_AGENT_SECRET
  },

  MONG0_URI: process.env.MONGO_URI,
};
