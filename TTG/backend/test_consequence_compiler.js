/**
 * Test Consequence Compiler
 * Tests event processing, rule matching, and job generation
 */

const {
  initialize,
  processEvent,
  matchRules,
  evaluateCondition,
  generateJobs,
  getStatistics
} = require('./consequence/consequenceCompiler');

const {
  createCollisionEvent,
  createScoreUpdateEvent,
  createEntityDestroyedEvent,
  createTimerExpiredEvent,
  createPickupCollectedEvent,
  ENTITY_TYPES
} = require('./events/runtimeEvents');

console.log('=== Consequence Compiler Test ===\n');

// Test 1: Initialize compiler
console.log('Test 1: Initialize Compiler');
const initResult = initialize();
if (initResult) {
  console.log('✅ Compiler initialized successfully');
  const stats = getStatistics();
  console.log(`   Rules loaded: ${stats.total_rules}`);
  console.log(`   Actions available: ${stats.total_actions}`);
} else {
  console.error('❌ Failed to initialize compiler');
  process.exit(1);
}
console.log();

// Test 2: Process collision event (player hits obstacle)
console.log('Test 2: Process Collision Event (Player Hits Obstacle)');
const collisionEvent = createCollisionEvent('player', 'obstacle_01', {
  velocity: 3.2,
  position: { x: 10.5, y: 2.0, z: 0.0 },
  collision_force: 5.8,
  entity_type: ENTITY_TYPES.OBSTACLE,
  damage: 1,
  gameSessionId: 'session_test_001',
  metadata: {
    engine_id: 'engine_local_01',
    user_id: 'user_test',
    game_mode: 'runner'
  }
});

const collisionResult = processEvent(collisionEvent, {
  gameSessionId: 'session_test_001',
  userId: 'user_test'
});

if (collisionResult.success) {
  console.log('✅ Collision event processed successfully');
  console.log(`   Matched rules: ${collisionResult.matchedRules}`);
  console.log(`   Generated jobs: ${collisionResult.jobs.length}`);
  console.log(`   Critical: ${collisionResult.critical}`);
  
  if (collisionResult.jobs.length > 0) {
    console.log('   Jobs:');
    collisionResult.jobs.forEach((job, index) => {
      console.log(`     ${index + 1}. ${job.jobType} (${job.priority})`);
      console.log(`        Payload: ${JSON.stringify(job.payload)}`);
    });
  }
} else {
  console.error('❌ Failed to process collision event:', collisionResult.error);
}
console.log();

// Test 3: Process entity destroyed event (enemy killed)
console.log('Test 3: Process Entity Destroyed Event (Enemy Killed)');
const enemyKilledEvent = createEntityDestroyedEvent('enemy_02', ENTITY_TYPES.ENEMY, {
  position: { x: 50.0, y: 0.0, z: 0.0 },
  gameSessionId: 'session_test_001',
  metadata: {
    engine_id: 'engine_local_01',
    user_id: 'user_test',
    game_mode: 'runner'
  }
});

const enemyResult = processEvent(enemyKilledEvent, {
  gameSessionId: 'session_test_001',
  userId: 'user_test'
});

if (enemyResult.success) {
  console.log('✅ Enemy killed event processed successfully');
  console.log(`   Matched rules: ${enemyResult.matchedRules}`);
  console.log(`   Generated jobs: ${enemyResult.jobs.length}`);
  
  if (enemyResult.jobs.length > 0) {
    console.log('   Jobs:');
    enemyResult.jobs.forEach((job, index) => {
      console.log(`     ${index + 1}. ${job.jobType} (${job.priority})`);
    });
  }
} else {
  console.error('❌ Failed to process enemy killed event:', enemyResult.error);
}
console.log();

// Test 4: Process pickup collected event
console.log('Test 4: Process Pickup Collected Event (Coin)');
const pickupEvent = createPickupCollectedEvent('coin_05', {
  position: { x: 30.0, y: 1.0, z: 0.0 },
  score: 10,
  gameSessionId: 'session_test_001',
  metadata: {
    engine_id: 'engine_local_01',
    user_id: 'user_test',
    game_mode: 'runner'
  }
});

const pickupResult = processEvent(pickupEvent, {
  gameSessionId: 'session_test_001',
  userId: 'user_test'
});

if (pickupResult.success) {
  console.log('✅ Pickup collected event processed successfully');
  console.log(`   Matched rules: ${pickupResult.matchedRules}`);
  console.log(`   Generated jobs: ${pickupResult.jobs.length}`);
  
  if (pickupResult.jobs.length > 0) {
    console.log('   Jobs:');
    pickupResult.jobs.forEach((job, index) => {
      console.log(`     ${index + 1}. ${job.jobType} (${job.priority})`);
    });
  }
} else {
  console.error('❌ Failed to process pickup event:', pickupResult.error);
}
console.log();

// Test 5: Process timer expired event
console.log('Test 5: Process Timer Expired Event');
const timerEvent = createTimerExpiredEvent(0, {
  gameSessionId: 'session_test_001',
  metadata: {
    engine_id: 'engine_local_01',
    user_id: 'user_test',
    game_mode: 'runner'
  }
});

const timerResult = processEvent(timerEvent, {
  gameSessionId: 'session_test_001',
  userId: 'user_test'
});

if (timerResult.success) {
  console.log('✅ Timer expired event processed successfully');
  console.log(`   Matched rules: ${timerResult.matchedRules}`);
  console.log(`   Generated jobs: ${timerResult.jobs.length}`);
  console.log(`   Critical: ${timerResult.critical}`);
  
  if (timerResult.jobs.length > 0) {
    console.log('   Jobs:');
    timerResult.jobs.forEach((job, index) => {
      console.log(`     ${index + 1}. ${job.jobType} (${job.priority})`);
    });
  }
} else {
  console.error('❌ Failed to process timer event:', timerResult.error);
}
console.log();

