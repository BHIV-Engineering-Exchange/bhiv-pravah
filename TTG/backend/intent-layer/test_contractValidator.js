const { contractValidator } = require("./validators/contractValidator");
const { compile } = require("./compiler/intentCompiler");

console.log("=== Contract Validator Tests ===\n");

// Test 1: Valid compiled contract
console.log("Test 1: Valid compiled contract");
const compiled = compile("fast runner with jump and obstacles");
const result1 = contractValidator(compiled);
console.log("Valid:", result1.valid);
console.log("Errors:", result1.errors);
console.log();

// Test 2: Unknown fields stripped
console.log("Test 2: Unknown fields stripped");
const withMalicious = {
  ...compiled,
  malicious_code: "alert('xss')",
  admin: true,
  __proto__: { polluted: true }
};
const result2 = contractValidator(withMalicious);
console.log("Valid:", result2.valid);
console.log("Violations:", result2.violations);
console.log("Sanitized keys:", Object.keys(result2.sanitized || {}));
console.log();

// Test 3: Invalid game_mode
console.log("Test 3: Invalid game_mode");
const invalid = { ...compiled, game_mode: "invalid_mode" };
const result3 = contractValidator(invalid);
console.log("Valid:", result3.valid);
console.log("Errors:", result3.errors);
console.log();

// Test 4: Speed out of range
console.log("Test 4: Speed out of range");
const outOfRange = { ...compiled, movement: { speed: 999 } };
const result4 = contractValidator(outOfRange);
console.log("Valid:", result4.valid);
console.log("Errors:", result4.errors);
console.log();

// Test 5: Null input
console.log("Test 5: Null input");
const result5 = contractValidator(null);
console.log("Valid:", result5.valid);
console.log("Errors:", result5.errors);
