'use strict';

/**
 * test_renderer_headless.js
 *
 * Validates CanvasRenderer headless mode using SimEngine output.
 * No browser, no DOM — pure Node.js.
 *
 * Run: node backend/simulation/engine/test_renderer_headless.js
 */

// ── Minimal CanvasRenderer port for Node (headless only) ─────────────────────
// The browser version uses ES module export — this is the CJS equivalent
// for server-side headless rendering and testing.

const STATE_COLORS = {
  active: '#22d3ee', idle: '#a78bfa', stopped: '#f59e0b', destroyed: '#ef4444'
};

class HeadlessRenderer {
  constructor(opts = {}) {
    this._width    = opts.width  || 600;
    this._height   = opts.height || 600;
    this._viewport = { minX: -100, maxX: 100, minZ: -100, maxZ: 100 };
  }

  fitViewport(entities) {
    const positions = Object.values(entities).map(e => e.position);
    if (!positions.length) return;
    let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity;
    for (const [x, , z] of positions) {
      if (x < minX) minX = x; if (x > maxX) maxX = x;
      if (z < minZ) minZ = z; if (z > maxZ) maxZ = z;
    }
    const padX = Math.max((maxX - minX) * 0.2, 10);
    const padZ = Math.max((maxZ - minZ) * 0.2, 10);
    this._viewport = { minX: minX - padX, maxX: maxX + padX, minZ: minZ - padZ, maxZ: maxZ + padZ };
  }

  _toScreen(x, z) {
    const { minX, maxX, minZ, maxZ } = this._viewport;
    return [
      ((x - minX) / (maxX - minX)) * this._width,
      ((z - minZ) / (maxZ - minZ)) * this._height
    ];
  }

  renderHeadless(tick_snapshots, zones, flags, blocked) {
    return tick_snapshots.map(snap => ({
      tick:         snap.tick,
      entity_count: Object.keys(snap.entity_states).length,
      entities: Object.entries(snap.entity_states).map(([id, e]) => ({
        id,
        state:    e.state,
        position: e.position,
        velocity: e.velocity,
        color:    STATE_COLORS[e.state] || '#94a3b8',
        screen:   this._toScreen(e.position[0], e.position[2] || 0),
        flagged:  !!(flags && flags[id]),
        blocked:  !!(blocked && blocked[id])
      })),
      zones: Object.entries(zones || {}).map(([id, z]) => ({
        id, position: z.position, radius: z.radius, members: z.members || []
      })),
      rendered_at: Date.now()
    }));
  }
}

// ─── Run SimEngine ────────────────────────────────────────────────────────────

const { run } = require('./SimEngine');

const CONTRACT = {
  trace_id:     'trace_render_test_001',
  execution_id: 'exec_render_test_001',
  entities: [
    { id: 'ALPHA', type: 'vessel',   position: [0,  0, 0],  state: 'active',  behaviors: ['go'],   meta: {} },
    { id: 'BRAVO', type: 'vessel',   position: [40, 0, 0],  state: 'active',  behaviors: ['stay'], meta: {} },
    { id: 'ZONE1', type: 'zone',     position: [20, 0, 0],  state: 'active',  behaviors: [],       meta: { radius: 8 } }
  ],
  transforms: [],
  rules: [],
  behaviors: [
    { id: 'go',   script: 'move_to', params: { target: [40, 0, 0], speed: 3, threshold: 1 } },
    { id: 'stay', script: 'anchor',  params: {} }
  ]
};

// ─── Tests ────────────────────────────────────────────────────────────────────

let passed = 0, failed = 0;

function assert(label, condition, detail = '') {
  if (condition) { console.log(`  ✅ ${label}`); passed++; }
  else           { console.error(`  ❌ ${label}${detail ? ' — ' + detail : ''}`); failed++; }
}

console.log('\n══════════════════════════════════════════');
console.log('  CanvasRenderer — Headless Test Suite');
console.log('══════════════════════════════════════════\n');

