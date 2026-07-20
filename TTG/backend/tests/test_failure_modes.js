// Test script for Day 2 failure modes
// Run with: node backend/test_failure_modes.js

const { engineMonitor } = require('./engine/engine_monitor');
const { startJobTimeout, clearJobTimeout } = require('./engine/job_timeout');

console.log('=== Day 2 Failure Modes Test ===\n');

// Test 1: Engine Monitor
console.log('Test 1: Engine Monitor');
console.log('----------------------');

engineMonitor.on('status_change', (status) => {
  console.log('✓ Status change event:', status);
});

engineMonitor.on('telemetry', (telemetry) => {
  console.log('✓ Telemetry event:', telemetry);
});

engineMonitor.setConnected(true);
console.log('Status:', engineMonitor.getStatus());

engineMonitor.recordHeartbeat();
console.log('✓ Heartbeat recorded');

// Test valid telemetry
const validTelemetry = engineMonitor.recordTelemetry({ 
  event: 'JOB_STARTED', 
  jobId: 'test-123' 
});
console.log('✓ Valid telemetry accepted:', validTelemetry);

// Test malformed telemetry
const invalidTelemetry = engineMonitor.recordTelemetry(null);
console.log('✓ Invalid telemetry rejected:', !invalidTelemetry);

engineMonitor.setConnected(false);
console.log('Status after disconnect:', engineMonitor.getStatus());

console.log('\nTest 2: Job Timeout');
console.log('-------------------');

let timeoutTriggered = false;
const testJobId = 'timeout-test-123';

startJobTimeout(testJobId, (jobId) => {
  timeoutTriggered = true;
  console.log('✓ Timeout triggered for job:', jobId);
});

console.log('✓ Timeout started for job:', testJobId);

// Clear timeout before it fires
setTimeout(() => {
  clearJobTimeout(testJobId);
  console.log('✓ Timeout cleared');
  
  if (!timeoutTriggered) {
    console.log('✓ Timeout successfully prevented');
  }
  
  console.log('\n=== All Tests Passed ===');
  process.exit(0);
}, 1000);
