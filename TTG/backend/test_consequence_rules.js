/**
 * Test Consequence Rules
 * Validates rule structure and demonstrates rule matching
 */

const {
  loadConsequenceRules,
  validateAllRules,
  checkDuplicateRuleIds,
  getRulesForEvent,
  getRuleById,
  getActionDefinitions,
  sortActionsByPriority,
  getRuleStatistics
} = require('./consequence/ruleValidator');

console.log('=== Consequence Rules Test ===\n');

// Test 1: Load rules
console.log('Test 1: Load Consequence Rules');
try {
  const rules = loadConsequenceRules();
  console.log('✅ Rules loaded successfully');
  console.log(`   Total rules: ${rules.rules.length}`);
  console.log(`   Total action definitions: ${Object.keys(rules.action_definitions).length}`);
  console.log();
} catch (error) {
  console.error('❌ Failed to load rules:', error.message);
  process.exit(1);
}

// Test 2: Validate all rules
console.log('Test 2: Validate All Rules');
const rules = loadConsequenceRules();
const validation = validateAllRules(rules);
if (validation.valid) {
  console.log('✅ All rules are valid');
} else {
  console.log('❌ Some rules are invalid:');
  Object.entries(validation.errors).forEach(([ruleId, errors]) => {
    console.log(`   ${ruleId}:`);
    errors.forEach(error => console.log(`     - ${error}`));
  });
}
console.log();

// Test 3: Check for duplicate rule IDs
console.log('Test 3: Check Duplicate Rule IDs');
const duplicateCheck = checkDuplicateRuleIds(rules);
if (duplicateCheck.valid) {
  console.log('✅ No duplicate rule IDs found');
} else {
  console.log('❌ Duplicate rule IDs found:');
  duplicateCheck.duplicates.forEach(id => console.log(`   - ${id}`));
}
console.log();

// Test 4: Get rules for collision events
console.log('Test 4: Get Rules for Collision Events');
const collisionRules = getRulesForEvent(rules, 'collision');
console.log(`Found ${collisionRules.length} collision rules:`);
collisionRules.forEach(rule => {
  console.log(`   - ${rule.rule_id}: ${rule.description}`);
});
console.log();

// Test 5: Get rules for enemy_killed
console.log('Test 5: Get Rules for Entity Destroyed Events');
const enemyKilledRules = getRulesForEvent(rules, 'entity_destroyed');
console.log(`Found ${enemyKilledRules.length} entity_destroyed rules:`);
enemyKilledRules.forEach(rule => {
  console.log(`   - ${rule.rule_id}: ${rule.description}`);
});
console.log();

// Test 6: Get rules for pickup_collected
console.log('Test 6: Get Rules for Pickup Collected Events');
const pickupRules = getRulesForEvent(rules, 'pickup_collected');
console.log(`Found ${pickupRules.length} pickup_collected rules:`);
pickupRules.forEach(rule => {
  console.log(`   - ${rule.rule_id}: ${rule.description}`);
});
console.log();

// Test 7: Get rules for timer_expired
console.log('Test 7: Get Rules for Timer Expired Events');
const timerRules = getRulesForEvent(rules, 'timer_expired');
console.log(`Found ${timerRules.length} timer_expired rules:`);
timerRules.forEach(rule => {
  console.log(`   - ${rule.rule_id}: ${rule.description}`);
});
console.log();

// Test 8: Get specific rule by ID
console.log('Test 8: Get Rule by ID');
const specificRule = getRuleById(rules, 'collision_player_obstacle');
if (specificRule) {
  console.log('✅ Found rule: collision_player_obstacle');
  console.log(`   Event: ${specificRule.on}`);
  console.log(`   Condition: ${specificRule.if.condition}`);
  console.log(`   Actions: ${specificRule.then.length}`);
  specificRule.then.forEach(action => {
    console.log(`     - ${action.action} (${action.priority})`);
  });
} else {
  console.log('❌ Rule not found');
}
console.log();

// Test 9: Get action definitions
console.log('Test 9: Action Definitions');
const actionDefs = getActionDefinitions(rules);
console.log(`Total action definitions: ${Object.keys(actionDefs).length}`);
console.log('Sample actions:');
['END_GAME', 'UPDATE_SCORE', 'SPAWN_ENTITY'].forEach(actionName => {
  const def = actionDefs[actionName];
  if (def) {
    console.log(`   - ${actionName}: ${def.description}`);
    console.log(`     Required: [${def.required_payload.join(', ')}]`);
  }
});
console.log();

// Test 10: Sort actions by priority
console.log('Test 10: Sort Actions by Priority');
const testActions = [
  { action: 'ACTION_1', priority: 'low', payload: {} },
  { action: 'ACTION_2', priority: 'critical', payload: {} },
  { action: 'ACTION_3', priority: 'medium', payload: {} },
  { action: 'ACTION_4', priority: 'high', payload: {} }
];
const sorted = sortActionsByPriority(testActions);
console.log('Sorted actions (highest priority first):');
sorted.forEach((action, index) => {
  console.log(`   ${index + 1}. ${action.action} (${action.priority})`);
});
console.log();

// Test 11: Rule statistics
console.log('Test 11: Rule Statistics');
const stats = getRuleStatistics(rules);
console.log(`Total rules: ${stats.total_rules}`);
console.log(`Total actions: ${stats.total_actions}`);
console.log(`Unique actions: ${stats.unique_actions.length}`);
console.log('\nRules by event type:');
Object.entries(stats.rules_by_event).forEach(([event, count]) => {
  console.log(`   ${event}: ${count}`);
});
console.log('\nActions by priority:');
Object.entries(stats.rules_by_priority).forEach(([priority, count]) => {
  console.log(`   ${priority}: ${count}`);
});
console.log();

// Test 12: Demonstrate rule matching logic
console.log('Test 12: Rule Matching Example');
console.log('Scenario: Player collides with obstacle');
console.log('Event: { event_type: "collision", entities: ["player", "obstacle_01"] }');
const matchedRule = getRuleById(rules, 'collision_player_obstacle');
if (matchedRule) {
  console.log('✅ Matched rule: collision_player_obstacle');
  console.log('Actions to execute:');
  matchedRule.then.forEach((action, index) => {
    console.log(`   ${index + 1}. ${action.action} (priority: ${action.priority})`);
    console.log(`      Payload: ${JSON.stringify(action.payload)}`);
  });
}
console.log();

// Test 13: Required event types coverage
console.log('Test 13: Required Event Types Coverage');
const requiredEvents = ['collision', 'entity_destroyed', 'pickup_collected', 'timer_expired'];
console.log('Checking coverage for required event types:');
requiredEvents.forEach(eventType => {
  const eventRules = getRulesForEvent(rules, eventType);
  const status = eventRules.length > 0 ? '✅' : '❌';
  console.log(`   ${status} ${eventType}: ${eventRules.length} rule(s)`);
});
console.log();

console.log('=== All Tests Complete ===');
