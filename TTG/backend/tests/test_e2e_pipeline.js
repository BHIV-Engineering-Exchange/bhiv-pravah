// Day 13 - End-to-End Pipeline Test
// Prompt → Compiled Schema → Core Endpoint → Engine Execution

const axios = require('axios');
const crypto = require('crypto');

const BASE_URL = 'http://localhost:3000';
const HMAC_SECRET = process.env.HMAC_SECRET || 'HMAC_SECRET_987654321';

// Test prompts
const TEST_PROMPTS = [
  'Make a fast runner with jump and obstacles',
  'Create an easy platform jump game',
  'Runner with collectibles and coins'
];

// Compile prompt to schema (simulating intent-layer)
function compilePrompt(prompt) {
  const lower = prompt.toLowerCase();
  
  return {
    game_mode: lower.includes('platform') ? 'sidescroller' : 'runner',
    movement: {
      speed: lower.includes('fast') ? 8 : lower.includes('slow') ? 3 : 5,
      jump_height: lower.includes('jump') ? 5 : 0
    },
    physics: {
      gravity: -9.8
    },
    spawn_rules: {
      obstacles: lower.includes('obstacle') ? 2 : 0,
      frequency: lower.includes('fast') ? 1.5 : 2.0
    },
    score_rules: {
      distance: lower.includes('collectible') || lower.includes('coin') ? 0 : 1,
      collectibles: lower.includes('collectible') || lower.includes('coin') ? 10 : 0
    },
    end_conditions: ['collision'],
    player_params: {
      jetpack: lower.includes('jetpack'),
      health: lower.includes('easy') ? 5 : lower.includes('hard') ? 1 : 3
    }
  };
}

// Generate HMAC signature with nonce
function generateSignature(execution_id, trace_id, executionSchema, timestamp, nonce) {
  const message = `${execution_id}|${trace_id}|${JSON.stringify(executionSchema)}|${timestamp}|${nonce}`;
  return crypto.createHmac('sha256', HMAC_SECRET).update(message).digest('hex');
}

// Execute end-to-end pipeline
async function runE2EPipeline(prompt, index) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`TEST ${index + 1}: "${prompt}"`);
  console.log('='.repeat(60));
  
  try {
    // Step 1: Compile prompt to schema
    console.log('\n[STEP 1] Compiling prompt to schema...');
    const executionSchema = compilePrompt(prompt);
    console.log('✅ Schema compiled:', JSON.stringify(executionSchema, null, 2));
    
    // Step 2: Prepare execution request
    const execution_id = `exec_e2e_${Date.now()}_${index}`;
    const trace_id = `trace_e2e_${Date.now()}`;
    const timestamp = Date.now();
    const nonce = crypto.randomBytes(16).toString('hex');
    
    // Step 3: Generate signature
    console.log('\n[STEP 2] Generating HMAC signature...');
    const signature = generateSignature(execution_id, trace_id, executionSchema, timestamp, nonce);
    console.log('✅ Signature generated');
    
    const payload = {
      execution_id,
      trace_id,
      executionSchema,
      user_id: 'test_user',
      timestamp,
      nonce,
      signature,
      intent: { prompt }
    };
    
    // Step 4: Send to core endpoint
    console.log('\n[STEP 3] Sending to /core/execute...');
    const response = await axios.post(`${BASE_URL}/core/execute`, payload, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log('✅ Core endpoint response:', response.data);
    
    // Step 5: Poll execution status
    console.log('\n[STEP 4] Polling execution status...');
    let attempts = 0;
    const maxAttempts = 20;
    
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const statusResponse = await axios.get(`${BASE_URL}/core/execution/${execution_id}?detailed=true`);
      const execution = statusResponse.data.execution;
      
      console.log(`   [${attempts + 1}/${maxAttempts}] Status: ${execution.status} | Jobs: ${execution.jobs?.completed || 0}/${execution.jobs?.total || 0}`);
      
      if (execution.status === 'completed') {
        console.log('\n✅ Execution completed successfully!');
        console.log('   Duration:', execution.duration, 'ms');
        console.log('   Jobs completed:', execution.jobs.completed);
        return { success: true, execution };
      }
      
      if (execution.status === 'failed') {
        console.log('\n❌ Execution failed:', execution.error);
        return { success: false, error: execution.error };
      }
      
      attempts++;
    }
    
    console.log('\n⚠️  Timeout waiting for execution to complete');
    return { success: false, error: 'Timeout' };
    
  } catch (error) {
    console.error('\n❌ Pipeline failed:', error.message);
    if (error.response) {
      console.error('   Response:', error.response.data);
    }
    return { success: false, error: error.message };
  }
}

// Run all tests
async function runAllTests() {
  console.log('\n🚀 Starting End-to-End Pipeline Tests');
  console.log('   Prompt → Schema → Core → Engine\n');
  
  const results = [];
  
  for (let i = 0; i < TEST_PROMPTS.length; i++) {
    const result = await runE2EPipeline(TEST_PROMPTS[i], i);
    results.push(result);
    
    // Wait between tests
    if (i < TEST_PROMPTS.length - 1) {
      console.log('\n⏳ Waiting 3s before next test...');
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
  }
  
  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('TEST SUMMARY');
  console.log('='.repeat(60));
  
  const passed = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;
  
  console.log(`\n✅ Passed: ${passed}/${results.length}`);
  console.log(`❌ Failed: ${failed}/${results.length}`);
  
  results.forEach((result, i) => {
    const status = result.success ? '✅' : '❌';
    console.log(`   ${status} Test ${i + 1}: "${TEST_PROMPTS[i]}"`);
  });
  
  console.log('\n' + '='.repeat(60));
  
  process.exit(failed > 0 ? 1 : 0);
}

// Run tests
runAllTests().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
