'use strict';

/**
 * maritimeAdapter.js
 *
 * Converts raw maritime data (JSON | CSV | mock stream) into a
 * schema-ready execution payload for the BHIV governance pipeline.
 *
 * Pipeline:
 *   raw input → parse → validate → normalize → map → executionSchema
 *
 * RULE: This module ONLY prepares the schema.
 *       It makes ZERO governance decisions.
 *       Decision authority belongs to Mitra (external).
 *       Enforcement belongs to enforcementGate.js.
 */

const { v4: uuidv4 } = require('uuid');
const template = require('./templates/maritime_template.json');

// ─── Coordinate constants ────────────────────────────────────────────────────
// Fixed origin for deterministic, reversible lat/lon ↔ x/z conversion.
// All runs use the same origin — results are consistent and replayable.
const LAT_ORIGIN = 0.0;
const LON_ORIGIN = 0.0;
const SCALE      = template.defaults.coordinate_scale; // 100.0

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Adapt a single vessel record (JSON object) into a governed execution schema.
 * @param {Object} rawVessel  - Raw domain input
 * @param {Object} [opts]     - { trace_id, execution_id } — generated if omitted
 * @returns {{ success, schema, errors }}
 */
function adaptVessel(rawVessel, opts = {}) {
  // 1. Parse (already an object — normalise field names)
  const parsed = _parseJSON(rawVessel);

  // 2. Validate domain fields
  const validation = _validateDomainInput(parsed);
  if (!validation.valid) {
    return { success: false, schema: null, errors: validation.errors };
  }

  // 3. Normalize
  const normalized = _normalize(parsed);

  // 4. Map domain → engine schema
  const engineSchema = _mapToEngineSchema(normalized);

  // 5. Attach IDs only — no decision, no governance assumption
  const schema = _attachIds(engineSchema, opts);

  return { success: true, schema, errors: [] };
}

/**
 * Adapt a CSV string containing one or more vessel rows.
 * Expected header: vessel_id,lat,lon,speed,heading,status
 * @param {string} csvText
 * @param {Object} [opts]
 * @returns {{ success, schemas: Array, errors: Array }}
 */
function adaptCSV(csvText, opts = {}) {
  const rows  = _parseCSV(csvText);
  const out   = { success: true, schemas: [], errors: [] };

  rows.forEach((row, i) => {
    const result = adaptVessel(row, {
      trace_id:     opts.trace_id     || uuidv4(),
      execution_id: opts.execution_id || `exec_maritime_${Date.now()}_${i}`
    });
    if (result.success) {
      out.schemas.push(result.schema);
    } else {
      out.success = false;
      out.errors.push({ row: i + 1, errors: result.errors });
    }
  });

  return out;
}

/**
 * Adapt a mock stream — array of vessel snapshots arriving over time.
 * Each item is processed independently with its own trace/execution IDs.
 * @param {Array<Object>} stream
 * @returns {{ success, schemas: Array, errors: Array }}
 */
function adaptStream(stream) {
  if (!Array.isArray(stream)) {
    return { success: false, schemas: [], errors: ['Stream must be an array'] };
  }

  const out = { success: true, schemas: [], errors: [] };

  stream.forEach((item, i) => {
    const result = adaptVessel(item, {
      trace_id:     uuidv4(),
      execution_id: `exec_maritime_stream_${Date.now()}_${i}`
    });
    if (result.success) {
      out.schemas.push(result.schema);
    } else {
      out.success = false;
      out.errors.push({ index: i, vessel_id: item.vessel_id || '?', errors: result.errors });
    }
  });

  return out;
}

// ─── Coordinate mapping ──────────────────────────────────────────────────────

/**
 * lat → x  (deterministic, reversible)
 * x = (lat - LAT_ORIGIN) * SCALE
 */
function latToX(lat) {
  return parseFloat(((lat - LAT_ORIGIN) * SCALE).toFixed(6));
}

/**
 * lon → z  (deterministic, reversible)
 * z = (lon - LON_ORIGIN) * SCALE
 */
function lonToZ(lon) {
  return parseFloat(((lon - LON_ORIGIN) * SCALE).toFixed(6));
}

/**
 * Reverse: x → lat
 */
function xToLat(x) {
  return parseFloat((x / SCALE + LAT_ORIGIN).toFixed(8));
}

/**
 * Reverse: z → lon
 */
function zToLon(z) {
  return parseFloat((z / SCALE + LON_ORIGIN).toFixed(8));
}

// ─── Internal steps ──────────────────────────────────────────────────────────

function _parseJSON(raw) {
  // Accept both snake_case and camelCase field names
  return {
    vessel_id: raw.vessel_id || raw.vesselId || raw.id || null,
    lat:       raw.lat       !== undefined ? raw.lat       : raw.latitude,
    lon:       raw.lon       !== undefined ? raw.lon       : raw.longitude,
    speed:     raw.speed     !== undefined ? raw.speed     : raw.knots,
    heading:   raw.heading   !== undefined ? raw.heading   : raw.course,
    status:    raw.status    || 'moving'
  };
}

