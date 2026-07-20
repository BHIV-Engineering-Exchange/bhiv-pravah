/**
 * Consequence Compiler
 * Converts runtime events into engine-safe jobs using consequence rules
 * 
 * Flow:
 * 1. Receive runtime event
 * 2. Validate event
 * 3. Match consequence rules
 * 4. Evaluate conditions
 * 5. Extract actions
 * 6. Sort by priority
 * 7. Generate engine jobs
 * 8. Pass to dispatcher
 */

const { validateRuntimeEvent, isCriticalEvent } = require('../events/runtimeEvents');
const {
  loadConsequenceRules,
  getRulesForEvent,
  sortActionsByPriority,
  getActionDefinitions
} = require('./ruleValidator');
const { v4: uuidv4 } = require('uuid');
const EventEmitter = require('events');

// Event emitter for consequence processing
const consequenceEvents = new EventEmitter();

// Load rules once at startup
let consequenceRules = null;
let actionDefinitions = null;

/**
 * Initialize the consequence compiler
 */
function initialize() {
  try {
    consequenceRules = loadConsequenceRules();
    actionDefinitions = getActionDefinitions(consequenceRules);
    console.log('[CONSEQUENCE COMPILER] Initialized with', consequenceRules.rules.length, 'rules');
    return true;
  } catch (error) {
    console.error('[CONSEQUENCE COMPILER] Failed to initialize:', error.message);
    return false;
  }
}

/**
 * Process a runtime event and generate jobs
 * @param {Object} event - Runtime event
 * @param {Object} options - Processing options
 * @returns {Object} { success: boolean, jobs: Array, error?: string }
 */
function processEvent(event, options = {}) {
  const {
    dispatchImmediately = true,
    gameSessionId = null,
    userId = null,
    gameState = null   // Phase 7: optional current game state snapshot
  } = options;

  try {
    // Step 1: Validate event
    const validation = validateRuntimeEvent(event);
    if (!validation.valid) {
      console.error('[CONSEQUENCE COMPILER] Invalid event:', validation.errors);
      return {
        success: false,
        jobs: [],
        error: `Invalid event: ${validation.errors.join(', ')}`
      };
    }

    // Step 2: Check if critical
    const critical = isCriticalEvent(event);
    if (critical) {
      console.log('[CONSEQUENCE COMPILER] Processing CRITICAL event:', event.event_type);
    }

    // Step 3: Match rules (state-aware if gameState provided)
    const matchedRules = matchRules(event, gameState);
    if (matchedRules.length === 0) {
      console.log('[CONSEQUENCE COMPILER] No rules matched for event:', event.event_type);
      return {
        success: true,
        jobs: [],
        message: 'No matching rules'
      };
    }

    console.log(`[CONSEQUENCE COMPILER] Matched ${matchedRules.length} rule(s) for ${event.event_type}`);

    // Step 4: Extract actions
    const actions = extractActions(matchedRules);

    // Step 5: Sort by priority
    const sortedActions = sortActionsByPriority(actions);

    // Step 6: Generate jobs
    const jobs = generateJobs(sortedActions, event, {
      gameSessionId,
      userId,
      critical
    });

    console.log(`[CONSEQUENCE COMPILER] Generated ${jobs.length} job(s) from ${actions.length} action(s)`);

    // Step 7: Emit event
    consequenceEvents.emit('jobs_generated', {
      event,
      matchedRules: matchedRules.length,
      jobs: jobs.length,
      critical
    });

    return {
      success: true,
      jobs,
      matchedRules: matchedRules.length,
      critical
    };

  } catch (error) {
    console.error('[CONSEQUENCE COMPILER] Error processing event:', error.message);
    return {
      success: false,
      jobs: [],
      error: error.message
    };
  }
}

/**
 * Match consequence rules to event
 * @param {Object} event - Runtime event
 * @param {Object|null} gameState - Current game state snapshot (Phase 7)
 * @returns {Array} Matched rules
 */
function matchRules(event, gameState = null) {
  if (!consequenceRules) {
    throw new Error('Consequence compiler not initialized');
  }

  // Get rules for this event type
  const candidateRules = getRulesForEvent(consequenceRules, event.event_type);

  // Filter by condition — pass state for state_checks evaluation
  const matchedRules = candidateRules.filter(rule => {
    return evaluateCondition(rule.if, event, gameState);
  });

  return matchedRules;
}

/**
 * Evaluate if a rule condition matches the event + current state.
 * @param {Object} condition  - Rule condition
 * @param {Object} event      - Runtime event
 * @param {Object|null} state - Current game state snapshot (may be null for stateless rules)
 * @returns {boolean} True if condition matches
 */
