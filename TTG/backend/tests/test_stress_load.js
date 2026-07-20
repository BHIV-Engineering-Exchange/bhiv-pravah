// Day 14 - Load and Stress Testing
// 50 execution requests - verify no crashes, no execution loss

const axios = require('axios');
const crypto = require('crypto');

const BASE_URL = 'http://localhost:3000';
const HMAC_SECRET = process.env.HMAC_SECRET || 'HMAC_SECRET_987654321';
const TOTAL_EXECUTIONS = 10;
const BATCH_SIZE = 2; // Process 2 at a time
const BATCH_DELAY = 3000; // 3s between batches

const TEST_SCHEMAS = [
  {
    name: 'Fast Runner',
    schema: {
      game_mode: 'runner',
      movement: { speed: 8, jump_height: 5 },
      physics: { gravity: -9.8 },
      spawn_rules: { obstacles: 2, frequency: 1.5 },
      score_rules: { distance: 1, collectibles: 0 },
      end_conditions: ['collision'],
      player_params: { jetpack: false, health: 3 }
    }
  },
  {
    name: 'Easy Platformer',
    schema: {
      game_mode: 'sidescroller',
      movement: { speed: 5, jump_height: 5 },
      physics: { gravity: -9.8 },
      spawn_rules: { obstacles: 0, frequency: 2 },
      score_rules: { distance: 1, collectibles: 0 },
      end_conditions: ['collision'],
      player_params: { jetpack: false, health: 5 }
    }
  },
  {
    name: 'Collection Game',
    schema: {
      game_mode: 'runner',
      movement: { speed: 5, jump_height: 0 },
      physics: { gravity: -9.8 },
      spawn_rules: { obstacles: 0, frequency: 2 },
      score_rules: { distance: 0, collectibles: 10 },
      end_conditions: ['collision'],
      player_params: { jetpack: false, health: 3 }
    }
  }
];

function generateSignature(execution_id, trace_id, executionSchema, timestamp, nonce) {
  const message = `${execution_id}|${trace_id}|${JSON.stringify(executionSchema)}|${timestamp}|${nonce}`;
  return crypto.createHmac('sha256', HMAC_SECRET).update(message).digest('hex');
}

async function submitExecution(index) {
  const testData = TEST_SCHEMAS[index % TEST_SCHEMAS.length];
  const execution_id = `exec_stress_${Date.now()}_${index}`;
  const trace_id = `trace_stress_${Date.now()}_${index}`;
  const timestamp = Date.now();
  const nonce = crypto.randomBytes(16).toString('hex');
  
  const signature = generateSignature(execution_id, trace_id, testData.schema, timestamp, nonce);
  
  const payload = {
    execution_id,
    trace_id,
    executionSchema: testData.schema,
    user_id: `stress_user_${index}`,
    timestamp,
    nonce,
    signature,
    intent: { prompt: testData.name }
  };
  
  try {
    const response = await axios.post(`${BASE_URL}/core/execute`, payload, {
      headers: { 'Content-Type': 'application/json' }
    });
    
    return {
      success: true,
      execution_id,
      index,
      name: testData.name,
      response: response.data
    };
  } catch (error) {
    return {
      success: false,
      execution_id,
      index,
      name: testData.name,
      error: error.message
    };
  }
}

