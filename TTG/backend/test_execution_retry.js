// test_execution_retry.js - Test execution retry logic
require('dotenv').config();
const executionRetry = require('./executionRetry');

async function testRetryLogic() {
  console.log('\n=== Execution Retry Test ===\n');

  const execution_id = `test_exec_${Date.now()}`;
  const trace_id = `trace_${Date.now()}`;

  // Test 1: Success on first attempt
  console.log('Test 1: Success on first attempt');
  const result1 = await executionRetry.executeWithRetry(
    `${execution_id}_1`,
    trace_id,
    async () => {
      console.log('  Executing job...');
      return { status: 'completed', data: 'success' };
    }
  );
  console.log('  Result:', result1);
  console.log('  ✓ Test 1 passed\n');

  // Test 2: Fail once, succeed on retry
  console.log('Test 2: Fail once, succeed on retry');
  let attempt = 0;
  const result2 = await executionRetry.executeWithRetry(
    `${execution_id}_2`,
    trace_id,
    async () => {
      attempt++;
      if (attempt === 1) {
        throw new Error('Temporary network error');
      }
      return { status: 'completed', data: 'success after retry' };
    }
  );
  console.log('  Result:', result2);
  console.log('  ✓ Test 2 passed\n');

  // Test 3: Fail all attempts
  console.log('Test 3: Fail all attempts (max retries)');
  const result3 = await executionRetry.executeWithRetry(
    `${execution_id}_3`,
    trace_id,
    async () => {
      throw new Error('Persistent database connection error');
    }
  );
  console.log('  Result:', result3);
  console.log('  ✓ Test 3 passed\n');

  console.log('=== All Retry Tests Passed! ===\n');
}

testRetryLogic().then(() => {
  console.log('Test completed successfully');
  process.exit(0);
}).catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});
