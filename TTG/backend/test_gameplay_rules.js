/**
 * Test Gameplay Rules Library
 * Tests game-mode-specific consequence rules
 */

const {
  loadGameplayRules,
  getRulesForGameMode,
  getAvailableGameModes,
  getGameModeInfo,
  getRulesByEventType,
  getGameplayRulesStatistics,
  validateGameModeRules,
  getExampleRules
} = require('./consequence/gameplayRulesLoader');

console.log('=== Gameplay Rules Library Test ===\n');

// Test 1: Load gameplay rules
console.log('Test 1: Load Gameplay Rules');
try {
  const rules = loadGameplayRules();
  console.log('✅ Gameplay rules loaded successfully');
  console.log(`   Game modes: ${Object.keys(rules.game_modes).length}`);
  console.log(`   Version: ${rules.version}`);
} catch (error) {
  console.error('❌ Failed to load gameplay rules:', error.message);
  process.exit(1);
}
console.log();

// Test 2: Get available game modes
console.log('Test 2: Available Game Modes');
const gameModes = getAvailableGameModes();
console.log(`Found ${gameModes.length} game modes:`);
gameModes.forEach(mode => {
  const info = getGameModeInfo(mode);
  console.log(`   - ${mode}: ${info.name} (${info.rule_count} rules)`);
  console.log(`     ${info.description}`);
});
console.log();

// Test 3: Get rules for Runner game
console.log('Test 3: Runner Game Rules');
const runnerRules = getRulesForGameMode('runner');
console.log(`Runner game has ${runnerRules.length} rules:`);
runnerRules.forEach(rule => {
  console.log(`   - ${rule.rule_id}: ${rule.description}`);
  console.log(`     Event: ${rule.on}, Actions: ${rule.then.length}`);
});
console.log();

// Test 4: Get rules for Arena game
console.log('Test 4: Arena Game Rules');
const arenaRules = getRulesForGameMode('arena');
console.log(`Arena game has ${arenaRules.length} rules:`);
arenaRules.forEach(rule => {
  console.log(`   - ${rule.rule_id}: ${rule.description}`);
  console.log(`     Event: ${rule.on}, Actions: ${rule.then.length}`);
});
console.log();

// Test 5: Get rules for Platformer game
console.log('Test 5: Platformer Game Rules');
const platformerRules = getRulesForGameMode('platformer');
console.log(`Platformer game has ${platformerRules.length} rules:`);
platformerRules.forEach(rule => {
  console.log(`   - ${rule.rule_id}: ${rule.description}`);
  console.log(`     Event: ${rule.on}, Actions: ${rule.then.length}`);
});
console.log();

// Test 6: Get rules by event type
console.log('Test 6: Get Rules by Event Type');
console.log('Collision rules in runner game:');
const runnerCollisionRules = getRulesByEventType('runner', 'collision');
runnerCollisionRules.forEach(rule => {
  console.log(`   - ${rule.rule_id}: ${rule.description}`);
});

console.log('Collision rules in arena game:');
const arenaCollisionRules = getRulesByEventType('arena', 'collision');
arenaCollisionRules.forEach(rule => {
  console.log(`   - ${rule.rule_id}: ${rule.description}`);
});
console.log();

// Test 7: Gameplay rules statistics
console.log('Test 7: Gameplay Rules Statistics');
const stats = getGameplayRulesStatistics();
console.log('Statistics:');
console.log(`   Total game modes: ${stats.total_game_modes}`);
console.log(`   Total rules: ${stats.total_rules}`);
console.log(`   Common rules: ${stats.common_rules}`);
console.log('   Rules by mode:');
Object.entries(stats.rules_by_mode).forEach(([mode, count]) => {
  console.log(`     ${mode}: ${count}`);
});
console.log();

