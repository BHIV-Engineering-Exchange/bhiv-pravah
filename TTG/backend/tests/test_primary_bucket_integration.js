// test_primary_bucket_integration.js - Test Primary Bucket Owner integration
const axios = require('axios');
const { sendExecutionSchema, sendExecutionStart, sendExecutionCompletion } = require('../primaryBucketAdapter');

const PRIMARY_BUCKET_URL = process.env.PRIMARY_BUCKET_URL || 'http://localhost:8000';

async function testPrimaryBucketIntegration() {
  console.log('🧪 Testing Primary Bucket Owner Integration\n');

  // Test 1: Check Primary Bucket health
  console.log('=== Test 1: Primary Bucket Health Check ===');
  try {
    const health = await axios.get(`${PRIMARY_BUCKET_URL}/health`);
    console.log('✅ Primary Bucket is healthy:', health.data.status);
    console.log('   Bucket Version:', health.data.bucket_version);
  } catch (error) {
    console.error('❌ Primary Bucket not reachable:', error.message);
    console.log('   Make sure Primary Bucket is running on port 8000');
    return;
  }

  // Test 2: Send execution schema
  console.log('\n=== Test 2: Send Execution Schema ===');
  const execution_id = `exec_test_${Date.now()}`;
  const trace_id = `trace_test_${Date.now()}`;
  
  const schemaResult = await sendExecutionSchema(
    execution_id,
    trace_id,
    {
      game_mode: 'runner',
      movement: { speed: 5 },
      physics: { gravity: -9.8 }
    },
    Date.now()
  );

  if (schemaResult.success) {
    console.log('✅ Execution schema sent successfully');
  } else {
    console.log('❌ Execution schema failed:', schemaResult.error);
  }

  // Test 3: Send execution start
  console.log('\n=== Test 3: Send Execution Start ===');
  const startResult = await sendExecutionStart(execution_id, trace_id, Date.now());
  
  if (startResult.success) {
    console.log('✅ Execution start sent successfully');
  } else {
    console.log('❌ Execution start failed:', startResult.error);
  }

  // Test 4: Send execution completion
  console.log('\n=== Test 4: Send Execution Completion ===');
  const completionResult = await sendExecutionCompletion(
    execution_id,
    trace_id,
    Date.now(),
    'completed',
    1500
  );
  
  if (completionResult.success) {
    console.log('✅ Execution completion sent successfully');
  } else {
    console.log('❌ Execution completion failed:', completionResult.error);
  }

  // Test 5: Verify artifact admission policy
  console.log('\n=== Test 5: Verify Artifact Admission Policy ===');
  try {
    const policy = await axios.get(`${PRIMARY_BUCKET_URL}/governance/artifact-policy`);
    console.log('✅ Artifact policy retrieved');
    console.log('   Approved classes:', policy.data.total_approved);
    console.log('   Rejected classes:', policy.data.total_rejected);
  } catch (error) {
    console.log('❌ Failed to get artifact policy:', error.message);
  }

  console.log('\n✅ Integration test completed');
}

// Run test
testPrimaryBucketIntegration().catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});
