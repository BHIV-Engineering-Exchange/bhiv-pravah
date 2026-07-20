const Ajv = require("ajv");
const schema = require("../schema/game.schema.json");

const ajv = new Ajv({ allErrors: true, strict: false });
const validate = ajv.compile(schema);

const ALLOWED_FIELDS = new Set(["game_mode", "movement", "camera", "spawn_rules", "score_rules", "end_conditions", "player_params", "world_params", "physics"]);

function contractValidator(data) {
  if (!data || typeof data !== "object") return { valid: false, errors: ["Invalid input: must be object"], sanitized: null, safe: false };
  if (Array.isArray(data)) return { valid: false, errors: ["Invalid input: arrays not allowed"], sanitized: null, safe: false };
  const sanitized = {}; const violations = []; const securityIssues = [];
  for (const key of Object.keys(data)) {
    if (ALLOWED_FIELDS.has(key)) sanitized[key] = data[key];
    else { violations.push(`Unknown field removed: ${key}`); securityIssues.push(`Attempted to inject field: ${key}`); }
  }
  if (data.hasOwnProperty("__proto__") || data.hasOwnProperty("constructor") || data.hasOwnProperty("prototype")) return { valid: false, errors: ["Security violation: prototype pollution"], sanitized: null, safe: false };
  const valid = validate(sanitized);
  if (!valid) { const errors = validate.errors.map(e => `${e.instancePath} ${e.message}`); return { valid: false, errors, violations, sanitized: null, safe: false }; }
  if (sanitized.movement?.speed && (sanitized.movement.speed < 1 || sanitized.movement.speed > 15)) return { valid: false, errors: ["Speed out of safe range (1-15)"], sanitized: null, safe: false };
  if (sanitized.physics?.gravity && (sanitized.physics.gravity < -20 || sanitized.physics.gravity > 0)) return { valid: false, errors: ["Gravity out of safe range (-20 to 0)"], sanitized: null, safe: false };
  if (violations.length > 0) console.warn("[CONTRACT_VALIDATOR] Violations:", violations);
  if (securityIssues.length > 0) console.warn("[CONTRACT_VALIDATOR] Security issues:", securityIssues);
  return { valid: true, errors: [], violations, sanitized, safe: securityIssues.length === 0 };
}

module.exports = { contractValidator };