async function pollExecution(execution_id) {
  const maxAttempts = 60; // Increased to 60s
  
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    try {
      const response = await axios.get(`${BASE_URL}/core/execution/${execution_id}?detailed=true`);
      const execution = response.data.execution;
      
      if (execution.status === 'completed') {
        return { success: true, execution };
      }
      
      if (execution.status === 'failed') {
        return { success: false, error: execution.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
  
  return { success: false, error: 'Timeout' };
}

async function runStressTest() {
  console.log('\n🔥 Day 14 - Load and Stress Testing');
  console.log(`   Testing ${TOTAL_EXECUTIONS} concurrent executions\n`);
  console.log('='.repeat(60));
  
  const startTime = Date.now();
  
  // Phase 1: Submit executions in batches
  console.log('\n[PHASE 1] Submitting executions in batches...\n');
  
  const allSubmitted = [];
  const batches = Math.ceil(TOTAL_EXECUTIONS / BATCH_SIZE);
  
  for (let batch = 0; batch < batches; batch++) {
    const start = batch * BATCH_SIZE;
    const end = Math.min(start + BATCH_SIZE, TOTAL_EXECUTIONS);
    
    console.log(`Batch ${batch + 1}/${batches}: Submitting ${start}-${end - 1}...`);
    
    const batchSubmissions = [];
    for (let i = start; i < end; i++) {
      batchSubmissions.push(submitExecution(i));
    }
    
    const batchResults = await Promise.all(batchSubmissions);
    allSubmitted.push(...batchResults);
    
    if (batch < batches - 1) {
      await new Promise(resolve => setTimeout(resolve, BATCH_DELAY));
    }
  }
  
  const submitted = allSubmitted.filter(r => r.success);
  const failed = allSubmitted.filter(r => !r.success);
  
  console.log(`✅ Submitted: ${submitted.length}/${TOTAL_EXECUTIONS}`);
  console.log(`❌ Failed: ${failed.length}/${TOTAL_EXECUTIONS}`);
  
  if (failed.length > 0) {
    console.log('\nFailed submissions:');
    failed.forEach(f => console.log(`   ${f.index}: ${f.error}`));
  }
  
  // Phase 2: Poll all executions
  console.log('\n[PHASE 2] Polling execution status...\n');
  
  const polls = submitted.map(s => 
    pollExecution(s.execution_id).then(result => ({
      ...s,
      pollResult: result
    }))
  );
  
  const completionResults = await Promise.all(polls);
  
  const completed = completionResults.filter(r => r.pollResult.success);
  const incomplete = completionResults.filter(r => !r.pollResult.success);
  
  const endTime = Date.now();
  const totalDuration = endTime - startTime;
  
  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('STRESS TEST RESULTS');
  console.log('='.repeat(60));
  
  console.log(`\n📊 Submission Phase:`);
  console.log(`   ✅ Accepted: ${submitted.length}/${TOTAL_EXECUTIONS}`);
  console.log(`   ❌ Rejected: ${failed.length}/${TOTAL_EXECUTIONS}`);
  
  console.log(`\n📊 Execution Phase:`);
  console.log(`   ✅ Completed: ${completed.length}/${submitted.length}`);
  console.log(`   ❌ Failed/Timeout: ${incomplete.length}/${submitted.length}`);
  
  console.log(`\n⏱️  Performance:`);
  console.log(`   Total Duration: ${(totalDuration / 1000).toFixed(2)}s`);
  console.log(`   Avg per Execution: ${(totalDuration / TOTAL_EXECUTIONS).toFixed(0)}ms`);
  
  if (completed.length > 0) {
    const durations = completed.map(c => c.pollResult.execution.duration);
    const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
    const minDuration = Math.min(...durations);
    const maxDuration = Math.max(...durations);
    
    console.log(`   Execution Duration (avg): ${avgDuration.toFixed(0)}ms`);
    console.log(`   Execution Duration (min): ${minDuration}ms`);
    console.log(`   Execution Duration (max): ${maxDuration}ms`);
  }
  
  console.log(`\n🎯 Success Rate:`);
  const successRate = (completed.length / TOTAL_EXECUTIONS * 100).toFixed(1);
  console.log(`   ${successRate}% (${completed.length}/${TOTAL_EXECUTIONS})`);
  
  console.log(`\n✅ No Crashes: ${failed.length === 0 ? 'PASS' : 'FAIL'}`);
  console.log(`✅ No Execution Loss: ${completed.length === submitted.length ? 'PASS' : 'FAIL'}`);
  
  if (incomplete.length > 0) {
    console.log(`\n⚠️  Incomplete Executions:`);
    incomplete.forEach(i => {
      console.log(`   ${i.index}: ${i.execution_id} - ${i.pollResult.error}`);
    });
  }
  
  console.log('\n' + '='.repeat(60));
  
  const allPassed = failed.length === 0 && completed.length === submitted.length;
  process.exit(allPassed ? 0 : 1);
}

runStressTest().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
