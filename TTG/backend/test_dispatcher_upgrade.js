const { buildExecutionSchema } = require('./core/executionSchemaBuilder');
const { mapSchemaToJobs } = require('./executionDispatcher');
const { selectTemplate } = require('./game-templates/templateSelector');

console.log('=== TESTING DISPATCHER WITH TEMPLATES ===\n');

// Test 1: Runner
console.log('TEST 1: Runner Game');
const result1 = buildExecutionSchema("Create a fast runner game");
const template1 = selectTemplate("runner");
const jobs1 = mapSchemaToJobs(result1.executionSchema, 'exec_1', 'trace_1', 'user_1', template1.jobs);
console.log('Template Jobs:', template1.jobs);
console.log('Generated Jobs:', jobs1.map(j => `${j.jobType} (${j.jobId})`));
console.log('\n---\n');

// Test 2: Platformer
console.log('TEST 2: Platformer Game');
const result2 = buildExecutionSchema("Make a platform jumping game");
const template2 = selectTemplate("platformer");
const jobs2 = mapSchemaToJobs(result2.executionSchema, 'exec_2', 'trace_2', 'user_2', template2.jobs);
console.log('Template Jobs:', template2.jobs);
console.log('Generated Jobs:', jobs2.map(j => `${j.jobType} (${j.jobId})`));
console.log('\n---\n');

// Test 3: Arena
console.log('TEST 3: Arena Game');
const result3 = buildExecutionSchema("Create an arena survival game");
const template3 = selectTemplate("arena");
const jobs3 = mapSchemaToJobs(result3.executionSchema, 'exec_3', 'trace_3', 'user_3', template3.jobs);
console.log('Template Jobs:', template3.jobs);
console.log('Generated Jobs:', jobs3.map(j => `${j.jobType} (${j.jobId})`));
console.log('\n---\n');

console.log('✅ Dispatcher upgrade test completed!');
console.log(`\nRunner: ${jobs1.length} jobs`);
console.log(`Platformer: ${jobs2.length} jobs`);
console.log(`Arena: ${jobs3.length} jobs`);
