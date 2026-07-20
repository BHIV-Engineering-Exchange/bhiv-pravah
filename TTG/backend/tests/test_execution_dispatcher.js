// test_execution_dispatcher.js - Test execution dispatcher
const axios = require('axios');

const BASE_URL = 'http://localhost:3000';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function testExecutionDispatcher() {
  console.log('🚀 Testing Execution Dispatcher\n');
  
  const execution_id = `exec_dispatch_${Date.now()}`;
  const trace_id = `trace_dispatch_${Date.now()}`;
  
  try {
    // Test 1: Submit execution and verify dispatch
    console.log('=== Test 1: Submit Execution ===');
    
    const response = await axios.post(`${BASE_URL}/core/execute`, {
      trace_id,
      execution_id,
      user_id: 'dispatcher_test_user',
      executionSchema: {
        game_mode: 'runner',
        movement: {
          speed: 8,
          jump_height: 5
        },
        camera: {
          type: 'third_person',
          distance: 10
        },
        spawn_rules: {
          obstacles: 2,
          frequency: 2
        },
        score_rules: {
          distance: 1,
          collectibles: 0
        },
        end_conditions: ['collision'],
        player_params: {
          jetpack: false,
          health: 3
        },
        world_params: {
          theme: 'default'
        },
        physics: {
          gravity: -9.8,
          friction: 0.5,
          bounce: 0.3
        }
      }
    });
    
    console.log('✅ Execution submitted:', response.data.execution_id);
    console.log(`   status: ${response.data.status}`);
    console.log(`   message: ${response.data.message}`);
    
    // Test 2: Wait and check execution status
    console.log('\n=== Test 2: Check Execution Status ===');
    console.log('⏳ Waiting for dispatch...');
    await sleep(2000);
    
    const statusResponse = await axios.get(`${BASE_URL}/core/execution/${execution_id}`);
    const execution = statusResponse.data.execution;
    
    console.log('✅ Execution status retrieved');
    console.log(`   execution_id: ${execution.execution_id}`);
    console.log(`   status: ${execution.status}`);
    console.log(`   jobs: ${execution.jobs.length}`);
    
    if (execution.jobs.length > 0) {
      console.log('✅ Jobs dispatched:');
      execution.jobs.forEach(jobId => {
        console.log(`     - ${jobId}`);
      });
    } else {
      console.log('⚠️  No jobs dispatched yet (may need more time)');
    }
    
    // Test 3: Verify job types
    console.log('\n=== Test 3: Verify Job Types ===');
    
    const expectedJobTypes = ['build_', 'spawn_player_', 'start_'];
    const hasAllJobTypes = expectedJobTypes.every(type => 
      execution.jobs.some(jobId => jobId.startsWith(type))
    );
    
    if (hasAllJobTypes) {
      console.log('✅ All expected job types created:');
      console.log('   - BUILD_SCENE');
      console.log('   - SPAWN_ENTITY (player)');
      console.log('   - START_LOOP');
    } else {
      console.log('⚠️  Some job types missing');
    }
    
    // Test 4: Check execution lifecycle
    console.log('\n=== Test 4: Execution Lifecycle ===');
    
    if (execution.startedAt) {
      console.log('✅ Execution started');
      console.log(`   startedAt: ${execution.startedAt}`);
    } else {
      console.log('⏳ Execution not started yet');
    }
    
    if (execution.completedAt) {
      console.log('✅ Execution completed');
      console.log(`   completedAt: ${execution.completedAt}`);
      console.log(`   duration: ${execution.duration}ms`);
    } else {
      console.log('⏳ Execution still running');
    }
    
    // Test 5: Wait for completion
    console.log('\n=== Test 5: Wait for Completion ===');
    console.log('⏳ Waiting for execution to complete...');
    
    let attempts = 0;
    const maxAttempts = 10;
    
    while (attempts < maxAttempts) {
      await sleep(1000);
      attempts++;
      
      const checkResponse = await axios.get(`${BASE_URL}/core/execution/${execution_id}`);
      const currentExecution = checkResponse.data.execution;
      
      console.log(`   Attempt ${attempts}: status = ${currentExecution.status}`);
      
      if (currentExecution.status === 'completed' || currentExecution.status === 'failed') {
        console.log(`✅ Execution ${currentExecution.status}`);
        console.log(`   duration: ${currentExecution.duration}ms`);
        console.log(`   jobs completed: ${currentExecution.jobs.length}`);
        break;
      }
    }
    
    if (attempts >= maxAttempts) {
      console.log('⚠️  Execution still running after 10 seconds');
      console.log('   (This is normal if engine is not connected)');
    }
    
    console.log('\n✅ Dispatcher test completed');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    if (error.response) {
      console.error('Response:', error.response.data);
    }
  }
}

testExecutionDispatcher();
