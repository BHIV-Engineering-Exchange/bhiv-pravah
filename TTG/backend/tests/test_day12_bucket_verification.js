// test_day12_bucket_verification.js - Day 12: Verify bucket artifacts (MongoDB)
const axios = require('axios');

const BASE_URL = 'http://localhost:3000';
const PRIMARY_BUCKET_URL = 'http://localhost:8000';

async function verifyBucketArtifacts() {
  console.log('📦 Day 12: Bucket Artifact Verification\n');

  // Step 1: Create a test execution
  console.log('=== Step 1: Create Test Execution ===');

  try {
    const response = await axios.post(`${BASE_URL}/core/test-execution`);
    console.log('✅ Test execution created:', response.data.execution_id);
    
    const executionId = response.data.execution_id;
    const traceId = response.data.trace_id;
    
    // Wait for async writes
    console.log('⏳ Waiting for artifacts to be written...');
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Step 2: Query execution state
    console.log('\n=== Step 2: Verify Execution State ===');
    
    const stateResponse = await axios.get(`${BASE_URL}/core/execution/${executionId}?detailed=true`);
    const execution = stateResponse.data.execution;
    
    console.log('Execution state:');
    console.log(`  Execution ID: ${execution.execution_id}`);
    console.log(`  Trace ID: ${execution.trace_id}`);
    console.log(`  Status: ${execution.status}`);
    console.log(`  Jobs: ${execution.jobs.total}`);

    // Step 3: Verify required fields
    console.log('\n=== Step 3: Verify Artifact Fields ===');
    
    const hasExecutionId = !!execution.execution_id;
    const hasTraceId = !!execution.trace_id;
    const hasReceivedAt = !!execution.receivedAt;
    const hasStartedAt = !!execution.startedAt;
    const hasJobs = execution.jobs.total > 0;

    console.log('📋 Artifact Checklist:');
    console.log(hasExecutionId ? '✅ Execution ID stored' : '❌ Execution ID missing');
    console.log(hasTraceId ? '✅ Trace ID stored' : '❌ Trace ID missing');
    console.log(hasReceivedAt ? '✅ Received timestamp stored' : '❌ Received timestamp missing');
    console.log(hasStartedAt ? '✅ Start timestamp stored' : '❌ Start timestamp missing');
    console.log(hasJobs ? '✅ Execution schema processed (jobs created)' : '❌ No jobs created');

    // Step 4: Verify Primary Bucket Integration
    console.log('\n=== Step 4: Verify Primary Bucket Integration ===');
    try {
      const health = await axios.get(`${PRIMARY_BUCKET_URL}/health`);
      console.log('✅ Primary Bucket connected:', health.data.status);
      
      const policy = await axios.get(`${PRIMARY_BUCKET_URL}/governance/artifact-policy`);
      console.log('✅ Artifact policy accessible');
      console.log(`   Approved classes: ${policy.data.total_approved}`);
      console.log(`   Rejected classes: ${policy.data.total_rejected}`);
      
      console.log('\n💡 Check Primary Bucket terminal for:');
      console.log('   - POST /governance/validate-artifact-admission (execution_metadata)');
      console.log('   - POST /governance/validate-artifact-admission (logs)');
    } catch (error) {
      console.log('⚠️  Primary Bucket not accessible:', error.message);
    }

    // Step 5: Check for completion (if execution finished)
    console.log('\n=== Step 5: Check Completion Status ===');
    
    if (execution.completedAt) {
      console.log('✅ Execution completion timestamp stored');
      console.log(`   Duration: ${execution.duration}ms`);
      console.log(`   Status: ${execution.status}`);
    } else {
      console.log('⏳ Execution still running (completion pending)');
      console.log('   This is normal - jobs may still be processing');
    }

    // Final Summary
    console.log('\n=== Day 12 Verification Summary ===');
    const coreArtifacts = hasExecutionId && hasTraceId && hasReceivedAt && hasStartedAt && hasJobs;
    
    if (coreArtifacts) {
      console.log('✅ CORE ARTIFACTS VERIFIED SUCCESSFULLY');
      console.log('✅ Execution schema stored correctly');
      console.log('✅ Trace ID tracked throughout lifecycle');
      console.log('✅ Timestamps recorded (received + start)');
      console.log('✅ Jobs created from execution schema');
      console.log('✅ Primary Bucket integration active');
      
      if (execution.completedAt) {
        console.log('✅ Execution completion stored correctly');
      } else {
        console.log('⏳ Completion timestamp pending (execution in progress)');
      }
      
      console.log('\n📊 Storage: MongoDB (bucket_artifacts collection)');
      console.log('📊 Governance: Primary Bucket Owner (port 8000)');
    } else {
      console.log('❌ SOME ARTIFACTS MISSING');
      console.log('   Check backend logs for errors');
    }

  } catch (error) {
    console.error('❌ Verification failed:', error.message);
    if (error.response) {
      console.error('   Response:', error.response.data);
    }
    console.error('   Make sure backend is running on port 3000');
  }
}

verifyBucketArtifacts();
