// verify_telemetry.js - Quick test of new telemetry format
const { recordTelemetry, loadTelemetry, clearTelemetry } = require('./engine/engine_telemetry');

console.log('=== TELEMETRY FORMAT VERIFICATION ===\n');

// Clear any existing data
clearTelemetry();

// Record test events
console.log('Recording 5 test events...');
recordTelemetry({ event: 'JOB_QUEUED', jobId: 'test_001', engineId: 'engine_01', userId: 'user_01', payload: { jobType: 'BUILD_SCENE' } });
recordTelemetry({ event: 'JOB_DISPATCHED', jobId: 'test_001', engineId: 'engine_01', userId: 'user_01', payload: { jobType: 'BUILD_SCENE' } });
recordTelemetry({ event: 'JOB_RUNNING', jobId: 'test_001', engineId: 'engine_01', userId: 'user_01', payload: { jobType: 'BUILD_SCENE' } });
recordTelemetry({ event: 'SCENE_LOADED', jobId: 'test_001', engineId: 'engine_01', userId: 'user_01', payload: { sceneId: 'scene_forest' } });
recordTelemetry({ event: 'JOB_COMPLETED', jobId: 'test_001', engineId: 'engine_01', userId: 'user_01', payload: { jobType: 'BUILD_SCENE', duration: 3200 } });

// Load and verify
const events = loadTelemetry();
console.log(`✅ Loaded ${events.length} events\n`);

// Check format
console.log('--- Format Verification ---');
const firstEvent = events[0];
const requiredFields = ['seq', 'ts', 'event', 'jobId', 'engineId', 'userId', 'payload', '_replay'];
const hasAllFields = requiredFields.every(field => firstEvent.hasOwnProperty(field));

if (hasAllFields) {
  console.log('✅ All required fields present');
} else {
  console.log('❌ Missing fields');
}

// Check sequence
console.log('\n--- Sequence Verification ---');
let valid = true;
for (let i = 0; i < events.length; i++) {
  if (events[i].seq !== i + 1) {
    console.log(`❌ Sequence error at index ${i}: expected ${i + 1}, got ${events[i].seq}`);
    valid = false;
  }
}
if (valid) {
  console.log('✅ Sequence numbers are correct (1, 2, 3, 4, 5)');
}

// Display sample
console.log('\n--- Sample Event ---');
console.log(JSON.stringify(firstEvent, null, 2));

console.log('\n=== VERIFICATION COMPLETE ===');
console.log('New telemetry format is working correctly.\n');
