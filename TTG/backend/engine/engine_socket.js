const fs = require("fs");
const path = require("path");

const {
  verifyEngineJWT,
  verifyEngineSignature,
  verifyAndConsumeNonce
} = require("./engine_auth");

const { recordTelemetry } = require("./engine_telemetry");
const { prepareEngineJob } = require("./engine_adapter");
const { jobDispatcher, updateJobStatus, findJobById, addJob } = require("../jobQueue");
const { engineMonitor } = require("./engine_monitor");
const sep          = require("../state/stateEventProcessor");
const guard        = require("../state/stateIntegrityGuard");
const compiler     = require("../consequence/consequenceCompiler");
const bucketWriter = require("../state/stateBucketWriter");
const gsm          = require("../state/gameStateManager");
const { run: simRun }             = require('../simulation/engine/SimEngine');
const { adapt: adaptToSumScript } = require('../simulation/contractAdapter');
const simResultStore              = require('../simulation/simResultStore');
const nicaiFormatter              = require('../simulation/nicaiFormatter');
const samruddhiFormatter          = require('../simulation/samruddhiFormatter');
const { validateEvent, buildEvent } = require('../routes/executionInterface');

const LOG_PATH = path.join(__dirname, "engine_event_log.json");
const LOG_CLEANUP_INTERVAL = 60 * 60 * 1000; // 1 hour
const LOG_MAX_AGE = 24 * 60 * 60 * 1000; // 24 hours
const MAX_LOG_ENTRIES = 5000; // Max entries before cleanup

// Auto-cleanup engine event log
setInterval(() => {
  cleanupEngineEventLog();
}, LOG_CLEANUP_INTERVAL);

function cleanupEngineEventLog() {
  if (!fs.existsSync(LOG_PATH)) return;
  
  try {
    const lines = fs.readFileSync(LOG_PATH, "utf-8").split("\n").filter(Boolean);
    const events = lines.map(line => JSON.parse(line));
    
    const now = Date.now();
    const recentEvents = events.filter(event => 
      (now - event.ts) < LOG_MAX_AGE
    ).slice(-MAX_LOG_ENTRIES); // Keep only recent entries, max limit
    
    if (recentEvents.length < events.length) {
      const newContent = recentEvents.map(event => JSON.stringify(event)).join("\n") + "\n";
      fs.writeFileSync(LOG_PATH, newContent);
      console.log(`[ENGINE LOG] Cleaned up ${events.length - recentEvents.length} old entries`);
    }
  } catch (err) {
    console.error("[ENGINE LOG] Cleanup failed:", err.message);
  }
}

function log(event) {
  fs.appendFileSync(
    LOG_PATH,
    JSON.stringify({ ...event, ts: Date.now() }) + "\n"
  );
}

function verifyEngineMessage(data, socket, eventType) {
  try {
    verifyEngineSignature(data);
    verifyAndConsumeNonce(data.nonce);
    return true;
  } catch (err) {
    console.error(`[ENGINE ${eventType} REJECTED]`, err.message);
    log({
      type: `ENGINE_${eventType}_REJECTED`,
      reason: err.message,
      engineId: socket.engineId
    });
    socket.emit(`${eventType.toLowerCase()}_rejected`, { reason: err.message });
    return false;
  }
}