function _parseCSV(csvText) {
  const lines  = csvText.trim().split('\n').map(l => l.trim()).filter(Boolean);
  if (lines.length < 2) return [];

  const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
  return lines.slice(1).map(line => {
    const values = line.split(',').map(v => v.trim());
    const obj    = {};
    headers.forEach((h, i) => { obj[h] = values[i]; });
    // Coerce numeric fields
    ['lat', 'lon', 'speed', 'heading'].forEach(f => {
      if (obj[f] !== undefined) obj[f] = parseFloat(obj[f]);
    });
    return obj;
  });
}

function _validateDomainInput(parsed) {
  const errors = [];

  if (!parsed.vessel_id || typeof parsed.vessel_id !== 'string') {
    errors.push('vessel_id is required and must be a string');
  }
  if (parsed.lat === undefined || parsed.lat === null || isNaN(parsed.lat)) {
    errors.push('lat is required and must be a number');
  } else if (parsed.lat < -90 || parsed.lat > 90) {
    errors.push('lat must be between -90 and 90');
  }
  if (parsed.lon === undefined || parsed.lon === null || isNaN(parsed.lon)) {
    errors.push('lon is required and must be a number');
  } else if (parsed.lon < -180 || parsed.lon > 180) {
    errors.push('lon must be between -180 and 180');
  }
  if (parsed.speed === undefined || parsed.speed === null || isNaN(parsed.speed)) {
    errors.push('speed is required and must be a number');
  } else if (parsed.speed < 0) {
    errors.push('speed must be >= 0');
  }
  if (parsed.heading === undefined || parsed.heading === null || isNaN(parsed.heading)) {
    errors.push('heading is required and must be a number');
  } else if (parsed.heading < 0 || parsed.heading > 360) {
    errors.push('heading must be between 0 and 360');
  }
  if (!['moving', 'anchored'].includes(parsed.status)) {
    errors.push('status must be "moving" or "anchored"');
  }

  return { valid: errors.length === 0, errors };
}

function _normalize(parsed) {
  return {
    vessel_id: String(parsed.vessel_id).replace(/[^a-zA-Z0-9_-]/g, '_'),
    lat:       parseFloat(parsed.lat),
    lon:       parseFloat(parsed.lon),
    speed:     parseFloat(parsed.speed),
    heading:   parseFloat(parsed.heading),
    status:    parsed.status
  };
}

/**
 * Map normalized domain fields → Atharva's engine execution contract.
 *
 * Contract required fields:
 *   execution_id, trace_id, game_mode, entities[], physics, scoring
 *
 * Maritime mapping:
 *   vessel   → entity (type: "npc" — closest engine type for a tracked object)
 *   lat/lon  → transform.position [x, 0, z]
 *   heading  → transform.rotation [0, heading, 0]
 *   speed    → movement.speed (clamped 1–15 per contract)
 *   status   → player_params (anchored = health 0 movement, moving = active)
 */
function _mapToEngineSchema(n) {
  const x = latToX(n.lat);
  const z = lonToZ(n.lon);

  // Clamp speed to engine contract range [1, 15]
  const engineSpeed = Math.min(15, Math.max(1, parseFloat(n.speed.toFixed(2))));

  return {
    // ── Atharva contract required fields ──────────────────────────────────
    game_mode: 'open_scene',

    scene: {
      scene_id:      'scene_maritime',
      ambient_light: [0.5, 0.7, 0.9],
      skybox:        'ocean_sky'
    },

    entities: [
      {
        id:   n.vessel_id,
        type: 'npc',
        transform: {
          position: [x, 0, z],
          rotation: [0, n.heading, 0],
          scale:    [1, 1, 1]
        },
        material: {
          shader:  'standard',
          texture: 'vessel_hull',
          color:   [0.2, 0.4, 0.8]
        },
        components: {
          mesh:     'vessel',
          collider: 'box',
          script:   'vessel_controller'
        }
      }
    ],

    physics: {
      gravity:          [0, 0, 0],   // maritime — no vertical gravity
      friction:         0.1,
      bounce:           0.0,
      air_resistance:   0.05,
      collision_force:  1.0
    },

    movement: {
      speed:       engineSpeed,
      jump_height: 0
    },

    camera: {
      type:     'top_down',
      distance: 20
    },

    spawn_rules: {
      obstacles: 0,
      frequency: template.defaults.update_interval_ms / 1000,
      distance:  template.defaults.proximity_radius
    },

    scoring: {
      rules: {
        distance:    0,
        collectibles: 0,
        time:        0
      },
      end_conditions: ['time_limit']
    },

    player_params: {
      health:  n.status === 'moving' ? 1 : 0,
      jetpack: false
    },

    // ── Maritime domain metadata (passed through, not consumed by engine) ──
    domain: {
      type:      'maritime',
      vessel_id: n.vessel_id,
      lat:       n.lat,
      lon:       n.lon,
      speed:     n.speed,
      heading:   n.heading,
      status:    n.status
    }
  };
}

/**
 * Attach trace_id and execution_id to the schema.
 * This is identity stamping only — NOT a governance decision.
 * Decision authority is external (Mitra).
 */
function _attachIds(schema, opts) {
  const trace_id     = opts.trace_id     || uuidv4();
  const execution_id = opts.execution_id || `exec_maritime_${Date.now()}`;

  return {
    execution_id,
    trace_id,
    ...schema
  };
}

// ─── Exports ─────────────────────────────────────────────────────────────────

module.exports = {
  adaptVessel,
  adaptCSV,
  adaptStream,
  latToX,
  lonToZ,
  xToLat,
  zToLon
};
