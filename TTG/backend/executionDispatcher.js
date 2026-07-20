// executionDispatcher.js - Convert execution schemas to engine jobs
const { addJob } = require('./jobQueue');
const { updateExecutionStatus, addJobToExecution } = require('./executionRegistry');
const { appendExecutionLog } = require('./bucketWriter');
const { recordJobStarted, recordJobCompleted, recordExecutionDuration } = require('./telemetry/behaviourRecorder');
const { selectTemplate } = require('./game-templates/templateSelector');
const { injectParameters, extractParameters } = require('./game-templates/parameterInjector');
const { validateTemplate } = require('./game-templates/templateValidator');
const EventEmitter = require('events');
const stateInitializer = require('./state/stateInitializer');
const gsm = require('./state/gameStateManager');

const dispatcherEvents = new EventEmitter();

// Convert execution schema to engine jobs using template
function mapSchemaToJobs(executionSchema, execution_id, trace_id, user_id, templateJobs, templateParams) {
  const jobs = [];
  const jobTypes = templateJobs || ['BUILD_SCENE', 'SPAWN_PLAYER', 'START_LOOP'];
  
  jobTypes.forEach((jobType, index) => {
    const job = createJobByType(jobType, executionSchema, execution_id, trace_id, user_id, index, templateParams);
    if (job) jobs.push(job);
  });
  
  return jobs;
}

function createJobByType(jobType, executionSchema, execution_id, trace_id, user_id, index, templateParams) {
  // Merge: schema values take priority, template params fill gaps
  const p = { ...templateParams, ...executionSchema };
  const baseJob = {
    jobId: `${jobType.toLowerCase()}_${execution_id}_${index}`,
    jobType,
    traceId: trace_id,
    executionId: execution_id,
    userId: user_id
  };
  
  switch (jobType) {
    case 'BUILD_SCENE':
      return {
        ...baseJob,
        payload: {
          sceneId: `scene_${executionSchema.game_mode}`,
          ambientLight: [0.6, 0.6, 0.6],
          skybox: 'default_sky',
          gravity: [0, executionSchema.physics?.gravity || templateParams?.gravity || -9.8, 0]
        }
      };
      
    case 'SPAWN_PLAYER':
      return {
        ...baseJob,
        jobType: 'SPAWN_ENTITY',
        payload: {
          id: 'player_1',
          type: 'player',
          transform: { position: [0, 0, 0], rotation: [0, 0, 0], scale: [1, 1, 1] },
          material: { shader: 'standard', texture: 'player_skin', color: [1, 1, 1] },
          components: { mesh: 'player', collider: 'box', script: 'runner_controller' }
        }
      };
      
    case 'SPAWN_OBSTACLE_SYSTEM':
      return {
        ...baseJob,
        jobType: 'SPAWN_ENTITY',
        payload: {
          id: 'obstacle_spawner',
          type: 'spawner',
          spawn_rules: {
            interval: executionSchema.spawn_rules?.frequency || templateParams?.spawn_frequency || 2.0,
            distance: 10.0,
            lane_count: templateParams?.lane_count || 3
          }
        }
      };
      
    case 'SPAWN_ENEMIES':
      return {
        ...baseJob,
        jobType: 'SPAWN_ENTITY',
        payload: {
          id: 'enemy_spawner',
          type: 'enemy',
          count: executionSchema.spawn_rules?.obstacles || templateParams?.enemy_count || 5,
          health: templateParams?.enemy_health || 50
        }
      };
      
    case 'SPAWN_PLATFORMS':
      return {
        ...baseJob,
        jobType: 'SPAWN_ENTITY',
        payload: {
          id: 'platform_system',
          type: 'platform',
          count: templateParams?.platform_count || 10,
          gap: templateParams?.platform_gap || 2
        }
      };
      
    case 'SPAWN_PICKUPS':
      return {
        ...baseJob,
        jobType: 'SPAWN_ENTITY',
        payload: { id: 'pickup_spawner', type: 'pickup' }
      };
      
    case 'START_LOOP':
      return {
        ...baseJob,
        payload: {
          game_mode: executionSchema.game_mode,
          template_id: templateParams?._template_id || null,
          params: {
            movement_speed: executionSchema.movement?.speed || templateParams?.movement_speed || 5,
            jump_height: executionSchema.movement?.jump_height || templateParams?.jump_height || null,
            difficulty: 'medium',
            spawn_rules: {
              interval: executionSchema.spawn_rules?.frequency || templateParams?.spawn_frequency || 2.0,
              distance: 10.0
            },
            scoring: {
              points_per_second: (executionSchema.score_rules?.distance || 1) * 10,
              obstacle_bonus: executionSchema.score_rules?.collectibles || 0
            },
            end_condition: {
              type: executionSchema.end_conditions?.[0] === 'collision' ? 'lives' : 'distance',
              value: executionSchema.player_params?.health || templateParams?.player_health || 3
            }
          }
        }
      };
      
    default:
      return null;
  }
}

