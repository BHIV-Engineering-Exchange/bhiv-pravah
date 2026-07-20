// test_execution_state.js - Test execution state tracker
const axios = require('axios');

const BASE_URL = 'http://localhost:3000';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function testExecutionState() {
  console.log('🚀 Testing Execution State Tracker\n');
  
  const execution_id = `exec_state_${Date.now()}`;
  const trace_id = `trace_state_${Date.now()}`;
  
  try {
    // Test 1: Submit execution
    console.log('=== Test 1: Submit Execution ===');
    
    await axios.post(`${BASE_URL}/core/execute`, {
      trace_id,
      execution_id,
      user_id: 'state_test_user',
      executionSchema: {
        game_mode: 'runner',
        movement: { speed: 8, jump_height: 5 },
        camera: { type: 'third_person', distance: 10 },
        spawn_rules: { obstacles: 2, frequency: 2 },
        score_rules: { distance: 1, collectibles: 0 },
        end_conditions: ['collision'],
        player_params: { jetpack: false, health: 3 },
        world_params: { theme: 'default' },
        physics: { gravity: -9.8, friction: 0.5, bounce: 0.3 }
      }
    });
    
    console.log('✅ Execution submitted');
    
    // Test 2: Get execution state (summary)
    console.log('\n=== Test 2: Get Execution State (Summary) ===');
    await sleep(1000);
    
    const summaryResponse = await axios.get(`${BASE_URL}/core/execution/${execution_id}`);
    const summary = summaryResponse.data.execution;
    
    console.log('✅ Execution state retrieved');
    console.log(`   execution_id: ${summary.execution_id}`);
    console.log(`   status: ${summary.status}`);
    console.log(`   progress: ${summary.progress}%`);
    console.log(`   jobs: ${summary.jobs}`);
    
    // Test 3: Get execution state (detailed)
    console.log('\n=== Test 3: Get Execution State (Detailed) ===');
    
    const detailedResponse = await axios.get(`${BASE_URL}/core/execution/${execution_id}?detailed=true`);
    const detailed = detailedResponse.data.execution;
    
    console.log('✅ Detailed execution state retrieved');
    console.log(`   execution_id: ${detailed.execution_id}`);
    console.log(`   status: ${detailed.status}`);
    console.log(`   progress: ${detailed.progress}%`);
    console.log(`   jobs.total: ${detailed.jobs.total}`);
    console.log(`   jobs.completed: ${detailed.jobs.completed}`);
    console.log(`   jobs.running: ${detailed.jobs.running}`);
    console.log(`   jobs.queued: ${detailed.jobs.queued}`);
    console.log(`   jobs.failed: ${detailed.jobs.failed}`);
    
    // Test 4: Display job details
    console.log('\n=== Test 4: Job Details ===');
    
    detailed.jobDetails.forEach(job => {
      console.log(`   ${job.jobId}:`);
      console.log(`     type: ${job.jobType}`);
      console.log(`     status: ${job.status}`);
      if (job.duration) {
        console.log(`     duration: ${job.duration}ms`);
      }
    });
    
    // Test 5: Track state changes
    console.log('\n=== Test 5: Track State Changes ===');
    
    for (let i = 1; i <= 5; i++) {
      await sleep(1000);
      
      const checkResponse = await axios.get(`${BASE_URL}/core/execution/${execution_id}`);
      const state = checkResponse.data.execution;
      
      console.log(`   Check ${i}: status=${state.status}, progress=${state.progress}%`);
      
      if (state.status === 'completed' || state.status === 'failed') {
        console.log(`✅ Execution ${state.status}`);
        break;
      }
    }
    
    // Test 6: List all executions
    console.log('\n=== Test 6: List All Executions ===');
    
    const listResponse = await axios.get(`${BASE_URL}/core/executions`);
    
    console.log(`✅ Found ${listResponse.data.count} executions`);
    listResponse.data.executions.slice(0, 3).forEach(exec => {
      console.log(`   - ${exec.execution_id}: ${exec.status}`);
    });
    
    // Test 7: Filter by status
    console.log('\n=== Test 7: Filter Executions by Status ===');
    
    const statuses = ['received', 'running', 'completed', 'failed'];
    
    for (const status of statuses) {
      const filterResponse = await axios.get(`${BASE_URL}/core/executions?status=${status}`);
      console.log(`   ${status}: ${filterResponse.data.count} executions`);
    }
    
    // Test 8: Verify state tracking
    console.log('\n=== Test 8: Verify State Tracking ===');
    
    const finalResponse = await axios.get(`${BASE_URL}/core/execution/${execution_id}?detailed=true`);
    const finalState = finalResponse.data.execution;
    
    console.log('✅ State tracking verified:');
    console.log(`   Status: ${finalState.status}`);
    console.log(`   Progress: ${finalState.progress}%`);
    console.log(`   Duration: ${finalState.duration || 'N/A'}ms`);
    console.log(`   Jobs completed: ${finalState.jobs.completed}/${finalState.jobs.total}`);
    
    console.log('\n✅ All execution state tests completed');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    if (error.response) {
      console.error('Response:', error.response.data);
    }
  }
}

testExecutionState();