function evaluateCondition(condition, event, state = null) {
  // Check entity match
  if (condition.entities && condition.entities.length > 0) {
    const hasAllEntities = condition.entities.every(requiredEntity => {
      return event.entities && event.entities.some(eventEntity => {
        return eventEntity === requiredEntity ||
               eventEntity.includes(requiredEntity) ||
               requiredEntity === 'player'   && eventEntity.startsWith('player')   ||
               requiredEntity === 'enemy'    && eventEntity.startsWith('enemy')    ||
               requiredEntity === 'obstacle' && eventEntity.startsWith('obstacle');
      });
    });
    if (!hasAllEntities) return false;
  }

  // Check context conditions (event data)
  if (condition.context_checks) {
    const contextMatch = Object.entries(condition.context_checks).every(([key, value]) => {
      const eventValue = event.context?.[key];
      if (typeof value === 'object' && value.operator) {
        return evaluateOperator(eventValue, value.operator, value.value);
      }
      return eventValue === value;
    });
    if (!contextMatch) return false;
  }

  // ── Phase 7: state_checks — evaluate against current game state ──────────
  if (condition.state_checks && state) {
    const stateMatch = Object.entries(condition.state_checks).every(([path, value]) => {
      const stateValue = _resolveStatePath(state, path);
      if (typeof value === 'object' && value.operator) {
        return evaluateOperator(stateValue, value.operator, value.value);
      }
      return stateValue === value;
    });
    if (!stateMatch) return false;
  }

  return true;
}

/**
 * Evaluate operator-based condition
 * @param {*} eventValue - Value from event
 * @param {string} operator - Comparison operator
 * @param {*} ruleValue - Value from rule
 * @returns {boolean} True if condition met
 */
function evaluateOperator(eventValue, operator, ruleValue) {
  switch (operator) {
    case '>=':
      return eventValue >= ruleValue;
    case '<=':
      return eventValue <= ruleValue;
    case '>':
      return eventValue > ruleValue;
    case '<':
      return eventValue < ruleValue;
    case '==':
      return eventValue == ruleValue;
    case '!=':
      return eventValue != ruleValue;
    default:
      return false;
  }
}

/**
 * Extract actions from matched rules
 * @param {Array} rules - Matched rules
 * @returns {Array} Actions with metadata
 */
function extractActions(rules) {
  const actions = [];

  rules.forEach(rule => {
    rule.then.forEach(action => {
      actions.push({
        ...action,
        rule_id: rule.rule_id,
        rule_description: rule.description
      });
    });
  });

  return actions;
}

/**
 * Generate engine jobs from actions
 * @param {Array} actions - Sorted actions
 * @param {Object} event - Original runtime event
 * @param {Object} context - Additional context
 * @returns {Array} Engine jobs
 */
function generateJobs(actions, event, context) {
  const jobs = [];

  actions.forEach((action, index) => {
    const job = createJobFromAction(action, event, context, index);
    if (job) {
      jobs.push(job);
    }
  });

  return jobs;
}

/**
 * Create a single job from an action
 * @param {Object} action - Action definition
 * @param {Object} event - Runtime event
 * @param {Object} context - Job context
 * @param {number} index - Action index
 * @returns {Object} Engine job
 */
function createJobFromAction(action, event, context, index) {
  const { gameSessionId, userId, critical } = context;

  // Base job structure
  const job = {
    jobId: `${action.action.toLowerCase()}_${event.event_id}_${index}`,
    jobType: action.action,
    traceId: event.event_id,
    executionId: gameSessionId || event.game_session_id || 'unknown',
    userId: userId || event.metadata?.user_id || 'unknown',
    priority: action.priority,
    critical: critical || false,
    payload: {
      ...action.payload,
      // Include event context for reference
      event_type: event.event_type,
      event_id: event.event_id,
      timestamp: event.timestamp
    },
    metadata: {
      rule_id: action.rule_id,
      rule_description: action.rule_description,
      source: 'consequence_compiler'
    },
    status: 'queued',
    queuedAt: Date.now()
  };

  // Enrich payload based on action type
  enrichJobPayload(job, action, event);

  return job;
}

/**
 * Enrich job payload with event-specific data
 * @param {Object} job - Job to enrich
 * @param {Object} action - Action definition
 * @param {Object} event - Runtime event
 */
