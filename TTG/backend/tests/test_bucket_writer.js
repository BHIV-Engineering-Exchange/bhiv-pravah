// test_bucket_writer.js - Test bucket artifact writing
const axios = require('axios');
const { readExecutionArtifacts, listExecutions } = require('../bucketWriter');

const BASE_URL = 'http://localhost:3000';

async function testBucketIntegration() {
  console.log('🚀 Testing Bucket Artifact Writer\n');
  
  // Test 1: Submit execution and verify bucket writes
  console.log('=== Test 1: Submit Execution ===');
  const execution_id = `exec_bucket_${Date.now()}`;
  
  try {
    const response = await axios.post(`${BASE_URL}/core/test-execution`);
    
    console.log('✅ Execution submitted:', response.data.execution_id);
    
    // Wait for async bucket writes
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Test 2: Verify artifacts written
    console.log('\n=== Test 2: Verify Bucket Artifacts ===');
    const artifacts = await readExecutionArtifacts(response.data.execution_id);
    
    if (artifacts.success) {
      console.log(`✅ Found ${artifacts.artifacts.length} artifacts:`);
      artifacts.artifacts.forEach(a => {
        console.log(`  - ${a.file} (${a.type})`);
      });
      
      const hasSchema = artifacts.artifacts.some(a => a.file.includes('_schema.json'));
      const hasLog = artifacts.artifacts.some(a => a.file.includes('_log.jsonl'));
      
      if (hasSchema) {
        console.log('✅ Execution schema artifact found');
      } else {
        console.log('❌ Execution schema artifact missing');
      }
      
      if (hasLog) {
        console.log('✅ Execution log artifact found');
      } else {
        console.log('❌ Execution log artifact missing');
      }
    } else {
      console.log('❌ Failed to read artifacts:', artifacts.error);
    }
    
    // Test 3: List all executions
    console.log('\n=== Test 3: List All Executions ===');
    const executions = await listExecutions();
    if (executions.success) {
      console.log(`✅ Found ${executions.executions.length} executions in bucket`);
      console.log('Recent executions:', executions.executions.slice(-5));
    } else {
      console.log('❌ Failed to list executions:', executions.error);
    }
    
    console.log('\n✅ All bucket tests completed');
    console.log('\n📊 Check Primary Bucket logs for integration messages');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

testBucketIntegration();
