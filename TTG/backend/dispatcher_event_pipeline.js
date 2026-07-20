/**
 * Dispatcher Event Pipeline
 * Integrates consequence compiler with execution dispatcher
 * 
 * Flow:
 * Runtime Event → Consequence Compiler → Job Queue → Engine
 * 
 * This module bridges the gap between gameplay events and engine execution
 */

const { processAndDispatch, consequenceEvents } = require('./consequence/consequenceCompiler');
const { validateRuntimeEvent, isCriticalEvent } = require('./events/runtimeEvents');
const { guardEvent, getViolations } = require('./consequence/eventSafetyGuard');
const { recordTelemetry } = require('./engine/engine_telemetry');
const EventEmitter = require('events');

// Event emitter for pipeline monitoring
const pipelineEvents = new EventEmitter();

// Pipeline statistics
const stats = {
  events_received: 0,
  events_processed: 0,
  events_failed: 0,
  jobs_generated: 0,
  jobs_dispatched: 0,
  critical_events: 0,
  last_event_time: null,
  start_time: Date.now()
};

/**
 * Process runtime event through the consequence pipeline
 * @param {Object} event - Runtime event from engine
 * @param {Object} context - Processing context
 * @returns {Object} Processing result
 */
function processRuntimeEvent(event, context = {}) {
  const {
    gameSessionId = null,
    userId = null,
    engineId = null
  } = context;

  stats.events_received++;
  stats.last_event_time = Date.now();

  try {
    // Step 1: Safety guard (rate limit, duplicate, loop, type, timestamp)
    const guard = guardEvent(event, gameSessionId);
    if (!guard.allowed) {
      console.warn('[PIPELINE] Event blocked by safety guard:', guard.reason);
      stats.events_failed++;

      recordTelemetry({
        event: 'EVENT_BLOCKED_BY_SAFETY_GUARD',
        engineId: engineId || 'unknown',
        payload: { event_type: event.event_type, reason: guard.reason }
      });

      return { success: false, error: guard.reason, stage: 'safety_guard' };
    }

    // Step 2: Schema validation
    const validation = validateRuntimeEvent(event);
    if (!validation.valid) {
      console.error('[PIPELINE] Invalid runtime event:', validation.errors);
      stats.events_failed++;

      recordTelemetry({
        event: 'RUNTIME_EVENT_INVALID',
        engineId: engineId || 'unknown',
        payload: { event_type: event.event_type, errors: validation.errors }
      });

      return {
        success: false,
        error: `Invalid event: ${validation.errors.join(', ')}`,
        stage: 'validation'
      };
    }

    // Step 3: Check if critical
    const critical = isCriticalEvent(event);
    if (critical) {
      stats.critical_events++;
      console.log('[PIPELINE] Processing CRITICAL event:', event.event_type);
    }

    // Step 4: Process through consequence compiler
    const result = processAndDispatch(event, {
      gameSessionId,
      userId,
      dispatchImmediately: true
    });

    if (!result.success) {
      console.error('[PIPELINE] Consequence processing failed:', result.error);
      stats.events_failed++;
      
      recordTelemetry({
        event: 'CONSEQUENCE_PROCESSING_FAILED',
        engineId: engineId || 'unknown',
        payload: {
          event_type: event.event_type,
          event_id: event.event_id,
          error: result.error
        }
      });

      return {
        success: false,
        error: result.error,
        stage: 'consequence_processing'
      };
    }

    // Step 5: Update statistics
    stats.events_processed++;
    stats.jobs_generated += result.jobs.length;
    stats.jobs_dispatched += result.dispatched || 0;

    // Step 6: Record telemetry
    recordTelemetry({
      event: 'RUNTIME_EVENT_PROCESSED',
      engineId: engineId || 'unknown',
      payload: {
        event_type: event.event_type,
        event_id: event.event_id,
        matched_rules: result.matchedRules,
        jobs_generated: result.jobs.length,
        jobs_dispatched: result.dispatched,
        critical
      }
    });

    // Step 7: Emit pipeline event
    pipelineEvents.emit('event_processed', {
      event,
      result,
      critical,
      timestamp: Date.now()
    });

    console.log(`[PIPELINE] Event processed: ${event.event_type} → ${result.dispatched} job(s) dispatched`);

    return {
      success: true,
      event_type: event.event_type,
      event_id: event.event_id,
      matched_rules: result.matchedRules,
      jobs_generated: result.jobs.length,
      jobs_dispatched: result.dispatched,
      critical,
      stage: 'completed'
    };

  } catch (error) {
    console.error('[PIPELINE] Unexpected error:', error.message);
    stats.events_failed++;

    recordTelemetry({
      event: 'PIPELINE_ERROR',
      engineId: engineId || 'unknown',
      payload: {
        event_type: event.event_type,
        error: error.message
      }
    });

    return {
      success: false,
      error: error.message,
      stage: 'exception'
    };
  }
}

/**
 * Setup runtime event handler for engine socket
 * @param {Object} socket - Engine socket
 * @param {Object} context - Socket context
 */
