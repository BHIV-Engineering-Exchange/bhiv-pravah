const Ajv = require("ajv");
const schema = require("./engine_contract_schema.json");

const ajv = new Ajv({ allErrors: true, strict: false });
const validate = ajv.compile(schema);

function validateGameplayContract(data) {
  const valid = validate(data);
  if (!valid) {
    throw new Error(
      "Gameplay contract validation failed: " +
      JSON.stringify(validate.errors, null, 2)
    );
  }
  return true;
}

module.exports = validateGameplayContract;
