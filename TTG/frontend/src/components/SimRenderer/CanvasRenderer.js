'use strict';

/**
 * CanvasRenderer.js
 *
 * Lightweight Canvas 2D renderer for SimEngine output.
 * NO Three.js. NO WebGL. NO external deps.
 *
 * Two modes:
 *   browser  — renders to a <canvas> DOM element
 *   headless — renders to an OffscreenCanvas, returns pixel data / JSON frame
 *
 * Renders:
 *   - Entities as colored shapes by type
 *   - Velocity vectors as directional arrows
 *   - State as color overlay (active/idle/stopped/destroyed)
 *   - Zone boundaries as dashed circles
 *   - Flags/blocks as icon overlays
 *   - Tick counter + entity count HUD
 *
 * Coordinate mapping:
 *   Simulation space  → screen space via viewport transform
 *   World [x, z]      → canvas [px, py]  (y axis is ignored — top-down view)
 */

// ─── State colors ─────────────────────────────────────────────────────────────

const STATE_COLORS = {
  active:    '#22d3ee',   // cyan
  idle:      '#a78bfa',   // violet
  stopped:   '#f59e0b',   // amber
  destroyed: '#ef4444'    // red
};

const TYPE_SHAPES = {
  vessel:   'circle',
  obstacle: 'square',
  zone:     'ring',
  marker:   'diamond',
  agent:    'triangle'
};

const FLAG_COLOR  = '#f97316';   // orange
const BLOCK_COLOR = '#dc2626';   // red

// ─── CanvasRenderer class ─────────────────────────────────────────────────────

class CanvasRenderer {
  /**
   * @param {Object} opts
   * @param {HTMLCanvasElement|null} opts.canvas   - DOM canvas (null = headless)
   * @param {number}  opts.width    - Canvas width  (default 600)
   * @param {number}  opts.height   - Canvas height (default 600)
   * @param {boolean} opts.headless - Force headless mode
   */
  constructor(opts = {}) {
    this._width    = opts.width  || 600;
    this._height   = opts.height || 600;
    this._headless = opts.headless || !opts.canvas;
    this._canvas   = null;
    this._ctx      = null;
    this._viewport = { minX: -100, maxX: 100, minZ: -100, maxZ: 100 };
    this._frames   = [];   // headless: stores frame snapshots

    if (!this._headless && opts.canvas) {
      this._canvas = opts.canvas;
      this._canvas.width  = this._width;
      this._canvas.height = this._height;
      this._ctx = this._canvas.getContext('2d');
    }
  }

  // ── Viewport ──────────────────────────────────────────────────────────────

  /**
   * Set the world-space viewport from entity positions.
   * Auto-fits all entities with padding.
   *
   * @param {Object} entities  - { [id]: entity }
   */
  fitViewport(entities) {
    const positions = Object.values(entities).map(e => e.position);
    if (positions.length === 0) return;

    let minX = Infinity, maxX = -Infinity;
    let minZ = Infinity, maxZ = -Infinity;

    for (const [x, , z] of positions) {
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (z < minZ) minZ = z;
      if (z > maxZ) maxZ = z;
    }

    const padX = Math.max((maxX - minX) * 0.2, 10);
    const padZ = Math.max((maxZ - minZ) * 0.2, 10);

    this._viewport = {
      minX: minX - padX,
      maxX: maxX + padX,
      minZ: minZ - padZ,
      maxZ: maxZ + padZ
    };
  }

  // ── World → screen ────────────────────────────────────────────────────────

  _toScreen(x, z) {
    const { minX, maxX, minZ, maxZ } = this._viewport;
    const px = ((x - minX) / (maxX - minX)) * this._width;
    const py = ((z - minZ) / (maxZ - minZ)) * this._height;
    return [px, py];
  }

  // ── Render ────────────────────────────────────────────────────────────────

  /**
   * Render one frame from a SimEngine result or tick snapshot.
   *
   * @param {Object} frame
   * @param {Object} frame.entities       - { [id]: entity }
   * @param {Object} [frame.zones]        - { [id]: { position, radius, members } }
   * @param {Object} [frame.flags]        - { [id]: { reason } }
   * @param {Object} [frame.blocked]      - { [id]: { reason } }
   * @param {number} [frame.tick]         - Current tick number
   * @param {string} [frame.trace_id]
   * @returns {Object|null}  headless: frame snapshot JSON | browser: null
   */
  render(frame) {
    const ctx = this._getCtx();
    if (!ctx) return this._headlessFrame(frame);

    this._drawFrame(ctx, frame);
    return null;
  }

