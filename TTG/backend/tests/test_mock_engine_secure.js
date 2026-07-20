require('dotenv').config();
const io = require('socket.io-client');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');

const ENGINE_SHARED_SECRET = process.env.ENGINE_SHARED_SECRET || 'ENGINE_SHARED_SECRET_123';
const JWT_SECRET = process.env.JWT_SECRET || 'JWT_SECRET_123456789';

const engineToken = jwt.sign(
  { engineId: 'mock_engine_01', role: 'engine' },
  JWT_SECRET,
  { expiresIn: '1h' }
);

console.log('🚀 Mock Engine starting...\n');

const socket = io('http://localhost:3000/engine', {
  auth: { token: engineToken }
});

function signMessage(payload) {
  const nonce = crypto.randomBytes(16).toString('hex');
  const ts    = Date.now();
  const sig   = crypto
    .createHmac('sha256', ENGINE_SHARED_SECRET)
    .update(JSON.stringify(payload) + nonce + ts)
    .digest('hex');
  return { payload, nonce, ts, sig };
}

socket.on('connect', () => {
  console.log('✅ Engine connected:', socket.id);
  socket.emit('engine_ready');
  setInterval(() => socket.emit('engine_heartbeat'), 3000);
});

socket.on('ready_ack',     () => console.log('✅ Ready acknowledged'));
socket.on('heartbeat_ack', () => console.log('💓 Heartbeat ack'));
socket.on('ack_received',  (d) => console.log(`✅ Ack received: ${d.jobId}`));
socket.on('status_ack',    (d) => console.log(`✅ Status ack: ${d.jobId}`));

// ── Backend emits 'job:dispatch' with job_id / job_type ───────────────────────
// Phase 2 — Execution as Pure Consumer
// Rules:
//   ✅ Accept contract
//   ✅ Run simulation
//   ✅ Emit events
//   ❌ NO mitra_decision assumptions
//   ❌ NO internal gating logic
//   ❌ NO decision branching
//   ❌ NO modification of contract
// Execution ONLY runs because pipeline already passed gateResult.passed === true
socket.on('job:dispatch', (job) => {
  const jobId    = job.job_id   || job.jobId;
  const jobType  = job.job_type || job.jobType;
  const contract = job.gameplay_contract || {};

  // ── Contract validation — reject immediately if malformed ────────────────
  // Execution does NOT validate governance — only schema shape
  if (!jobId || !jobType) {
    console.error(`❌ [EXECUTION] Rejected job — missing job_id or job_type`);
    return;
  }
  if (jobType !== 'BUILD_SCENE' && jobType !== 'SPAWN_ENTITY' && jobType !== 'START_LOOP') {
    console.error(`❌ [EXECUTION] Rejected job — unknown job_type: ${jobType}`);
    return;
  }

  console.log(`\n📦 Job received: ${jobId} (${jobType})`);

  // Ack
  socket.emit('job_ack', signMessage({ jobId, status: 'received' }));

  // Started
  setTimeout(() => {
    socket.emit('job_started', signMessage({ job_id: jobId, timestamp: Date.now() }));
    console.log(`  ⚙️  Started: ${jobId}`);
  }, 300);

  // Progress
  setTimeout(() => {
    socket.emit('job_progress', signMessage({ job_id: jobId, progress: 50, timestamp: Date.now() }));
    console.log(`  📊 Progress 50%: ${jobId}`);
  }, 800);

  // Completed
  setTimeout(() => {
    socket.emit('job_completed', signMessage({ job_id: jobId, result: { success: true }, timestamp: Date.now() }));
    console.log(`  ✅ Completed: ${jobId}`);

    // START_LOOP → run game simulation
    if (jobType === 'START_LOOP') {
      setTimeout(() => _runGame(contract), 300);
    }
  }, 1500);
});