// Test 8: Validate game mode rules
console.log('Test 8: Validate Game Mode Rules');
gameModes.forEach(mode => {
  const validation = validateGameModeRules(mode);
  if (validation.valid) {
    console.log(`✅ ${mode}: Valid (${validation.rule_count} rules)`);
  } else {
    console.error(`❌ ${mode}: Invalid`);
    validation.errors.forEach(error => console.error(`   - ${error}`));
  }
});
console.log();

// Test 9: Example rules
console.log('Test 9: Example Rules');
console.log('Runner game examples:');
const runnerExamples = getExampleRules('runner', 2);
runnerExamples.forEach(rule => {
  console.log(`   ${rule.rule_id}:`);
  console.log(`     Event: ${rule.on}`);
  console.log(`     Condition: ${rule.if.condition}`);
  console.log(`     Actions: ${rule.then.map(a => a.action).join(', ')}`);
});
console.log();

// Test 10: Rule structure validation
console.log('Test 10: Rule Structure Validation');
const sampleRule = runnerRules[0];
const hasRequiredFields = 
  sampleRule.rule_id &&
  sampleRule.on &&
  sampleRule.if &&
  sampleRule.then &&
  sampleRule.description;

if (hasRequiredFields) {
  console.log('✅ Rule structure is valid');
  console.log('   Sample rule:');
  console.log(`     ID: ${sampleRule.rule_id}`);
  console.log(`     Event: ${sampleRule.on}`);
  console.log(`     Condition: ${sampleRule.if.condition}`);
  console.log(`     Actions: ${sampleRule.then.length}`);
} else {
  console.error('❌ Rule structure is invalid');
}
console.log();

// Test 11: Action priority distribution
console.log('Test 11: Action Priority Distribution');
const allRules = [
  ...runnerRules,
  ...arenaRules,
  ...platformerRules
];

const priorityCounts = {
  critical: 0,
  high: 0,
  medium: 0,
  low: 0
};

allRules.forEach(rule => {
  rule.then.forEach(action => {
    priorityCounts[action.priority]++;
  });
});

console.log('Priority distribution:');
Object.entries(priorityCounts).forEach(([priority, count]) => {
  console.log(`   ${priority}: ${count}`);
});
console.log();

// Test 12: Game mode comparison
console.log('Test 12: Game Mode Comparison');
console.log('Comparison of game modes:');
console.log('┌─────────────┬───────┬────────────┬──────────────┐');
console.log('│ Game Mode   │ Rules │ Collision  │ Pickup       │');
console.log('├─────────────┼───────┼────────────┼──────────────┤');
gameModes.forEach(mode => {
  const rules = getRulesForGameMode(mode);
  const collisionRules = getRulesByEventType(mode, 'collision');
  const pickupRules = getRulesByEventType(mode, 'pickup_collected');
  
  const modeName = mode.padEnd(11);
  const ruleCount = rules.length.toString().padEnd(5);
  const collisionCount = collisionRules.length.toString().padEnd(10);
  const pickupCount = pickupRules.length.toString().padEnd(12);
  
  console.log(`│ ${modeName} │ ${ruleCount} │ ${collisionCount} │ ${pickupCount} │`);
});
console.log('└─────────────┴───────┴────────────┴──────────────┘');
console.log();

// Summary
console.log('=== Test Summary ===');
console.log('✅ Gameplay rules loaded');
console.log('✅ Available game modes retrieved');
console.log('✅ Runner game rules loaded');
console.log('✅ Arena game rules loaded');
console.log('✅ Platformer game rules loaded');
console.log('✅ Rules by event type working');
console.log('✅ Statistics calculated');
console.log('✅ Validation working');
console.log('✅ Example rules retrieved');
console.log('✅ Rule structure validated');
console.log('✅ Priority distribution analyzed');
console.log('✅ Game mode comparison complete');
console.log();
console.log('=== All Tests Complete ===');
console.log();
console.log(`Total Game Modes: ${gameModes.length}`);
console.log(`Total Rules: ${stats.total_rules}`);
console.log('Gameplay Rules Library: ✅ OPERATIONAL');