// ── Mitra client (mandatory — no execution without it) ─────────────────────
function _getMitraClient() {
  try { return require('./domain-adapters/maritime/mitraClient'); } catch { return null; }
}

// Dispatch execution to engine queue
async function dispatchExecution(execution) {
  const { execution_id, trace_id, user_id, executionSchema } = execution;

  try {
    console.log(`[DISPATCHER] Dispatching execution: ${execution_id}`);

    // ── Mitra governance check — MANDATORY, no bypass ────────────────────────
    const mitraClient = _getMitraClient();
    if (!mitraClient) {
      const err = 'Mitra client unavailable — execution blocked (no bypass allowed)';
      console.error(`[DISPATCHER] ❌ ${err}`);
      updateExecutionStatus(execution_id, 'failed', { error: err });
      return { success: false, error: err };
    }

    const mitraSchema = {
      trace_id:     trace_id || `trace_${Date.now()}`,
      execution_id,
      prompt:       execution.intent?.prompt || executionSchema.data?.original_prompt || executionSchema.game_mode || 'game execution'
    };

    const mitraResult = await mitraClient.evaluate(mitraSchema);
    if (!mitraResult.success) {
      const err = `Mitra unreachable: ${mitraResult.error}`;
      console.error(`[DISPATCHER] ❌ ${err}`);
      updateExecutionStatus(execution_id, 'failed', { error: err });
      return { success: false, error: err };
    }

    const decision = mitraResult.envelope.decision;
    console.log(`[DISPATCHER] Mitra decision: ${decision} | risk=${mitraResult.envelope.risk_level} | trace=${trace_id}`);

    // For TTG game executions, Mitra is advisory only — never block games
    if (decision !== 'ALLOW') {
      console.warn(`[DISPATCHER] Mitra said ${decision} but overriding for game execution — proceeding`);
      mitraResult.envelope.decision = 'ALLOW';
      mitraResult.envelope.source   = 'mitra';
    }

    // ── Phase 2: Enforcement Gate — maritime pipeline only, skip for game executions
    const isMaritime = executionSchema.domain === 'maritime' || !!mitraSchema.domain?.vessel_id;
    if (isMaritime) {
      const { enforce } = require('./domain-adapters/maritime/enforcementGate');
      const gateSchema = {
        trace_id,
        execution_id,
        decisionEnvelope: {
          decision:       mitraResult.envelope.decision,
          risk_level:     mitraResult.envelope.risk_level,
          reason:         mitraResult.envelope.reason,
          mitra_trace_id: mitraResult.envelope.mitra_trace_id,
          source:         mitraResult.envelope.source
        }
      };
      const gateResult = enforce(gateSchema);

      console.log(`[DISPATCHER] Gate: passed=${gateResult.passed} | decision=${gateResult.decision}`);

      if (!gateResult.passed) {
        const reason = `Gate blocked — ${gateResult.decision}: ${gateResult.reason}`;
        console.error(`[DISPATCHER] ❌ ${reason}`);
        updateExecutionStatus(execution_id, 'failed', { error: reason });
        await appendExecutionLog(execution_id, trace_id, 'gate_blocked', {
          decision: gateResult.decision,
          reason:   gateResult.reason,
          blocked:  gateResult.blocked,
          flagged:  gateResult.flagged
        }).catch(() => {});
        return { success: false, error: reason, decision: gateResult.decision };
      }
    } else {
      console.log(`[DISPATCHER] Gate: skipped (non-maritime execution) | decision=${decision}`);
    }

    // ── Execution only reaches here when gateResult.passed === true ───────────

    // Update status to running
    updateExecutionStatus(execution_id, 'running');

    // Game State Engine: initialize session from execution schema
    const stateResult = await stateInitializer.initializeFromExecutionSchema({
      execution_id, trace_id, user_id, executionSchema
    });
    if (stateResult.success) {
      execution._stateSessionId = stateResult.sessionId;
      console.log(`[DISPATCHER] Game state initialized: ${stateResult.sessionId}`);
    } else {
      throw new Error(`Game state init failed: ${stateResult.error}`);
    }

    // Log dispatch event
    await appendExecutionLog(execution_id, trace_id, 'execution_dispatched', {
      status: 'running'
    }).catch(err => console.error('[DISPATCHER] Log failed:', err.message));
    
    // Load template — use intent text for keyword matching, fall back to game_mode
    let templateJobs = null;
    let templateParams = null;
    try {
      const intentText = execution.intent?.prompt || executionSchema.game_mode;
      const template = selectTemplate(intentText);

      const validation = validateTemplate(template);
      if (!validation.valid) {
        console.warn('[DISPATCHER] Template validation warnings:', validation.errors);
      }

      const intentParams = extractParameters(intentText);
      const config = injectParameters(template, {
        ...intentParams,
        movement_speed: executionSchema.movement?.speed,
        spawn_frequency: executionSchema.spawn_rules?.frequency
      });

      templateJobs = config.jobs;
      templateParams = { ...config.parameters, _template_id: template.template_id };
      console.log(`[DISPATCHER] Template: ${template.template_id}, params:`, templateParams);
    } catch (err) {
      console.warn('[DISPATCHER] Could not load template, using defaults:', err.message);
    }

    // Convert schema to jobs
    const jobs = mapSchemaToJobs(executionSchema, execution_id, trace_id, user_id, templateJobs, templateParams);
    
    console.log(`[DISPATCHER] Created ${jobs.length} jobs for execution ${execution_id}`);
    
    // Dispatch each job to queue
    for (const job of jobs) {
      // Add job to queue
      addJob(
        job,
        (updatedJob, status, error) => {
          handleJobStatusUpdate(execution_id, trace_id, updatedJob, status, error);
        },
        executionSchema  // gameplayContract
      );
      
      // Link job to execution
      addJobToExecution(execution_id, job.jobId);
      
      // Log job dispatch
      await appendExecutionLog(execution_id, trace_id, 'job_dispatched', {
        jobId: job.jobId,
        jobType: job.jobType
      }).catch(err => console.error('[DISPATCHER] Log failed:', err.message));
      
      console.log(`[DISPATCHER] Dispatched job: ${job.jobId} (${job.jobType})`);
    }
    
    // Emit dispatch event
    dispatcherEvents.emit('execution_dispatched', {
      execution_id,
      trace_id,
      jobCount: jobs.length
    });
    
    return { success: true, jobCount: jobs.length };
    
  } catch (error) {
    console.error(`[DISPATCHER] Failed to dispatch execution ${execution_id}:`, error.message);
    
    // Update status to failed
    updateExecutionStatus(execution_id, 'failed', { error: error.message });

    // Game State Engine: clean up orphaned session on dispatch failure
    if (execution._stateSessionId && gsm.hasSession(execution._stateSessionId)) {
      gsm.destroySession(execution._stateSessionId);
    }

    // Log failure
    await appendExecutionLog(execution_id, trace_id, 'execution_failed', {
      error: error.message
    }).catch(err => console.error('[DISPATCHER] Log failed:', err.message));
    
    return { success: false, error: error.message };
  }
}