// 1. SimEngine produces output
console.log('1. SimEngine Output');
const result = run(CONTRACT, { ticks: 8 });
assert('sim succeeds',           result.success, result.error);
assert('8 tick snapshots',       result.tick_snapshots.length === 8);
assert('entities present',       Object.keys(result.entities).length === 3);

// 2. Headless renderer
console.log('\n2. Headless Renderer');
const renderer = new HeadlessRenderer({ width: 600, height: 400 });
renderer.fitViewport(result.entities);

const frames = renderer.renderHeadless(
  result.tick_snapshots,
  result.zones,
  result.flags,
  result.blocked
);

assert('8 frames produced',      frames.length === 8);
assert('frame has tick',         typeof frames[0].tick === 'number');
assert('frame has entity_count', typeof frames[0].entity_count === 'number');
assert('frame has entities arr', Array.isArray(frames[0].entities));
assert('frame has zones arr',    Array.isArray(frames[0].zones));
assert('frame has rendered_at',  typeof frames[0].rendered_at === 'number');

// 3. Entity frame data
console.log('\n3. Entity Frame Data');
const alpha_frame = frames[0].entities.find(e => e.id === 'ALPHA');
const bravo_frame = frames[0].entities.find(e => e.id === 'BRAVO');

assert('ALPHA in frame',         !!alpha_frame);
assert('BRAVO in frame',         !!bravo_frame);
assert('entity has state',       typeof alpha_frame.state === 'string');
assert('entity has position',    Array.isArray(alpha_frame.position));
assert('entity has screen [x,y]',Array.isArray(alpha_frame.screen) && alpha_frame.screen.length === 2);
assert('screen x in range',      alpha_frame.screen[0] >= -10 && alpha_frame.screen[0] <= 610);
assert('screen y in range',      alpha_frame.screen[1] >= 0 && alpha_frame.screen[1] <= 400);
assert('entity has color',       alpha_frame.color.startsWith('#'));
assert('BRAVO stopped = amber',  bravo_frame.color === '#f59e0b');

// 4. Zone in frame
console.log('\n4. Zone Frame Data');
const zone_frame = frames[0].zones.find(z => z.id === 'ZONE1');
assert('ZONE1 in frame',         !!zone_frame);
assert('zone has position',      Array.isArray(zone_frame.position));
assert('zone has radius',        typeof zone_frame.radius === 'number');

// 5. Movement across frames
console.log('\n5. Movement Across Frames');
const alpha_f0 = frames[0].entities.find(e => e.id === 'ALPHA');
const alpha_f7 = frames[7].entities.find(e => e.id === 'ALPHA');
assert('ALPHA moved across ticks',
  alpha_f7.position[0] > alpha_f0.position[0]
);
assert('ALPHA screen position changed',
  alpha_f7.screen[0] !== alpha_f0.screen[0]
);

// 6. Determinism
console.log('\n6. Determinism');
const r2 = run(CONTRACT, { ticks: 8 });
renderer.fitViewport(r2.entities);
const frames2 = renderer.renderHeadless(r2.tick_snapshots, r2.zones, r2.flags, r2.blocked);
assert('same frame[0] positions both runs',
  JSON.stringify(frames[0].entities.map(e => e.position)) ===
  JSON.stringify(frames2[0].entities.map(e => e.position))
);

// 7. Headless output shape (NICAI/Samruddhi ready)
console.log('\n7. Output Shape');
const sample = frames[3];
assert('tick is number',         typeof sample.tick === 'number');
assert('entity_count is number', typeof sample.entity_count === 'number');
assert('all entities have id',   sample.entities.every(e => typeof e.id === 'string'));
assert('all entities have state',sample.entities.every(e => typeof e.state === 'string'));
assert('all entities have screen',sample.entities.every(e => Array.isArray(e.screen)));

// ─── Summary ──────────────────────────────────────────────────────────────────

console.log('\n══════════════════════════════════════════');
console.log(`  Results: ${passed} passed, ${failed} failed`);
console.log('══════════════════════════════════════════\n');

if (failed > 0) process.exit(1);