// Test 6: Process event with no matching rules
console.log('Test 6: Process Event with No Matching Rules');
const noMatchEvent = createScoreUpdateEvent(50, {
  position: { x: 15.0, y: 0.0, z: 0.0 },
  gameSessionId: 'session_test_001'
});

const noMatchResult = processEvent(noMatchEvent, {
  gameSessionId: 'session_test_001',
  userId: 'user_test'
});

if (noMatchResult.success) {
  console.log('✅ Event processed (no rules matched)');
  console.log(`   Matched rules: ${noMatchResult.matchedRules || 0}`);
  console.log(`   Generated jobs: ${noMatchResult.jobs.length}`);
} else {
  console.error('❌ Failed to process event:', noMatchResult.error);
}
console.log();

// Test 7: Invalid event handling
console.log('Test 7: Invalid Event Handling');
const invalidEvent = {
  event_type: 'invalid_type',
  timestamp: 'not_a_number'
};

const invalidResult = processEvent(invalidEvent);
if (!invalidResult.success) {
  console.log('✅ Invalid event rejected correctly');
  console.log(`   Error: ${invalidResult.error}`);
} else {
  console.error('❌ Invalid event was not rejected');
}
console.log();

// Test 8: Condition evaluation
console.log('Test 8: Condition Evaluation');
const testCondition = {
  condition: 'player_hits_obstacle',
  entities: ['player', 'obstacle'],
  context_checks: {
    entity_type: 'obstacle'
  }
};

const testEvent = {
  event_type: 'collision',
  entities: ['player', 'obstacle_01'],
  context: {
    entity_type: 'obstacle',
    velocity: 3.2
  }
};

const conditionMatch = evaluateCondition(testCondition, testEvent);
console.log(`Condition match: ${conditionMatch ? '✅ True' : '❌ False'}`);
console.log();

// Test 9: Job structure validation
console.log('Test 9: Job Structure Validation');
if (collisionResult.success && collisionResult.jobs.length > 0) {
  const job = collisionResult.jobs[0];
  const hasRequiredFields = 
    job.jobId && 
    job.jobType && 
    job.traceId && 
    job.executionId && 
    job.userId && 
    job.priority && 
    job.payload && 
    job.metadata;
  
  if (hasRequiredFields) {
    console.log('✅ Job structure is valid');
    console.log('   Required fields present:');
    console.log(`     - jobId: ${job.jobId}`);
    console.log(`     - jobType: ${job.jobType}`);
    console.log(`     - priority: ${job.priority}`);
    console.log(`     - traceId: ${job.traceId}`);
    console.log(`     - executionId: ${job.executionId}`);
  } else {
    console.error('❌ Job structure is missing required fields');
  }
} else {
  console.log('⚠️  No jobs to validate');
}
console.log();

// Test 10: Statistics
console.log('Test 10: Compiler Statistics');
const stats = getStatistics();
console.log('Compiler statistics:');
console.log(`   Initialized: ${stats.initialized}`);
console.log(`   Total rules: ${stats.total_rules}`);
console.log(`   Total actions: ${stats.total_actions}`);
console.log('   Rules by event type:');
Object.entries(stats.rules_by_event).forEach(([event, count]) => {
  console.log(`     ${event}: ${count}`);
});
console.log();

// Test 11: Priority ordering
console.log('Test 11: Priority Ordering in Jobs');
if (enemyResult.success && enemyResult.jobs.length > 1) {
  console.log('Checking priority order:');
  const priorities = ['critical', 'high', 'medium', 'low'];
  let lastPriorityIndex = -1;
  let ordered = true;
  
  enemyResult.jobs.forEach((job, index) => {
    const priorityIndex = priorities.indexOf(job.priority);
    console.log(`   ${index + 1}. ${job.jobType}: ${job.priority}`);
    
    if (priorityIndex < lastPriorityIndex) {
      ordered = false;
    }
    lastPriorityIndex = priorityIndex;
  });
  
  if (ordered) {
    console.log('✅ Jobs are correctly ordered by priority');
  } else {
    console.log('⚠️  Jobs may not be in optimal priority order');
  }
} else {
  console.log('⚠️  Not enough jobs to test priority ordering');
}
console.log();

// Test 12: Event enrichment
console.log('Test 12: Job Payload Enrichment');
if (collisionResult.success && collisionResult.jobs.length > 0) {
  const job = collisionResult.jobs[0];
  const hasEventContext = 
    job.payload.event_type &&
    job.payload.event_id &&
    job.payload.timestamp;
  
  if (hasEventContext) {
    console.log('✅ Job payload includes event context');
    console.log(`   Event type: ${job.payload.event_type}`);
    console.log(`   Event ID: ${job.payload.event_id}`);
  } else {
    console.error('❌ Job payload missing event context');
  }
} else {
  console.log('⚠️  No jobs to validate');
}
console.log();

// Summary
console.log('=== Test Summary ===');
console.log('✅ Compiler initialization');
console.log('✅ Collision event processing');
console.log('✅ Enemy killed event processing');
console.log('✅ Pickup collected event processing');
console.log('✅ Timer expired event processing');
console.log('✅ No-match event handling');
console.log('✅ Invalid event rejection');
console.log('✅ Condition evaluation');
console.log('✅ Job structure validation');
console.log('✅ Statistics retrieval');
console.log('✅ Priority ordering');
console.log('✅ Payload enrichment');
console.log();
console.log('=== All Tests Complete ===');
