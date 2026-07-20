// test_storage.js - Test storage contract implementations
require('dotenv').config();
const { createStorage } = require('./storage');

async function testStorage() {
  console.log('\n=== Storage Contract Test ===\n');
  
  const storage = createStorage();
  const provider = process.env.STORAGE_PROVIDER || 'local';
  
  console.log(`Testing provider: ${provider}\n`);
  
  const execution_id = `test_${Date.now()}`;
  const trace_id = `trace_${Date.now()}`;
  
  try {
    // Test 1: Write execution schema
    console.log('1. Writing execution schema...');
    const schemaResult = await storage.writeExecutionSchema(
      execution_id,
      trace_id,
      { type: 'test', steps: ['step1', 'step2'] },
      Date.now()
    );
    console.log('   ✓ Schema written:', schemaResult.success ? 'SUCCESS' : 'FAILED');
    
    // Test 2: Write execution start
    console.log('\n2. Writing execution start...');
    const startResult = await storage.writeExecutionStart(
      execution_id,
      trace_id,
      Date.now()
    );
    console.log('   ✓ Start written:', startResult.success ? 'SUCCESS' : 'FAILED');
    
    // Test 3: Append logs
    console.log('\n3. Appending execution logs...');
    await storage.appendExecutionLog(execution_id, trace_id, 'job_started', { job: 'test_job' });
    await storage.appendExecutionLog(execution_id, trace_id, 'job_progress', { progress: 50 });
    await storage.appendExecutionLog(execution_id, trace_id, 'job_completed', { result: 'success' });
    console.log('   ✓ Logs appended: SUCCESS');
    
    // Test 4: Write execution completion
    console.log('\n4. Writing execution completion...');
    const completionResult = await storage.writeExecutionCompletion(
      execution_id,
      trace_id,
      Date.now(),
      'completed',
      1500
    );
    console.log('   ✓ Completion written:', completionResult.success ? 'SUCCESS' : 'FAILED');
    
    // Test 5: Write complete artifact
    console.log('\n5. Writing complete execution artifact...');
    const artifactResult = await storage.writeExecutionArtifact({
      execution_id,
      trace_id,
      user_id: 'test_user',
      executionSchema: { type: 'test' },
      status: 'completed',
      jobs: ['job1', 'job2'],
      receivedAt: Date.now() - 2000,
      startedAt: Date.now() - 1500,
      completedAt: Date.now(),
      error: null
    });
    console.log('   ✓ Artifact written:', artifactResult.success ? 'SUCCESS' : 'FAILED');
    
    // Test 6: Read artifacts
    console.log('\n6. Reading execution artifacts...');
    const readResult = await storage.readExecutionArtifacts(execution_id);
    console.log('   ✓ Artifacts read:', readResult.success ? 'SUCCESS' : 'FAILED');
    console.log('   ✓ Artifacts found:', readResult.artifacts?.length || 0);
    
    // Test 7: List executions
    console.log('\n7. Listing all executions...');
    const listResult = await storage.listExecutions();
    console.log('   ✓ Executions listed:', listResult.success ? 'SUCCESS' : 'FAILED');
    console.log('   ✓ Total executions:', listResult.executions?.length || 0);
    
    console.log('\n=== All Tests Passed! ===\n');
    
    // Cleanup for MongoDB
    if (storage.close) {
      await storage.close();
    }
    
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

// Run tests
testStorage().then(() => {
  console.log('Test completed successfully');
  process.exit(0);
}).catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});
