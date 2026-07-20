const { compile } = require('./intent-layer/compiler/intentCompiler.js');
const { guard } = require('./intent-layer/validators/safetyGuard.js');

const prompts = [
  "fast runner with jump",
  "slow platform game with obstacles",
  "open world sandbox exploration",
  "runner with jetpack and collectibles",
  "sidescroller with low gravity",
  "easy runner for beginners",
  "hard platform challenge",
  "runner with bouncy physics",
  "open scene with slippery ice",
  "fast sidescroller with dash",
  "runner with high gravity",
  "platform game with sticky surfaces",
  "open world with jump ability",
  "runner with time limit",
  "sidescroller with distance goal",
  "casual runner with collectibles",
  "intense platform game",
  "runner with obstacles and jump",
  "open sandbox with jetpack",
  "platform game with score tracking"
];

console.log('=== DAY 5 A: STRESS TEST (20 PROMPTS) ===\n');

let passed = 0;
let failed = 0;
const results = [];

prompts.forEach((prompt, index) => {
  try {
    const schema = compile(prompt);
    const safe = guard(schema);
    
    // Validate required fields
    const valid = 
      safe.game_mode &&
      safe.movement?.speed &&
      safe.camera?.type &&
      safe.spawn_rules &&
      safe.score_rules &&
      safe.end_conditions &&
      safe.player_params &&
      safe.world_params &&
      safe.physics;
    
    if (valid) {
      passed++;
      console.log(`✅ ${index + 1}. "${prompt}" → ${safe.game_mode}`);
      results.push({ prompt, status: 'PASS', gameMode: safe.game_mode });
    } else {
      failed++;
      console.log(`❌ ${index + 1}. "${prompt}" → INVALID SCHEMA`);
      results.push({ prompt, status: 'FAIL', error: 'Missing fields' });
    }
  } catch (error) {
    failed++;
    console.log(`❌ ${index + 1}. "${prompt}" → ERROR: ${error.message}`);
    results.push({ prompt, status: 'FAIL', error: error.message });
  }
});

console.log(`\n=== RESULTS ===`);
console.log(`Total: ${prompts.length}`);
console.log(`Passed: ${passed} ✅`);
console.log(`Failed: ${failed} ❌`);
console.log(`Success Rate: ${((passed / prompts.length) * 100).toFixed(1)}%`);

if (failed === 0) {
  console.log('\n🎉 ALL TESTS PASSED - NO FAILURES');
} else {
  console.log('\n⚠️ FAILURES DETECTED:');
  results.filter(r => r.status === 'FAIL').forEach(r => {
    console.log(`  - "${r.prompt}": ${r.error}`);
  });
}

process.exit(failed > 0 ? 1 : 0);