function setupEngineSocket(io, jobQueue) {
  const engineNS = io.of("/engine");

  // Broadcast engine status to all clients
  engineMonitor.on('status_change', (status) => {
    io.emit('engine_status', status);
  });

  engineMonitor.on('telemetry', (telemetry) => {
    io.emit('engine_telemetry', telemetry);
  });

  engineNS.on("connection", (socket) => {
    try {
      verifyEngineJWT(socket);
    } catch (err) {
      console.error("[ENGINE AUTH FAILED]", err.message);
      return socket.disconnect(true);
    }
  
    console.log("[ENGINE CONNECTED]", socket.id, socket.engineId);
    log({
      type: "ENGINE_CONNECTED",
      socketId: socket.id,
      engineId: socket.engineId
    });

    jobQueue.setEngineConnected(true);
    engineMonitor.setConnected(true);

    let lastHeartbeat = Date.now();

    // Listen for jobs from queue
    const dispatchHandler = ({ job, gameplayContract }) => {
      try {
        // Send gameplay contract to engine in new format
        const engineJob = {
          job_id: job.jobId,
          job_type: job.jobType,
          gameplay_contract: gameplayContract,
          payload: job.payload || {},
          execution_params: {
            priority: "normal",
            timeout_ms: 300000
          },
          submitted_at: Date.now(),
          user_id: job.userId || "system"
        };
        
        console.log(`[BACKEND DISPATCH] ${JSON.stringify(engineJob, null, 2)}`);
        
        socket.emit("job:dispatch", engineJob);
        
        console.log(`[ENGINE] Dispatched job ${job.jobId} (${job.jobType})`);
        log({ type: "JOB_DISPATCHED_TO_ENGINE", jobId: job.jobId, jobType: job.jobType });
      } catch (err) {
        console.error(`[ENGINE] Failed to dispatch job ${job.jobId}: ${err.message}`);
        updateJobStatus(job.jobId, "failed", { 
          error: `DISPATCH_FAILED: ${err.message}`,
          failedAt: Date.now()
        });
      }
    };

    jobDispatcher.on('dispatch_to_engine', dispatchHandler);

    // Heartbeat handler
    socket.on("engine_heartbeat", () => {
      lastHeartbeat = Date.now();
      engineMonitor.recordHeartbeat();
      socket.emit("heartbeat_ack", { ts: Date.now() });
      log({ type: "ENGINE_HEARTBEAT", engineId: socket.engineId });
    });

    // Heartbeat watchdog
    const heartbeatInterval = setInterval(() => {
      if (Date.now() - lastHeartbeat > 10000) {
        console.warn("[ENGINE HEARTBEAT LOST]", socket.engineId);
        log({
          type: "ENGINE_HEARTBEAT_TIMEOUT",
          engineId: socket.engineId
        });
        jobQueue.setEngineConnected(false);
        socket.disconnect(true);
      }
    }, 5000);

    // Engine ready
    socket.on("engine_ready", () => {
      console.log("[ENGINE READY]", socket.engineId);
      log({ type: "ENGINE_READY", engineId: socket.engineId });
      
      socket.emit("ready_ack", { 
        status: "acknowledged",
        ts: Date.now() 
      });
    });

    // Job acknowledgement from engine
    socket.on("job_ack", (data) => {
      if (!verifyEngineMessage(data, socket, 'JOB_ACK')) return;
      
      const { jobId, status } = data.payload;
      console.log(`[ENGINE ACK] Job ${jobId}: ${status}`);
      
      log({
        type: "JOB_ACK",
        jobId,
        status,
        engineId: socket.engineId
      });

      socket.emit("ack_received", { jobId, ts: Date.now() });
    });



    // Job status update from engine
    socket.on("job_status", (data) => {
      try {
        verifyEngineSignature(data);
        verifyAndConsumeNonce(data.nonce);
      } catch (err) {
        console.error("[ENGINE PACKET REJECTED]", err.message);
        log({
          type: "ENGINE_PACKET_REJECTED",
          reason: err.message,
          engineId: socket.engineId
        });
        socket.emit("status_rejected", { reason: err.message });
        return;
      }
    
      const { jobId, jobType, status, error } = data.payload;

      console.log(`[ENGINE STATUS] Job ${jobId}: ${status}`);

      log({
        type: "ENGINE_JOB_STATUS",
        jobId,
        status,
        error,
        engineId: socket.engineId
      });

      // Send acknowledgement
      socket.emit("status_ack", { 
        jobId, 
        received: true,
        ts: Date.now() 
      });

      // Record telemetry
      if (status === "completed") {
        recordTelemetry({
          event: "JOB_COMPLETED",
          jobId,
          engineId: socket.engineId,
          payload: { jobType }
        });

        if (jobType === "BUILD_SCENE") {
          recordTelemetry({
            event: "SCENE_LOADED",
            jobId,
            engineId: socket.engineId,
            payload: {}
          });
        } else if (jobType === "SPAWN_ENTITY") {
          recordTelemetry({
            event: "ENTITY_SPAWNED",
            jobId,
            engineId: socket.engineId,
            payload: {}
          });
        }
      } else if (status === "failed") {
        recordTelemetry({
          event: "JOB_FAILED",
          jobId,
          engineId: socket.engineId,
          payload: { jobType, error }
        });
      }
    });

    // Engine error reporting
    socket.on("engine_error", (data) => {
      if (!verifyEngineMessage(data, socket, 'ENGINE_ERROR')) return;
      
      console.error("[ENGINE ERROR]", data.payload);
      log({
        type: "ENGINE_ERROR",
        error: data.payload.error,
        details: data.payload.details,
        engineId: socket.engineId
      });

      socket.emit("error_ack", { received: true, ts: Date.now() });
    });

    // Inbound telemetry: job_started
    socket.on("job_started", (data) => {
      if (!verifyEngineMessage(data, socket, 'JOB_STARTED')) return;
      
      if (!engineMonitor.recordTelemetry({ event: 'JOB_STARTED', ...data.payload })) {
        console.warn('[ENGINE] Malformed job_started telemetry');
        return;
      }

      const { job_id, timestamp } = data.payload;
      console.log(`[ENGINE TELEMETRY] Job started: ${job_id}`);

      updateJobStatus(job_id, "running", {
        startedAt: timestamp || Date.now()
      });

      recordTelemetry({
        event: "JOB_STARTED",
        jobId: job_id,
        engineId: socket.engineId,
        payload: {}
      });

      log({ type: "JOB_STARTED", jobId: job_id });
    });

    // Inbound telemetry: job_progress
    socket.on("job_progress", (data) => {
      if (!verifyEngineMessage(data, socket, 'JOB_PROGRESS')) return;
      
      if (!engineMonitor.recordTelemetry({ event: 'JOB_PROGRESS', ...data.payload })) {
        console.warn('[ENGINE] Malformed job_progress telemetry');
        return;
      }

      const { job_id, progress, timestamp } = data.payload;
      console.log(`[ENGINE TELEMETRY] Job ${job_id}: ${progress}%`);

      recordTelemetry({
        event: "JOB_PROGRESS",
        jobId: job_id,
        engineId: socket.engineId,
        payload: { progress }
      });

      log({ type: "JOB_PROGRESS", jobId: job_id, progress });
    });

    // Inbound telemetry: job_completed
    socket.on("job_completed", (data) => {
      if (!verifyEngineMessage(data, socket, 'JOB_COMPLETED')) return;
      
      if (!engineMonitor.recordTelemetry({ event: 'JOB_COMPLETED', ...data.payload })) {
        console.warn('[ENGINE] Malformed job_completed telemetry');
        return;
      }

      const { job_id, result, timestamp } = data.payload;
      console.log(`[ENGINE TELEMETRY] Job completed: ${job_id}`);

      const job = findJobById(job_id);
      const startedAt = job?.startedAt || Date.now();
      const completedAt = timestamp || Date.now();

      updateJobStatus(job_id, "completed", {
        completedAt,
        duration: completedAt - startedAt
      });

      recordTelemetry({
        event: "JOB_COMPLETED",
        jobId: job_id,
        engineId: socket.engineId,
        payload: result || {}
      });

      log({ type: "JOB_COMPLETED", jobId: job_id });
    });

    // Game telemetry (fps, score, game_over)
    // Phase 4: enrich with trace fields if missing
    socket.on("telemetry", (data) => {
      const enriched = {
        ...data,
        trace_id:     data.trace_id     || socket._lastTraceId     || null,
        execution_id: data.execution_id || socket._lastExecutionId || null,
        event_type:   'telemetry',
        timestamp:    data.timestamp    || Date.now()
      };
      io.emit('telemetry', enriched);
      console.log(`[TELEMETRY] FPS: ${data.fps}, Score: ${data.score}, Lives: ${data.lives}`);
      recordTelemetry({ event: "GAME_TELEMETRY", engineId: socket.engineId, payload: enriched });
    });

    // Game started event — trigger SimEngine with the gameplay contract
    socket.on("game:started", (data) => {
      io.emit('game:started', data);
      console.log(`[GAME] Started: ${data.game_mode} | has_contract=${!!data.gameplay_contract}`);

      // Phase 4: store trace context on socket for subsequent events
      socket._lastTraceId     = data.trace_id     || null;
      socket._lastExecutionId = data.execution_id || null;

      const sid = data.sessionId || data.game_session_id;
      if (sid && gsm.hasSession(sid)) gsm.setRunning(sid);

      const contract = data.gameplay_contract || data.contract || null;
      if (!contract) {
        console.warn('[SIM] No gameplay_contract in game:started — SimEngine skipped');
        return;
      }

      try {
        console.log(`[SIM] Running SimEngine | mode=${data.game_mode} | speed=${contract.movement?.speed} | obstacles=${contract.spawn_rules?.obstacles}`);

        const adaptResult = adaptToSumScript({
          trace_id:     data.trace_id     || `trace_game_${Date.now()}`,
          execution_id: data.execution_id || `exec_game_${Date.now()}`,
          game_mode:    contract.game_mode    || data.game_mode || 'runner',
          entities:     _buildEntitiesFromContract(contract),
          physics: {
            gravity:         [0, contract.physics?.gravity ?? -9.8, 0],
            friction:        contract.physics?.friction        ?? 0.1,
            bounce:          contract.physics?.bounce          ?? 0.0,
            air_resistance:  contract.physics?.air_resistance  ?? 0.05,
            collision_force: contract.physics?.collision_force ?? 1.0
          },
          movement:      { speed: contract.movement?.speed || 3 },
          spawn_rules:   contract.spawn_rules   || { obstacles: 0, frequency: 1 },
          scoring:       { rules: contract.score_rules || { distance: 1, collectibles: 0 }, end_conditions: contract.end_conditions || ['collision'] },
          player_params: contract.player_params || { health: 3, jetpack: false }
        });

        if (!adaptResult.valid) {
          console.warn(`[SIM] Adapter failed: ${adaptResult.errors.join(', ')}`);
          return;
        }

        const frequency = contract.spawn_rules?.frequency || 2;
        const ticks     = Math.max(15, Math.floor(40 / frequency));
        const simResult = simRun(adaptResult.sumscript, { ticks });

        if (simResult.success) {
          simResultStore.save(simResult.trace_id, simResult, adaptResult.sumscript);
          const nicai     = nicaiFormatter.format(simResult);
          const samruddhi = samruddhiFormatter.format(simResult);
          console.log(`[SIM] SimEngine completed | ticks=${simResult.ticks_run} | entities=${Object.keys(simResult.entities).length} | events=${simResult.event_count}`);
          io.emit('sim_result', {
            trace_id:     simResult.trace_id,
            execution_id: simResult.execution_id,
            game_mode:    data.game_mode,
            simResult,
            nicai,
            samruddhi,
            from_prompt:  data.from_prompt || null
          });
        } else {
          console.warn(`[SIM] SimEngine failed: ${simResult.error}`);
        }
      } catch (err) {
        console.error(`[SIM] SimEngine error: ${err.message}`);
      }
    });

    // Game ended event — write final bucket artifacts
    socket.on("game:ended", (data) => {
      io.emit('game:ended', data);
      console.log(`[GAME] Ended: ${data.reason}, Score: ${data.final_score}`);

      const sid = data.sessionId || data.game_session_id;
      if (sid && gsm.hasSession(sid)) {
        bucketWriter.writeStateSnapshot(sid)
          .catch(err => console.warn(`[ENGINE_SOCKET] Final snapshot failed: ${err.message}`));
      }
    });

    // Runtime event bridge — engine sends gameplay events, we update state + fire consequence jobs
    socket.on("runtime_event", (data) => {
      const { sessionId, event } = data || {};
      if (!sessionId || !event) return;

      const currentState = gsm.getCurrentState(sessionId);
      if (!currentState) {
        console.warn(`[ENGINE_SOCKET] runtime_event for unknown session: ${sessionId}`);
        return;
      }

      // Integrity guard pre-check
      const guardCheck = guard.validateEvent(event, currentState);
      if (!guardCheck.valid) {
        console.warn(`[ENGINE_SOCKET] Event blocked by guard: ${guardCheck.violations.join(', ')}`);
        return socket.emit('event_rejected', { reason: guardCheck.violations });
      }

      // Apply event to state
      const sepResult = sep.processEvent(sessionId, event);
      if (!sepResult.success) {
        console.warn(`[ENGINE_SOCKET] SEP failed: ${sepResult.error}`);
        return;
      }

      // Append to event trace (non-fatal)
      bucketWriter.appendEventTrace(sessionId, sepResult.event || event, sepResult.changes)
        .catch(() => {});

      // Consequence jobs — state-aware
      const compResult = compiler.processEventWithState(event, { sessionId });
      if (compResult.success && compResult.jobs.length > 0) {
        compResult.jobs.forEach(job => {
          addJob(job, (updatedJob, status, error) => {
            io.emit('job_status', {
              jobId: updatedJob.jobId,
              jobType: updatedJob.jobType,
              status,
              priority: updatedJob.priority || 'medium',
              submittedAt: updatedJob.queuedAt,
              executionId: updatedJob.executionId,
              error: error || null
            });
          }, null);
        });
      }

      // Broadcast updated state to all dashboard clients
      io.emit('game_state_update', {
        sessionId,
        state:      sepResult.state,
        changes:    sepResult.changes,
        event_type: event.event_type
      });
    });

    // Inbound telemetry: job_failed
    socket.on("job_failed", (data) => {
      if (!verifyEngineMessage(data, socket, 'JOB_FAILED')) return;
      
      if (!engineMonitor.recordTelemetry({ event: 'JOB_FAILED', ...data.payload })) {
        console.warn('[ENGINE] Malformed job_failed telemetry');
        return;
      }

      const { job_id, error, details, timestamp } = data.payload;
      console.error(`[ENGINE TELEMETRY] Job failed: ${job_id} - ${error}`);

      updateJobStatus(job_id, "failed", {
        error: `${error}: ${details || ''}`,
        failedAt: timestamp || Date.now()
      });

      recordTelemetry({
        event: "JOB_FAILED",
        jobId: job_id,
        engineId: socket.engineId,
        payload: { error, details }
      });

      log({ type: "JOB_FAILED", jobId: job_id, error });
    });

    socket.on("disconnect", () => {
      clearInterval(heartbeatInterval);
      jobDispatcher.removeListener('dispatch_to_engine', dispatchHandler);
      console.log("[ENGINE DISCONNECTED]", socket.engineId);
      log({
        type: "ENGINE_DISCONNECTED",
        socketId: socket.id,
        engineId: socket.engineId
      });
      jobQueue.setEngineConnected(false);
      engineMonitor.handleDisconnect();
    });
  });

  return engineNS;
}

