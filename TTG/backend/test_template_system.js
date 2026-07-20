const { buildExecutionSchema } = require('./core/executionSchemaBuilder');

console.log('=== TESTING GAME TEMPLATE SYSTEM ===\n');

// Test 1: Fast Runner
console.log('TEST 1: "Create a fast runner game with obstacles"');
const test1 = buildExecutionSchema("Create a fast runner game with obstacles");
console.log('Template Selected:', test1.template.template_id);
console.log('Parameters:', JSON.stringify(test1.config.parameters, null, 2));
console.log('Execution Schema:', JSON.stringify(test1.executionSchema, null, 2));
console.log('\n---\n');

// Test 2: Easy Platformer
console.log('TEST 2: "Make an easy platform jumping game"');
const test2 = buildExecutionSchema("Make an easy platform jumping game");
console.log('Template Selected:', test2.template.template_id);
console.log('Parameters:', JSON.stringify(test2.config.parameters, null, 2));
console.log('Execution Schema:', JSON.stringify(test2.executionSchema, null, 2));
console.log('\n---\n');

// Test 3: Arena Survival
console.log('TEST 3: "Generate an arena survival game"');
const test3 = buildExecutionSchema("Generate an arena survival game");
console.log('Template Selected:', test3.template.template_id);
console.log('Parameters:', JSON.stringify(test3.config.parameters, null, 2));
console.log('Execution Schema:', JSON.stringify(test3.executionSchema, null, 2));
console.log('\n---\n');

// Test 4: Hard Small Arena
console.log('TEST 4: "Create a hard small arena combat game"');
const test4 = buildExecutionSchema("Create a hard small arena combat game");
console.log('Template Selected:', test4.template.template_id);
console.log('Parameters:', JSON.stringify(test4.config.parameters, null, 2));
console.log('Execution Schema:', JSON.stringify(test4.executionSchema, null, 2));
console.log('\n---\n');

console.log('✅ All tests completed!');
