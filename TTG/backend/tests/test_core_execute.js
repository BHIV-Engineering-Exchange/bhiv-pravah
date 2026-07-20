// test_core_execute.js - Test POST /core/execute endpoint
const axios = require('axios');

const BASE_URL = 'http://localhost:3000';

// Test 1: Valid execution schema
async function testValidSchema() {
  console.log('\n=== Test 1: Valid Execution Schema ===');
  
  try {
    const response = await axios.post(`${BASE_URL}/core/execute`, {
      trace_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
      execution_id: 'exec_test_001',
      timestamp: Date.now(),
      user_id: 'test_user',
      intent: {
        genre: 'runner',
        pacing: 'fast',
        difficulty: 'medium'
      },
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
    
    console.log('✅ Success:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Error:', error.response?.data || error.message);
  }
}

// Test 2: Reject raw prompt
async function testRawPrompt() {
  console.log('\n=== Test 2: Reject Raw Prompt ===');
  
  try {
    const response = await axios.post(`${BASE_URL}/core/execute`, {
      trace_id: 'trace_002',
      execution_id: 'exec_test_002',
      executionSchema: 'Create a fast runner game with obstacles'  // String = raw prompt
    });
    
    console.log('❌ Should have been rejected:', response.data);
  } catch (error) {
    console.log('✅ Correctly rejected:', error.response?.data);
  }
}

// Test 3: Missing required fields
async function testMissingFields() {
  console.log('\n=== Test 3: Missing Required Fields ===');
  
  try {
    const response = await axios.post(`${BASE_URL}/core/execute`, {
      execution_id: 'exec_test_003'
      // Missing trace_id and executionSchema
    });
    
    console.log('❌ Should have been rejected:', response.data);
  } catch (error) {
    console.log('✅ Correctly rejected:', error.response?.data);
  }
}

// Test 4: Invalid schema structure
async function testInvalidSchema() {
  console.log('\n=== Test 4: Invalid Schema Structure ===');
  
  try {
    const response = await axios.post(`${BASE_URL}/core/execute`, {
      trace_id: 'trace_004',
      execution_id: 'exec_test_004',
      executionSchema: {
        // Missing game_mode
        movement: { speed: 8 }
      }
    });
    
    console.log('❌ Should have been rejected:', response.data);
  } catch (error) {
    console.log('✅ Correctly rejected:', error.response?.data);
  }
}

// Test 5: Query execution status
async function testQueryExecution(execution_id) {
  console.log('\n=== Test 5: Query Execution Status ===');
  
  try {
    const response = await axios.get(`${BASE_URL}/core/execution/${execution_id}`);
    console.log('✅ Execution found:', response.data);
  } catch (error) {
    console.error('❌ Error:', error.response?.data || error.message);
  }
}

// Run all tests
async function runTests() {
  console.log('🚀 Testing POST /core/execute endpoint\n');
  
  const result = await testValidSchema();
  await testRawPrompt();
  await testMissingFields();
  await testInvalidSchema();
  
  if (result?.execution_id) {
    await testQueryExecution(result.execution_id);
  }
  
  console.log('\n✅ All tests completed');
}

runTests();
