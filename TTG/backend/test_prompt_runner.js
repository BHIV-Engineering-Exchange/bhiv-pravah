// test_prompt_runner.js - Test Prompt Runner integration
const axios = require('axios');

const BACKEND_URL = 'http://localhost:3000';

async function testPromptRunnerHealth() {
  console.log('\n=== Test 1: Prompt Runner Health Check ===');
  try {
    const response = await axios.get(`${BACKEND_URL}/core/prompt-runner-health`);
    console.log('✅ Health check:', response.data);
    return response.data.healthy;
  } catch (error) {
    console.error('❌ Health check failed:', error.message);
    return false;
  }
}

async function testExecuteFromText() {
  console.log('\n=== Test 2: Execute from Natural Language ===');
  try {
    const response = await axios.post(`${BACKEND_URL}/core/execute-from-text`, {
      prompt: 'Create a fast-paced runner game with obstacles and collectibles',
      user_id: 'test_user'
    });
    console.log('✅ Execution created:', response.data);
    return response.data.execution_id;
  } catch (error) {
    console.error('❌ Execute from text failed:', error.response?.data || error.message);
    return null;
  }
}

async function testExecuteFromPrompt() {
  console.log('\n=== Test 3: Execute from Prompt Runner Output ===');
  try {
    const response = await axios.post(`${BACKEND_URL}/core/execute-from-prompt`, {
      module: 'creator',
      intent: 'generate_game',
      topic: 'endless runner game',
      tasks: ['setup_scene', 'spawn_player', 'generate_obstacles'],
      output_format: 'step_by_step_guide',
      user_id: 'test_user'
    });
    console.log('✅ Execution created:', response.data);
    return response.data.execution_id;
  } catch (error) {
    console.error('❌ Execute from prompt failed:', error.response?.data || error.message);
    return null;
  }
}

async function checkExecutionStatus(execution_id) {
  console.log(`\n=== Test 4: Check Execution Status (${execution_id}) ===`);
  try {
    const response = await axios.get(`${BACKEND_URL}/core/execution/${execution_id}`);
    console.log('✅ Execution status:', response.data.execution);
  } catch (error) {
    console.error('❌ Status check failed:', error.response?.data || error.message);
  }
}

async function runTests() {
  console.log('🚀 Starting Prompt Runner Integration Tests...\n');
  
  // Test 1: Health check
  const isHealthy = await testPromptRunnerHealth();
  if (!isHealthy) {
    console.log('\n⚠️  Prompt Runner service not available. Some tests will be skipped.');
  }
  
  // Test 2: Execute from text (requires Prompt Runner service)
  if (isHealthy) {
    const execution_id1 = await testExecuteFromText();
    if (execution_id1) {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await checkExecutionStatus(execution_id1);
    }
  }
  
  // Test 3: Execute from prompt output (doesn't require Prompt Runner)
  const execution_id2 = await testExecuteFromPrompt();
  if (execution_id2) {
    await new Promise(resolve => setTimeout(resolve, 2000));
    await checkExecutionStatus(execution_id2);
  }
  
  console.log('\n✅ All tests completed!\n');
}

runTests().catch(err => {
  console.error('Test suite failed:', err);
  process.exit(1);
});
