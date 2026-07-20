'use strict';

const express          = require('express');
const router           = express.Router();
const { run }          = require('../simulation/engine/SimEngine');
const { runStream }    = require('../simulation/engine/SimEngineStream');
const store            = require('../simulation/simResultStore');
const adapter          = require('../simulation/contractAdapter');
const validator        = require('../simulation/contractValidator.v1');
const streamRegistry   = require('../simulation/streamRegistry');
const { replay: simReplay, replayStream } = require('../simulation/simReplayEngine');

// ── Request size guard ────────────────────────────────────────────────────────
// Reject payloads over 256KB — prevents memory exhaustion from oversized contracts
const MAX_BODY_BYTES = 256 * 1024;

function sizeGuard(req, res, next) {
  const len = parseInt(req.headers['content-length'] || '0', 10);
  if (len > MAX_BODY_BYTES) {
    return res.status(413).json(_err('Request body exceeds 256KB limit'));
  }
  next();
}

// ── Consistent error shape ────────────────────────────────────────────────────
function _err(error, errors) {
  const out = { status: 'failed', error };
  if (errors) out.errors = errors;
  return out;
}

// ── POST /simulate/run ────────────────────────────────────────────────────────
// Idempotent: same trace_id → same result (stored result returned, no re-run)
// Fail-closed: any contract violation → 422, no partial execution

router.post('/run', sizeGuard, (req, res) => {

  // Step 1: validate against simulationContract.v1
  const v1 = validator.validate(req.body);
  if (!v1.valid) {
    return res.status(422).json(_err('Contract v1 validation failed', v1.errors));
  }

  const { trace_id, execution_id, domain, scenario,
          entities, behaviors, rules, constraints, ticks } = req.body;

  // Step 2: idempotency — if trace_id already ran, return stored result
  const existing = store.get(trace_id);
  if (existing) {
    return res.status(200).json(existing);
  }

  // Step 3: adapt to SumScript
  const adapted = adapter.adapt({ trace_id, execution_id, domain, scenario,
                                   entities, behaviors, rules, constraints });
  if (!adapted.valid) {
    return res.status(422).json(_err(adapted.errors.join('; ')));
  }

  // Step 4: run simulation
  const result = run(adapted.sumscript, { ticks: ticks || 10 });

  // Step 5: persist for replay — only on success
  if (result.status === 'completed') {
    store.save(result.trace_id, result, adapted.sumscript);
  }

  return res.status(result.status === 'completed' ? 200 : 422).json(result);
});

// ── POST /simulate/replay/:trace_id ──────────────────────────────────────────
// Re-runs from stored contract. Validates determinism.
// Same trace_id → same seed → identical output guaranteed.

router.post('/replay/:trace_id', (req, res) => {
  const { trace_id } = req.params;

  if (!trace_id || typeof trace_id !== 'string') {
    return res.status(400).json(_err('trace_id is required'));
  }

  const result = simReplay(trace_id);
  return res.status(result.success ? 200 : 422).json(result);
});

// ── GET /simulate/result/:trace_id ────────────────────────────────────────────
// Returns simulationState.v1 directly — no wrapper

router.get('/result/:trace_id', (req, res) => {
  const result = store.get(req.params.trace_id);
  if (!result) {
    return res.status(404).json(_err(`No result for trace_id: ${req.params.trace_id}`));
  }
  return res.json(result);
});

// ── GET /simulate/health ──────────────────────────────────────────────────────
// Reports node liveness + store size (count only — no trace_ids leaked)

router.get('/health', (_req, res) => {
  return res.json({
    status:       'ok',
    node:         'simulation',
    headless:     true,
    ui_required:  false,
    stored_count: store.count(),
    timestamp:    Date.now()
  });
});

// ── Socket.IO namespace: /simulate/stream ────────────────────────────────────
// Attach after HTTP routes. Called once from index.js with the io instance.
//
// Protocol:
//   client emits  → 'stream:start'  { contract }   (simulationContract.v1 shape)
//   server emits  → 'stream:tick'   { TANTRA delta payload per tick }
//   server emits  → 'stream:done'   { trace_id, ticks_run, status }
//   server emits  → 'stream:error'  { code, reason, trace_id }