function setupRuntimeEventHandler(socket, context = {}) {
  const { engineId, userId } = context;

  console.log('[PIPELINE] Setting up runtime event handler for engine:', engineId);

  // Listen for runtime events from engine
  socket.on('runtime_event', (rawEvent) => {
    console.log('[PIPELINE] Received runtime event:', rawEvent.event_type);

    // Process event through pipeline
    const result = processRuntimeEvent(rawEvent, {
      gameSessionId: rawEvent.game_session_id,
      userId: userId || rawEvent.metadata?.user_id,
      engineId
    });

    // Send acknowledgement to engine
    socket.emit('runtime_event_ack', {
      event_id: rawEvent.event_id,
      success: result.success,
      jobs_dispatched: result.jobs_dispatched || 0,
      error: result.error || null,
      timestamp: Date.now()
    });

    // Emit to dashboard clients if needed
    if (result.success && result.critical) {
      socket.broadcast.emit('critical_event', {
        event_type: rawEvent.event_type,
        event_id: rawEvent.event_id,
        jobs_dispatched: result.jobs_dispatched
      });
    }
  });

  // Listen for batch runtime events (optimization for high-frequency events)
  socket.on('runtime_events_batch', (events) => {
    console.log(`[PIPELINE] Received batch of ${events.length} runtime events`);

    const results = events.map(event => 
      processRuntimeEvent(event, {
        gameSessionId: event.game_session_id,
        userId: userId || event.metadata?.user_id,
        engineId
      })
    );

    const successful = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;

    socket.emit('runtime_events_batch_ack', {
      total: events.length,
      successful,
      failed,
      timestamp: Date.now()
    });

    console.log(`[PIPELINE] Batch processed: ${successful} success, ${failed} failed`);
  });
}

/**
 * Get pipeline statistics
 * @returns {Object} Statistics
 */
function getPipelineStatistics() {
  const uptime = Date.now() - stats.start_time;
  const uptimeSeconds = Math.floor(uptime / 1000);

  return {
    ...stats,
    uptime_ms: uptime,
    uptime_seconds: uptimeSeconds,
    events_per_second: uptimeSeconds > 0 ? (stats.events_processed / uptimeSeconds).toFixed(2) : 0,
    success_rate: stats.events_received > 0 
      ? ((stats.events_processed / stats.events_received) * 100).toFixed(2) + '%'
      : '0%',
    average_jobs_per_event: stats.events_processed > 0
      ? (stats.jobs_generated / stats.events_processed).toFixed(2)
      : 0
  };
}

/**
 * Reset pipeline statistics
 */
function resetStatistics() {
  stats.events_received = 0;
  stats.events_processed = 0;
  stats.events_failed = 0;
  stats.jobs_generated = 0;
  stats.jobs_dispatched = 0;
  stats.critical_events = 0;
  stats.last_event_time = null;
  stats.start_time = Date.now();
  
  console.log('[PIPELINE] Statistics reset');
}

/**
 * Health check for pipeline
 * @returns {Object} Health status
 */
function getHealthStatus() {
  const now = Date.now();
  const timeSinceLastEvent = stats.last_event_time 
    ? now - stats.last_event_time 
    : null;

  const healthy = stats.events_failed === 0 || 
    (stats.events_received > 0 && (stats.events_processed / stats.events_received) > 0.9);

  return {
    healthy,
    status: healthy ? 'operational' : 'degraded',
    events_received: stats.events_received,
    events_processed: stats.events_processed,
    events_failed: stats.events_failed,
    time_since_last_event_ms: timeSinceLastEvent,
    uptime_ms: now - stats.start_time
  };
}

/**
 * Example pipeline flow for testing
 * @param {string} eventType - Type of event to simulate
 * @returns {Object} Result
 */
function simulatePipelineFlow(eventType = 'collision') {
  const { createCollisionEvent, createEntityDestroyedEvent, createPickupCollectedEvent } = require('./events/runtimeEvents');

  let event;
  switch (eventType) {
    case 'collision':
      event = createCollisionEvent('player', 'obstacle_01', {
        velocity: 3.2,
        entity_type: 'obstacle',
        gameSessionId: 'test_session'
      });
      break;
    case 'enemy_killed':
      event = createEntityDestroyedEvent('enemy_02', 'enemy', {
        gameSessionId: 'test_session'
      });
      break;
    case 'pickup':
      event = createPickupCollectedEvent('coin_05', {
        score: 10,
        gameSessionId: 'test_session'
      });
      break;
    default:
      return { success: false, error: 'Unknown event type' };
  }

  return processRuntimeEvent(event, {
    gameSessionId: 'test_session',
    userId: 'test_user',
    engineId: 'test_engine'
  });
}

// Listen to consequence compiler events
consequenceEvents.on('jobs_generated', (data) => {
  pipelineEvents.emit('jobs_generated', data);
});

consequenceEvents.on('job_status_updated', (data) => {
  pipelineEvents.emit('job_status_updated', data);
});

// Log pipeline events
pipelineEvents.on('event_processed', (data) => {
  console.log(`[PIPELINE EVENT] ${data.event.event_type} processed, ${data.result.jobs_dispatched} jobs dispatched`);
});

module.exports = {
  processRuntimeEvent,
  setupRuntimeEventHandler,
  getPipelineStatistics,
  resetStatistics,
  getHealthStatus,
  simulatePipelineFlow,
  getSafetyViolations: getViolations,
  pipelineEvents
};