function _runGame(contract) {
  const gameMode    = contract.game_mode        || 'runner';
  const speed       = contract.movement?.speed  || 5;
  const obstacles   = contract.spawn_rules?.obstacles || 0;
  const frequency   = contract.spawn_rules?.frequency || 2.0;
  let   lives       = contract.player_params?.health  || 3;
  const hasJetpack  = contract.player_params?.jetpack || false;
  let   score       = 0;
  let   duration    = 0;

  // Hit probability scales with obstacles and difficulty
  // More obstacles = higher chance of getting hit per tick
  const hitChance   = Math.min(0.02 + (obstacles * 0.015), 0.15);

  // Coin chance scales with game mode
  const coinChance  = gameMode === 'open_scene' ? 0.05 : 0.1;

  // Score per tick scales with speed
  const scorePerTick = Math.floor(10 * (speed / 5));

  // Max duration scales with frequency — faster spawn = shorter game
  const maxDuration = Math.max(15, Math.floor(40 / frequency));

  socket.emit('game:started', {
    game_mode:        gameMode,
    speed,
    obstacles,
    lives,
    gameplay_contract: contract,
    trace_id:         contract.trace_id     || null,
    execution_id:     contract.execution_id || null,
    from_prompt:      contract.data?.original_prompt || null
  });
  console.log(`\n🎮 GAME STARTED — mode=${gameMode} speed=${speed} obstacles=${obstacles} lives=${lives} hitChance=${hitChance.toFixed(2)}\n`);

  const tick = setInterval(() => {
    duration++;
    score += scorePerTick;

    // Coin pickup
    if (Math.random() < coinChance) {
      score += 50;
      console.log('💎 Coin +50');
    }

    // Obstacle hit — probability driven by obstacle count + game mode
    if (Math.random() < hitChance && lives > 0) {
      // Jetpack gives 50% damage reduction
      if (!hasJetpack || Math.random() > 0.5) {
        lives--;
        console.log(`💔 Hit! Lives: ${lives}`);
      } else {
        console.log('🚀 Jetpack dodge!');
      }
    }

    // Arena mode: enemies deal extra damage at higher frequency
    if (gameMode === 'open_scene' && Math.random() < 0.03 && lives > 0) {
      lives--;
      console.log(`👾 Enemy attack! Lives: ${lives}`);
    }

    socket.emit('telemetry', {
      // Phase 4: every event must include trace_id, execution_id, event_type, timestamp, data
      trace_id:     contract.trace_id     || null,
      execution_id: contract.execution_id || null,
      event_type:   'telemetry',
      timestamp:    Date.now(),
      data: {
        fps:       57 + Math.floor(Math.random() * 4),
        score,
        lives,
        duration,
        game_mode: gameMode
      },
      // Legacy flat fields for backward compat
      fps:       57 + Math.floor(Math.random() * 4),
      score,
      lives,
      duration,
      game_mode: gameMode
    });
    console.log(`⏱️  ${duration}s | Score: ${score} | Lives: ${lives} | Mode: ${gameMode}`);

    if (lives === 0 || duration >= maxDuration) {
      clearInterval(tick);
      const reason = lives === 0 ? 'player_death' : 'time_up';
      socket.emit('game:ended', {
        // Phase 4: every event must include trace_id, execution_id, event_type, timestamp, data
        trace_id:     contract.trace_id     || null,
        execution_id: contract.execution_id || null,
        event_type:   'game_ended',
        timestamp:    Date.now(),
        data:         { reason, final_score: score, duration, game_mode: gameMode },
        // Legacy flat fields
        reason, final_score: score, duration, game_mode: gameMode
      });
      console.log(`\n🏁 GAME OVER — ${reason} | Score: ${score} | Mode: ${gameMode}\n`);
    }
  }, 1000);
}

socket.on('disconnect',    () => console.log('❌ Engine disconnected'));
socket.on('connect_error', (e) => console.error('❌ Connect error:', e.message));

console.log('Waiting for jobs...\n');