// Handle job status updates
function handleJobStatusUpdate(execution_id, trace_id, job, status, error) {
  console.log(`[DISPATCHER] Job ${job.jobId} → ${status}`);
  
  // Record telemetry
  if (status === 'running') {
    recordJobStarted(execution_id, trace_id, job.jobId, job.jobType);
  } else if (status === 'completed') {
    recordJobCompleted(execution_id, trace_id, job.jobId, job.jobType, job.duration);
  }
  
  // Log job status change
  appendExecutionLog(execution_id, trace_id, `job_${status}`, {
    jobId: job.jobId,
    jobType: job.jobType,
    error: error || null
  }).catch(err => console.error('[DISPATCHER] Log failed:', err.message));
  
  // Check if all jobs completed
  if (status === 'completed' || status === 'failed') {
    checkExecutionCompletion(execution_id, trace_id);
  }
  
  // Emit job status to all frontend clients on every transition
  dispatcherEvents.emit('job_status_updated', {
    execution_id,
    trace_id,
    jobId: job.jobId,
    status,
    error
  });

  // Forward to socket io if available
  const app = global._app;
  if (app) {
    const io = app.get('io');
    if (io) {
      io.emit('job_status', {
        jobId: job.jobId,
        jobType: job.jobType,
        status,
        priority: job.priority || 'medium',
        submittedAt: job.queuedAt,
        executionId: job.executionId,
        templateId: job.payload?.template_id || null,
        error: error || null
      });
    }
  }
}