function attachStreamNamespace(io) {
  const ns = io.of('/simulate/stream');

  ns.on('connection', (socket) => {
    console.log(`[STREAM] client connected: ${socket.id}`);

    // Phase 6: track active trace_ids for this socket so disconnect releases them
    const _active_traces = new Set();

    function _failClose(trace_id, code, reason) {
      streamRegistry.release(trace_id);
      _active_traces.delete(trace_id);
      socket.emit('stream:error', { code, reason, trace_id });
      console.error(`[STREAM] fail-close trace_id=${trace_id} code=${code}`);
    }

    socket.on('stream:start', (payload) => {
      const contract = payload?.contract;

      // ── Validate contract ───────────────────────────────────────────────
      const v1 = validator.validate(contract);
      if (!v1.valid) {
        socket.emit('stream:error', {
          code:     'INVALID_CONTRACT',
          reason:   v1.errors.join('; '),
          trace_id: contract?.trace_id || null
        });
        return;
      }

      const trace_id = contract.trace_id;

      // ── One stream per trace_id ─────────────────────────────────────────
      if (!streamRegistry.register(trace_id, socket.id)) {
        socket.emit('stream:error', {
          code:     'STREAM_ALREADY_ACTIVE',
          reason:   `Stream already running for trace_id: ${trace_id}`,
          trace_id
        });
        return;
      }
      _active_traces.add(trace_id);

      // ── Adapt to SumScript ──────────────────────────────────────────────
      const { trace_id: _t, execution_id, domain, scenario,
              entities, behaviors, rules, constraints, ticks } = contract;

      const adapted = adapter.adapt({ trace_id, execution_id, domain, scenario,
                                      entities, behaviors, rules, constraints });
      if (!adapted.valid) {
        streamRegistry.release(trace_id);
        socket.emit('stream:error', {
          code:     'ADAPT_FAILED',
          reason:   adapted.errors.join('; '),
          trace_id
        });
        return;
      }

      console.log(`[STREAM] starting trace_id=${trace_id} ticks=${ticks || 10}`);

      // ── Run streaming simulation ────────────────────────────────────────
      runStream(adapted.sumscript, {
        ticks: ticks || 10,

        onTick(delta) {
          socket.emit('stream:tick', delta);
        },

        onComplete(summary) {
          streamRegistry.release(trace_id);
          _active_traces.delete(trace_id);
          socket.emit('stream:done', summary);
          console.log(`[STREAM] completed trace_id=${trace_id} ticks=${summary.ticks_run}`);
        },

        onError(err) {
          streamRegistry.release(trace_id);
          _active_traces.delete(trace_id);
          socket.emit('stream:error', err);
          console.error(`[STREAM] error trace_id=${err.trace_id} code=${err.code} reason=${err.reason}`);
        }
      });
    });

    socket.on('disconnect', () => {
      // Phase 6: stream interruption boundary
      // Release all active traces for this socket on disconnect
      for (const tid of _active_traces) {
        streamRegistry.release(tid);
        console.warn(`[STREAM] interrupted — released trace_id=${tid} on socket disconnect`);
      }
      _active_traces.clear();
      console.log(`[STREAM] client disconnected: ${socket.id}`);
    });

    // ── replay:start ──────────────────────────────────────────────────────────────────
    // client emits → 'replay:start' { trace_id }
    // server emits → 'stream:tick'  (same shape as live — no replay-specific events)
    // server emits → 'stream:done'  (same shape as live)
    // server emits → 'stream:error' (same shape as live)

    socket.on('replay:start', (payload) => {
      const trace_id = payload?.trace_id;

      if (!trace_id || typeof trace_id !== 'string') {
        socket.emit('stream:error', {
          code:     'MISSING_TRACE_ID',
          reason:   'trace_id is required',
          trace_id: null
        });
        return;
      }

      if (!streamRegistry.register(`replay:${trace_id}`, socket.id)) {
        socket.emit('stream:error', {
          code:     'REPLAY_ALREADY_ACTIVE',
          reason:   `Replay already running for trace_id: ${trace_id}`,
          trace_id
        });
        return;
      }

      // Phase 2: replay uses _isReplay=true so SimEngineStream skips recordTick
      // No need to register raw trace_id in streamRegistry for replay

      console.log(`[REPLAY] starting trace_id=${trace_id}`);

      replayStream(trace_id, {
        onTick(delta) {
          socket.emit('stream:tick', delta);
        },
        onComplete(summary) {
          streamRegistry.release(`replay:${trace_id}`);
          socket.emit('stream:done', summary);
          console.log(`[REPLAY] completed trace_id=${trace_id} ticks=${summary.ticks_run}`);
        },
        onError(err) {
          streamRegistry.release(`replay:${trace_id}`);
          socket.emit('stream:error', err);
          console.error(`[REPLAY] error trace_id=${err.trace_id} code=${err.code}`);
        }
      });
    });
  });
}

module.exports = router;
module.exports.attachStreamNamespace = attachStreamNamespace;