  /**
   * Render a sequence of tick snapshots as an animation.
   * Browser only — uses requestAnimationFrame.
   *
   * @param {Object[]} tick_snapshots  - From SimEngine result
   * @param {Object}   final_entities  - Final entity state
   * @param {Object}   [zones]
   * @param {Object}   [flags]
   * @param {Object}   [blocked]
   * @param {number}   [interval_ms]   - Ms between frames (default 200)
   * @returns {{ stop: Function }}     - Call stop() to cancel
   */
  animate(tick_snapshots, final_entities, zones, flags, blocked, interval_ms) {
    if (this._headless) return { stop: () => {} };

    const ms    = interval_ms || 200;
    let   idx   = 0;
    let   timer = null;

    const step = () => {
      if (idx >= tick_snapshots.length) {
        // Hold final frame
        this.render({ entities: final_entities, zones, flags, blocked, tick: tick_snapshots.length });
        return;
      }

      const snap = tick_snapshots[idx];
      this.render({
        entities: snap.entity_states,
        zones,
        flags,
        blocked,
        tick: snap.tick
      });
      idx++;
      timer = setTimeout(step, ms);
    };

    step();
    return { stop: () => { if (timer) clearTimeout(timer); } };
  }

  /**
   * Render all tick snapshots headlessly.
   * Returns array of frame snapshots (JSON).
   *
   * @param {Object[]} tick_snapshots
   * @param {Object}   [zones]
   * @param {Object}   [flags]
   * @param {Object}   [blocked]
   * @returns {Object[]} frames
   */
  renderHeadless(tick_snapshots, zones, flags, blocked) {
    return tick_snapshots.map(snap => this._headlessFrame({
      entities: snap.entity_states,
      zones:    zones    || {},
      flags:    flags    || {},
      blocked:  blocked  || {},
      tick:     snap.tick
    }));
  }

  // ── Core draw ─────────────────────────────────────────────────────────────

  _drawFrame(ctx, frame) {
    const { entities = {}, zones = {}, flags = {}, blocked = {}, tick = 0, trace_id } = frame;

    // Background
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, this._width, this._height);

    // Grid
    this._drawGrid(ctx);

    // Zones first (behind entities)
    for (const [zone_id, zone] of Object.entries(zones)) {
      this._drawZone(ctx, zone_id, zone);
    }

    // Entities
    for (const [id, entity] of Object.entries(entities)) {
      this._drawEntity(ctx, id, entity, flags[id], blocked[id]);
    }