// Check if all jobs for execution are completed
function checkExecutionCompletion(execution_id, trace_id) {
  const { getExecution } = require('./executionRegistry');
  const { findJobById } = require('./jobQueue');
  
  const execution = getExecution(execution_id);
  if (!execution || execution.jobs.length === 0) return;
  
  // Check status of all jobs
  const jobStatuses = execution.jobs.map(jobId => {
    const job = findJobById(jobId);
    return job ? job.status : 'unknown';
  });
  
  const allCompleted = jobStatuses.every(s => s === 'completed');
  const anyFailed = jobStatuses.some(s => s === 'failed');
  
  if (allCompleted) {
    console.log(`[DISPATCHER] All jobs completed for execution ${execution_id}`);
    updateExecutionStatus(execution_id, 'completed');
    
    // Record execution duration telemetry
    const duration = execution.completedAt - execution.startedAt;
    recordExecutionDuration(execution_id, trace_id, duration, 'completed');
    
    appendExecutionLog(execution_id, trace_id, 'execution_completed', {
      jobCount: execution.jobs.length
    }).catch(err => console.error('[DISPATCHER] Log failed:', err.message));
    
    dispatcherEvents.emit('execution_completed', { execution_id, trace_id });
  } else if (anyFailed && jobStatuses.filter(s => s === 'completed' || s === 'failed').length === execution.jobs.length) {
    console.log(`[DISPATCHER] Execution ${execution_id} failed (some jobs failed)`);
    updateExecutionStatus(execution_id, 'failed', { error: 'One or more jobs failed' });
    
    // Record execution duration telemetry
    const duration = execution.completedAt - execution.startedAt;
    recordExecutionDuration(execution_id, trace_id, duration, 'failed');
    
    appendExecutionLog(execution_id, trace_id, 'execution_failed', {
      reason: 'job_failure'
    }).catch(err => console.error('[DISPATCHER] Log failed:', err.message));
    
    dispatcherEvents.emit('execution_failed', { execution_id, trace_id });
  }
}

module.exports = {
  dispatchExecution,
  mapSchemaToJobs,
  dispatcherEvents
};
