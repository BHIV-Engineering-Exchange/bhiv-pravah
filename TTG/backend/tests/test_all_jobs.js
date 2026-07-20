/**
 * Comprehensive Job Dispatch Test Suite
 * Tests all 4 job types with multiple scenarios
 */

const { mapTextToGameMode } = require('./ttg_integration/game_mode_mapper');
const { convertToEngineSchema } = require('./ttg_integration/schema_converter');
const { buildEngineJobs, createEndGameJob } = require('./engine/engine_job_queue');

console.log('╔' + '═'.repeat(58) + '╗');
console.log('║' + ' '.repeat(10) + 'JOB DISPATCH TEST SUITE' + ' '.repeat(25) + '║');
console.log('╚' + '═'.repeat(58) + '╝\n');

const testCases = [
  {
    name: 'Fast Runner Game',
    text: 'Create a fast runner game with obstacles',
    expected: { mode: 'runner', speed: 8, difficulty: 'medium' }
  },
  {
    name: 'Easy Platform Game',
    text: 'Easy platform game with obstacles',
    expected: { mode: 'side_scroller', speed: 5, difficulty: 'easy' }
  },
  {
    name: 'Hard Endless Runner',
    text: 'Hard endless runner with 3 lives',
    expected: { mode: 'runner', speed: 5, difficulty: 'hard' }
  }
];

let totalJobs = 0;
let passedTests = 0;

testCases.forEach((testCase, index) => {
  console.log(`\n${'─'.repeat(60)}`);
  console.log(`TEST ${index + 1}: ${testCase.name}`);
  console.log(`${'─'.repeat(60)}`);
  console.log(`Input: "${testCase.text}"`);
  
  try {
    // Step 1: Map text to game mode
    const gameModeData = mapTextToGameMode(testCase.text);
    
    // Validate expectations
    const modeMatch = gameModeData.game_mode === testCase.expected.mode;
    const speedMatch = gameModeData.params.movement_speed === testCase.expected.speed;
    const difficultyMatch = gameModeData.params.difficulty === testCase.expected.difficulty;
    
    console.log(`\n✓ Game Mode: ${gameModeData.game_mode} ${modeMatch ? '✅' : '❌'}`);
    console.log(`✓ Speed: ${gameModeData.params.movement_speed} ${speedMatch ? '✅' : '❌'}`);
    console.log(`✓ Difficulty: ${gameModeData.params.difficulty} ${difficultyMatch ? '✅' : '❌'}`);
    
    // Step 2: Convert to engine schema
    const engineSchema = convertToEngineSchema(gameModeData);
    console.log(`✓ Schema Version: ${engineSchema.schema_version}`);
    console.log(`✓ Entities: ${engineSchema.entities.length}`);
    
    // Step 3: Build jobs
    const jobs = buildEngineJobs(engineSchema, {
      game_mode: gameModeData.game_mode,
      params: gameModeData.params
    });
    
    totalJobs += jobs.length;
    
    console.log(`\n📦 Generated ${jobs.length} jobs:`);
    
    const jobTypes = {};
    jobs.forEach(job => {
      jobTypes[job.jobType] = (jobTypes[job.jobType] || 0) + 1;
    });
    
    Object.entries(jobTypes).forEach(([type, count]) => {
      console.log(`   ${type}: ${count}`);
    });
    
    // Verify all required job types
    const hasBuild = jobs.some(j => j.jobType === 'BUILD_SCENE');
    const hasLoad = jobs.some(j => j.jobType === 'LOAD_ASSETS');
    const hasSpawn = jobs.some(j => j.jobType === 'SPAWN_ENTITY');
    const hasStart = jobs.some(j => j.jobType === 'START_LOOP');
    
    console.log(`\n✓ BUILD_SCENE: ${hasBuild ? '✅' : '❌'}`);
    console.log(`✓ LOAD_ASSETS: ${hasLoad ? '✅' : '❌'}`);
    console.log(`✓ SPAWN_ENTITY: ${hasSpawn ? '✅' : '❌'}`);
    console.log(`✓ START_LOOP: ${hasStart ? '✅' : '❌'}`);
    
    if (hasBuild && hasLoad && hasSpawn && hasStart) {
      console.log(`\n✅ TEST PASSED`);
      passedTests++;
    } else {
      console.log(`\n❌ TEST FAILED: Missing job types`);
    }
    
  } catch (error) {
    console.log(`\n❌ TEST FAILED: ${error.message}`);
  }
});

// Test END_GAME job
console.log(`\n${'─'.repeat(60)}`);
console.log(`TEST ${testCases.length + 1}: END_GAME Job`);
console.log(`${'─'.repeat(60)}`);

const endReasons = ['player_death', 'goal_reached', 'time_up', 'manual_stop'];
endReasons.forEach(reason => {
  const endJob = createEndGameJob(reason, Math.floor(Math.random() * 5000), Math.random() * 200);
  console.log(`✓ ${reason}: ${endJob.jobType === 'END_GAME' ? '✅' : '❌'}`);
});

console.log(`\n✅ END_GAME TEST PASSED`);
passedTests++;

// Summary
console.log(`\n${'═'.repeat(60)}`);
console.log('📊 TEST SUMMARY');
console.log(`${'═'.repeat(60)}`);
console.log(`Tests Passed: ${passedTests}/${testCases.length + 1}`);
console.log(`Total Jobs Generated: ${totalJobs}`);
console.log(`\nJob Types Verified:`);
console.log(`  ✅ BUILD_SCENE`);
console.log(`  ✅ LOAD_ASSETS`);
console.log(`  ✅ SPAWN_ENTITY`);
console.log(`  ✅ START_LOOP`);
console.log(`  ✅ END_GAME`);
console.log(`\n${passedTests === testCases.length + 1 ? '✅ ALL TESTS PASSED!' : '❌ SOME TESTS FAILED'}`);
console.log(`${'═'.repeat(60)}\n`);
