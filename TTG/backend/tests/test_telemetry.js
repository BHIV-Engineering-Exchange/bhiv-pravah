// test_telemetry.js - Test telemetry forwarding
const axios = require('axios');

const BASE_URL = 'http://localhost:3000';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function testTelemetry() {
  console.log('🚀 Testing Telemetry Forwarding\n');
  
  const execution_id = `exec_telemetry_${Date.now()}`;
  const trace_id = `trace_telemetry_${Date.now()}`;
  
  try {
    // Test 1: Submit execution
    console.log('=== Test 1: Submit Execution ===');
    
    await axios.post(`${BASE_URL}/core/execute`, {
      trace_id,
      execution_id,
      user_id: 'telemetry_test_user',
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
    
    // Test 2: Wait for telemetry
    console.log('\n=== Test 2: Wait for Telemetry Events ===');
    console.log('⏳ Waiting for jobs to start...');
    await sleep(2000);
    
    // Test 3: Get execution telemetry
    console.log('\n=== Test 3: Get Execution Telemetry ===');
    
    const telemetryResponse = await axios.get(`${BASE_URL}/core/telemetry/${execution_id}`);
    const telemetry = telemetryResponse.data;
    
    console.log(`✅ Telemetry retrieved: ${telemetry.count} events`);
    
    // Test 4: Display telemetry events
    console.log('\n=== Test 4: Telemetry Events ===');
    
    telemetry.telemetry.forEach((event, index) => {
      console.log(`\n   Event ${index + 1}:`);
      console.log(`     event: ${event.event}`);
      console.log(`     timestamp: ${new Date(event.timestamp).toISOString()}`);
      
      if (event.event === 'job_started') {
        console.log(`     jobId: ${event.data.jobId}`);
        console.log(`     jobType: ${event.data.jobType}`);
      } else if (event.event === 'job_completed') {
        console.log(`     jobId: ${event.data.jobId}`);
        console.log(`     jobType: ${event.data.jobType}`);
        console.log(`     duration: ${event.data.duration}ms`);
      } else if (event.event === 'execution_duration') {
        console.log(`     duration: ${event.data.duration}ms`);
        console.log(`     status: ${event.data.status}`);
      }
    });
    
    // Test 5: Verify telemetry types
    console.log('\n=== Test 5: Verify Telemetry Types ===');
    
    const eventTypes = telemetry.telemetry.map(e => e.event);
    const hasJobStarted = eventTypes.includes('job_started');
    const hasJobCompleted = eventTypes.includes('job_completed');
    const hasExecutionDuration = eventTypes.includes('execution_duration');
    
    if (hasJobStarted) {
      console.log('✅ job_started events recorded');
    } else {
      console.log('⚠️  No job_started events yet');
    }
    
    if (hasJobCompleted) {
      console.log('✅ job_completed events recorded');
    } else {
      console.log('⚠️  No job_completed events yet');
    }
    
    if (hasExecutionDuration) {
      console.log('✅ execution_duration event recorded');
    } else {
      console.log('⚠️  No execution_duration event yet');
    }
    
    // Test 6: Get all telemetry
    console.log('\n=== Test 6: Get All Telemetry ===');
    
    const allTelemetryResponse = await axios.get(`${BASE_URL}/core/telemetry`);
    
    console.log(`✅ Total executions with telemetry: ${allTelemetryResponse.data.count}`);
    
    // Test 7: Telemetry summary
    console.log('\n=== Test 7: Telemetry Summary ===');
    
    const jobStartedCount = telemetry.telemetry.filter(e => e.event === 'job_started').length;
    const jobCompletedCount = telemetry.telemetry.filter(e => e.event === 'job_completed').length;
    const executionDurationCount = telemetry.telemetry.filter(e => e.event === 'execution_duration').length;
    
    console.log(`   job_started: ${jobStartedCount} events`);
    console.log(`   job_completed: ${jobCompletedCount} events`);
    console.log(`   execution_duration: ${executionDurationCount} events`);
    console.log(`   total: ${telemetry.count} events`);
    
    console.log('\n✅ All telemetry tests completed');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    if (error.response) {
      console.error('Response:', error.response.data);
    }
  }
}

testTelemetry();