    // HUD
    this._drawHUD(ctx, tick, Object.keys(entities).length, trace_id);
  }

  _drawGrid(ctx) {
    ctx.strokeStyle = 'rgba(255,255,255,0.04)';
    ctx.lineWidth   = 1;
    const step = this._width / 10;
    for (let i = 0; i <= this._width; i += step) {
      ctx.beginPath();
      ctx.moveTo(i, 0);
      ctx.lineTo(i, this._height);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, i);
      ctx.lineTo(this._width, i);
      ctx.stroke();
    }
  }

  _drawZone(ctx, zone_id, zone) {
    if (!zone.position) return;
    const [px, py] = this._toScreen(zone.position[0], zone.position[2]);

    // Convert world radius to screen radius
    const { minX, maxX } = this._viewport;
    const worldWidth = maxX - minX;
    const screenRadius = (zone.radius / worldWidth) * this._width;

    ctx.save();
    ctx.strokeStyle = 'rgba(251,191,36,0.5)';
    ctx.lineWidth   = 1.5;
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.arc(px, py, Math.max(screenRadius, 8), 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);

    // Zone label
    ctx.fillStyle = 'rgba(251,191,36,0.7)';
    ctx.font      = '10px monospace';
    ctx.fillText(zone_id, px + 4, py - 4);
    ctx.restore();
  }

  _drawEntity(ctx, id, entity, flag, block) {
    const [px, py] = this._toScreen(entity.position[0], entity.position[2] || entity.position[2] || 0);
    const shape    = TYPE_SHAPES[entity.type] || 'circle';
    const color    = STATE_COLORS[entity.state] || '#94a3b8';
    const r        = 8;

    ctx.save();

    // Shadow glow
    ctx.shadowColor = color;
    ctx.shadowBlur  = 10;

    // Shape
    ctx.fillStyle = color;
    this._drawShape(ctx, shape, px, py, r);

    // Velocity arrow
    if (entity.velocity) {
      const [vx, , vz] = entity.velocity;
      const mag = Math.sqrt(vx * vx + vz * vz);
      if (mag > 0.001) {
        this._drawArrow(ctx, px, py, vx, vz, mag, color);
      }
    }

    ctx.shadowBlur = 0;

    // Flag overlay
    if (flag) {
      ctx.strokeStyle = FLAG_COLOR;
      ctx.lineWidth   = 2;
      ctx.beginPath();
      ctx.arc(px, py, r + 4, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Block overlay
    if (block) {
      ctx.strokeStyle = BLOCK_COLOR;
      ctx.lineWidth   = 2.5;
      ctx.beginPath();
      ctx.moveTo(px - r - 4, py - r - 4);
      ctx.lineTo(px + r + 4, py + r + 4);
      ctx.moveTo(px + r + 4, py - r - 4);
      ctx.lineTo(px - r - 4, py + r + 4);
      ctx.stroke();
    }

    // Entity label
    ctx.fillStyle = 'rgba(255,255,255,0.75)';
    ctx.font      = '9px monospace';
    ctx.fillText(id.length > 12 ? id.slice(0, 12) : id, px + r + 3, py + 4);

    ctx.restore();
  }

  _drawShape(ctx, shape, px, py, r) {
    ctx.beginPath();
    switch (shape) {
      case 'circle':
        ctx.arc(px, py, r, 0, Math.PI * 2);
        break;
      case 'square':
        ctx.rect(px - r, py - r, r * 2, r * 2);
        break;
      case 'ring':
        ctx.arc(px, py, r, 0, Math.PI * 2);
        ctx.fillStyle = 'transparent';
        ctx.strokeStyle = ctx.fillStyle;
        break;
      case 'diamond':
        ctx.moveTo(px,     py - r);
        ctx.lineTo(px + r, py);
        ctx.lineTo(px,     py + r);
        ctx.lineTo(px - r, py);
        ctx.closePath();
        break;
      case 'triangle':
        ctx.moveTo(px,         py - r);
        ctx.lineTo(px + r,     py + r);
        ctx.lineTo(px - r,     py + r);
        ctx.closePath();
        break;
      default:
        ctx.arc(px, py, r, 0, Math.PI * 2);
    }
    ctx.fill();
  }

  _drawArrow(ctx, px, py, vx, vz, mag, color) {
    const scale  = Math.min(mag * 20, 30);
    const norm   = [vx / mag, vz / mag];
    const ex     = px + norm[0] * scale;
    const ey     = py + norm[1] * scale;
    const headLen = 6;
    const angle  = Math.atan2(ey - py, ex - px);

    ctx.strokeStyle = color;
    ctx.lineWidth   = 1.5;
    ctx.globalAlpha = 0.7;
    ctx.beginPath();
    ctx.moveTo(px, py);
    ctx.lineTo(ex, ey);
    ctx.stroke();

    // Arrowhead
    ctx.beginPath();
    ctx.moveTo(ex, ey);
    ctx.lineTo(ex - headLen * Math.cos(angle - 0.4), ey - headLen * Math.sin(angle - 0.4));
    ctx.moveTo(ex, ey);
    ctx.lineTo(ex - headLen * Math.cos(angle + 0.4), ey - headLen * Math.sin(angle + 0.4));
    ctx.stroke();
    ctx.globalAlpha = 1;
  }

  _drawHUD(ctx, tick, entityCount, trace_id) {
    ctx.save();
    ctx.fillStyle = 'rgba(15,23,42,0.75)';
    ctx.fillRect(8, 8, 200, 52);

    ctx.fillStyle = '#94a3b8';
    ctx.font      = '11px monospace';
    ctx.fillText(`tick: ${tick}`,           16, 26);
    ctx.fillText(`entities: ${entityCount}`, 16, 42);
    if (trace_id) {
      ctx.fillStyle = 'rgba(148,163,184,0.5)';
      ctx.font      = '9px monospace';
      ctx.fillText(trace_id.slice(0, 28), 16, 54);
    }
    ctx.restore();
  }

  // ── Headless frame ────────────────────────────────────────────────────────

  _headlessFrame(frame) {
    const { entities = {}, zones = {}, flags = {}, blocked = {}, tick = 0 } = frame;

    return {
      tick,
      entity_count: Object.keys(entities).length,
      entities: Object.entries(entities).map(([id, e]) => ({
        id,
        type:     e.type,
        state:    e.state,
        position: e.position,
        velocity: e.velocity,
        flagged:  !!flags[id],
        blocked:  !!blocked[id],
        screen:   this._toScreen(e.position[0], e.position[2] || 0)
      })),
      zones: Object.entries(zones).map(([id, z]) => ({
        id,
        position: z.position,
        radius:   z.radius,
        members:  z.members || []
      })),
      rendered_at: Date.now()
    };
  }

  // ── Context helper ────────────────────────────────────────────────────────

  _getCtx() {
    if (this._headless) return null;
    return this._ctx;
  }

  // ── Legend ────────────────────────────────────────────────────────────────

  /**
   * Draw a static legend onto the canvas.
   * Call once after mounting.
   */
  drawLegend() {
    const ctx = this._getCtx();
    if (!ctx) return;

    const x = this._width - 130;
    let   y = 16;

    ctx.save();
    ctx.fillStyle = 'rgba(15,23,42,0.8)';
    ctx.fillRect(x - 8, y - 12, 130, 120);

    ctx.font = '10px monospace';

    for (const [state, color] of Object.entries(STATE_COLORS)) {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(x + 6, y, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#94a3b8';
      ctx.fillText(state, x + 16, y + 4);
      y += 18;
    }

    ctx.fillStyle = FLAG_COLOR;
    ctx.fillText('○ flagged', x, y + 4);
    y += 18;
    ctx.fillStyle = BLOCK_COLOR;
    ctx.fillText('✕ blocked', x, y + 4);

    ctx.restore();
  }
}

// ─── Exports ──────────────────────────────────────────────────────────────────

export default CanvasRenderer;
