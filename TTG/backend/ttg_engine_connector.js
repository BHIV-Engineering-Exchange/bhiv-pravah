/**
 * ttg_engine_connector.js
 *
 * DROP THIS FILE into Atharva's TTG engine repo.
 *
 * This connects Atharva's engine to Rudra's backend as a Socket.IO client
 * on the /engine namespace. The backend sends jobs; this file receives them,
 * runs the game, and sends back status/telemetry.
 *
 * Setup (in Atharva's repo):
 *   npm install socket.io-client jsonwebtoken
 *
 * Run:
 *   RUDRA_URL=http://<rudra-ip>:3000 node ttg_engine_connector.js
 *
 * Or set defaults below and just run:
 *   node ttg_engine_connector.js
 */

const { io }   = require('socket.io-client');
const jwt      = require('jsonwebtoken');
const crypto   = require('crypto');

// ── Config — update RUDRA_URL to Rudra's machine IP ─────────────────────────
const RUDRA_URL           = process.env.RUDRA_URL            || 'http://localhost:3000';
const JWT_SECRET          = process.env.JWT_SECRET           || 'JWT_SECRET_123456789';
const ENGINE_SHARED_SECRET = process.env.ENGINE_SHARED_SECRET || 'ENGINE_SHARED_SECRET_123';
const ENGINE_ID           = process.env.ENGINE_ID            || 'atharva_ttg_engine_01';

// ── Generate auth token ──────────────────────────────────────────────────────
const token = jwt.sign(
  { engineId: ENGINE_ID, role: 'engine' },
  JWT_SECRET,
  { expiresIn: '24h' }
);

// ── HMAC signer — required by Rudra's backend for all outbound messages ──────
function sign(payload) {
  const nonce = crypto.randomBytes(16).toString('hex');
  const ts    = Date.now();
  const sig   = crypto
    .createHmac('sha256', ENGINE_SHARED_SECRET)
    .update(JSON.stringify(payload) + nonce + ts)
    .digest('hex');
  return { payload, nonce, ts, sig };
}

// ── Connect ──────────────────────────────────────────────────────────────────
console.log(`[TTG ENGINE] Connecting to Rudra's backend: ${RUDRA_URL}/engine`);

const socket = io(`${RUDRA_URL}/engine`, {
  auth: { token },
  reconnection: true,
  reconnectionDelay: 3000
});

socket.on('connect', () => {
  console.log(`[TTG ENGINE] ✅ Connected — socket.id=${socket.id}`);
  socket.emit('engine_ready');
  // Heartbeat every 3s to stay alive
  setInterval(() => socket.emit('engine_heartbeat'), 3000);
});

socket.on('ready_ack',     () => console.log('[TTG ENGINE] Ready acknowledged'));
socket.on('heartbeat_ack', () => {});  // silent

// ── Receive jobs from Rudra's backend ────────────────────────────────────────
socket.on('job:dispatch', (job) => {
  const jobId    = job.job_id   || job.jobId;
  const jobType  = job.job_type || job.jobType;
  const contract = job.gameplay_contract || {};

  if (!jobId || !jobType) {
    console.error('[TTG ENGINE] ❌ Rejected job — missing job_id or job_type');
    return;
  }

  console.log(`\n[TTG ENGINE] 📦 Job received: ${jobId} (${jobType})`);
  console.log(`[TTG ENGINE]    game_mode : ${contract.game_mode || 'runner'}`);
  console.log(`[TTG ENGINE]    speed     : ${contract.movement?.speed || 5}`);
  console.log(`[TTG ENGINE]    blueprint :`, contract.blueprint?.blueprint?.payload?.title || 'none');

  // Ack receipt
  socket.emit('job_ack', sign({ jobId, status: 'received' }));

  // ── Hand off to Atharva's actual engine logic ──────────────────────────────
  // Replace the function below with your real engine call.
  // The contract contains everything needed to launch the game:
  //   contract.game_mode        — "runner" | "sidescroller" | "arena"
  //   contract.movement.speed   — player speed
  //   contract.physics          — gravity, friction, bounce etc.
  //   contract.spawn_rules      — obstacles, frequency
  //   contract.player_params    — health, jetpack
  //   contract.blueprint        — full Prompt Runner blueprint (title, outline, tasks)
  //   contract.data.original_prompt — the original user text prompt

  runGame(jobId, jobType, contract);
});

// ── Engine execution — REPLACE this with Atharva's real engine calls ─────────
function runGame(jobId, jobType, contract) {
  const gameMode = contract.game_mode || 'runner';
  const speed    = contract.movement?.speed || 5;

  // Signal job started
  setTimeout(() => {
    socket.emit('job_started', sign({ job_id: jobId, timestamp: Date.now() }));
    console.log(`[TTG ENGINE] ⚙️  Started: ${jobId}`);
  }, 200);

  // ── INSERT ATHARVA'S ENGINE LAUNCH CODE HERE ─────────────────────────────
  // Example:
  //   atharvaEngine.launch({ gameMode, speed, contract });
  //   atharvaEngine.on('progress', (pct) => reportProgress(jobId, pct));
  //   atharvaEngine.on('done', () => reportCompleted(jobId, contract));
  // ─────────────────────────────────────────────────────────────────────────

  // Signal job completed (remove this once real engine hooks are in place)
  setTimeout(() => {
    socket.emit('job_completed', sign({
      job_id: jobId,
      result: { success: true, game_mode: gameMode },
      timestamp: Date.now()
    }));
    console.log(`[TTG ENGINE] ✅ Completed: ${jobId}`);

    // START_LOOP = game is now running — start sending telemetry
    if (jobType === 'START_LOOP') {
      startTelemetry(contract);
    }
  }, 1000);
}

// ── Send telemetry back to Rudra's dashboard ─────────────────────────────────
function startTelemetry(contract) {
  const gameMode = contract.game_mode || 'runner';
  let score = 0, lives = contract.player_params?.health || 3, duration = 0;

  socket.emit('game:started', {
    game_mode:         gameMode,
    gameplay_contract: contract,
    trace_id:          contract.trace_id     || null,
    execution_id:      contract.execution_id || null
  });

  console.log(`\n[TTG ENGINE] 🎮 GAME STARTED — mode=${gameMode}\n`);

  const tick = setInterval(() => {
    duration++;
    score += 10;

    // ── REPLACE with real game state from Atharva's engine ────────────────
    socket.emit('telemetry', {
      trace_id:     contract.trace_id     || null,
      execution_id: contract.execution_id || null,
      event_type:   'telemetry',
      timestamp:    Date.now(),
      fps: 60, score, lives, duration, game_mode: gameMode
    });

    console.log(`[TTG ENGINE] ⏱️  ${duration}s | Score: ${score} | Lives: ${lives}`);

    if (duration >= 30 || lives <= 0) {
      clearInterval(tick);
      const reason = lives <= 0 ? 'player_death' : 'time_up';
      socket.emit('game:ended', {
        trace_id:     contract.trace_id     || null,
        execution_id: contract.execution_id || null,
        event_type:   'game_ended',
        timestamp:    Date.now(),
        reason, final_score: score, duration, game_mode: gameMode
      });
      console.log(`[TTG ENGINE] 🏁 GAME OVER — ${reason} | Score: ${score}`);
    }
  }, 1000);
}

socket.on('disconnect',    () => console.log('[TTG ENGINE] ❌ Disconnected — will reconnect...'));
socket.on('connect_error', (e) => console.error('[TTG ENGINE] ❌ Connect error:', e.message));