function enrichJobPayload(job, action, event) {
  switch (action.action) {
    case 'END_GAME':
      job.payload.final_score = event.context?.score || 0;
      job.payload.game_session_id = event.game_session_id;
      break;

    case 'UPDATE_SCORE':
      job.payload.current_score = event.context?.score || 0;
      job.payload.position = event.context?.position;
      break;

    case 'SPAWN_ENTITY':
      job.payload.position = event.context?.position || { x: 0, y: 0, z: 0 };
      job.payload.spawn_reason = event.event_type;
      break;

    case 'DAMAGE_PLAYER':
      job.payload.source_entity = event.entities?.[1] || 'unknown';
      job.payload.collision_force = event.context?.collision_force || 0;
      break;

    case 'PLAY_SOUND':
      job.payload.position = event.context?.position;
      job.payload.volume = 1.0;
      break;

    case 'RESPAWN_PLAYER':
      job.payload.last_position = event.context?.position;
      break;

    default:
      // No additional enrichment needed
      break;
  }
}

/**
 * Dispatch jobs to the job queue
 * @param {Array} jobs - Jobs to dispatch
 * @returns {Object} Dispatch result
 */
function dispatchJobs(jobs) {
  if (jobs.length === 0) {
    return { success: true, dispatched: 0 };
  }

  try {
    const { addJob } = require('../jobQueue');

    let dispatched = 0;
    jobs.forEach(job => {
      addJob(
        job,
        (updatedJob, status, error) => {
          handleJobStatusUpdate(updatedJob, status, error);
        },
        null // gameplayContract - not needed for consequence jobs
      );
      dispatched++;
    });

    console.log(`[CONSEQUENCE COMPILER] Dispatched ${dispatched} job(s) to queue`);

    return { success: true, dispatched };

  } catch (error) {
    console.error('[CONSEQUENCE COMPILER] Failed to dispatch jobs:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Handle job status updates
 * @param {Object} job - Updated job
 * @param {string} status - New status
 * @param {string} error - Error message if failed
 */
function handleJobStatusUpdate(job, status, error) {
  console.log(`[CONSEQUENCE COMPILER] Job ${job.jobId} → ${status}`);

  consequenceEvents.emit('job_status_updated', {
    jobId: job.jobId,
    jobType: job.jobType,
    status,
    error
  });

  if (status === 'completed') {
    console.log(`[CONSEQUENCE COMPILER] Job ${job.jobId} completed successfully`);
  } else if (status === 'failed') {
    console.error(`[CONSEQUENCE COMPILER] Job ${job.jobId} failed:`, error);
  }
}

/**
 * Process event and dispatch jobs in one call
 * @param {Object} event - Runtime event
 * @param {Object} options - Processing options
 * @returns {Object} Result
 */
function processAndDispatch(event, options = {}) {
  const result = processEvent(event, options);

  if (result.success && result.jobs.length > 0) {
    const dispatchResult = dispatchJobs(result.jobs);
    return {
      ...result,
      dispatched: dispatchResult.dispatched,
      dispatchSuccess: dispatchResult.success
    };
  }

  return {
    ...result,
    dispatched: 0,
    dispatchSuccess: true
  };
}

/**
 * Get compiler statistics
 * @returns {Object} Statistics
 */
function getStatistics() {
  if (!consequenceRules) {
    return { initialized: false };
  }

  return {
    initialized: true,
    total_rules: consequenceRules.rules.length,
    total_actions: actionDefinitions ? Object.keys(actionDefinitions).length : 0,
    rules_by_event: consequenceRules.rules.reduce((acc, rule) => {
      acc[rule.on] = (acc[rule.on] || 0) + 1;
      return acc;
    }, {})
  };
}

/**
 * State-aware entry point (Phase 7).
 * Reads current game state from GSM automatically using sessionId.
 *
 * @param {Object} event
 * @param {Object} options  — same as processEvent, plus { sessionId }
 * @returns {Object} same shape as processEvent
 */
function processEventWithState(event, options = {}) {
  const { sessionId } = options;
  let gameState = null;

  if (sessionId) {
    try {
      const gsm = require('../state/gameStateManager');
      gameState = gsm.getCurrentState(sessionId);
    } catch (err) {
      console.warn('[CONSEQUENCE COMPILER] Could not load state for session:', sessionId);
    }
  }

  return processEvent(event, { ...options, gameState });
}

/**
 * Resolve a dot-notation path against the state object.
 * e.g. 'entities.enemy_count' → state.entities.enemy_count
 */
function _resolveStatePath(state, path) {
  return path.split('.').reduce((obj, key) => obj?.[key], state);
}

// Initialize on module load
initialize();

module.exports = {
  initialize,
  processEvent,
  processEventWithState,
  processAndDispatch,
  matchRules,
  evaluateCondition,
  generateJobs,
  dispatchJobs,
  getStatistics,
  consequenceEvents
};