// Build entities from gameplay contract for SimEngine
function _buildEntitiesFromContract(contract) {
  const entities      = [];
  const speed         = contract.movement?.speed    || 3;
  const health        = contract.player_params?.health || 3;
  const gameMode      = contract.game_mode          || 'runner';
  const obstacleCount = Math.min(contract.spawn_rules?.obstacles || 0, 5);
  const frequency     = contract.spawn_rules?.frequency || 1;
  const goalDist      = 40 + speed * 10;
  const spread        = gameMode === 'arena' || gameMode === 'open_scene' ? 20 : 12;
  const baseGap       = Math.max(8, Math.floor(goalDist / (obstacleCount + 1)));

  entities.push({
    id: 'PLAYER', type: 'vessel',
    transform: { position: [0, 0, 0], rotation: [0, 0, 0], scale: [1, 1, 1] },
    meta: { speed, health, game_mode: gameMode }
  });

  for (let i = 0; i < obstacleCount; i++) {
    const zOffset = (i % 3 === 0 ? 0 : i % 3 === 1 ? spread : -spread);
    entities.push({
      id: `OBSTACLE_${i + 1}`, type: 'obstacle',
      transform: { position: [baseGap * (i + 1), 0, zOffset], rotation: [0, 0, 0], scale: [1, 1, 1] }
    });
  }

  if (gameMode === 'arena' || gameMode === 'open_scene') {
    const enemyCount = Math.min(Math.floor(health), 3);
    for (let i = 0; i < enemyCount; i++) {
      entities.push({
        id: `ENEMY_${i + 1}`, type: 'agent',
        transform: { position: [goalDist * 0.5 + i * 15, 0, i % 2 === 0 ? 15 : -15], rotation: [0, 0, 0], scale: [1, 1, 1] },
        meta: { target_id: 'PLAYER' }
      });
    }
  }

  entities.push({
    id: 'ZONE_GOAL', type: 'zone',
    transform: { position: [goalDist, 0, 0], rotation: [0, 0, 0], scale: [1, 1, 1] },
    meta: { radius: 10 + frequency * 2 }
  });

  return entities;
}

module.exports = { setupEngineSocket };
