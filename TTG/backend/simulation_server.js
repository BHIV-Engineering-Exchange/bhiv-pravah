'use strict';

/**
 * simulation_server.js
 *
 * Headless simulation node.
 *
 * Exposes exactly 4 routes:
 *   POST /simulate/run
 *   POST /simulate/replay/:trace_id
 *   GET  /simulate/result/:trace_id
 *   GET  /simulate/health
 *
 * No socket. No dashboard. No auth. No UI dependency.
 * Runs standalone or embedded in a larger service.
 */

require('dotenv').config();

const express        = require('express');
const cors           = require('cors');
const simulateRoutes = require('./routes/simulate');

const app  = express();
const PORT = process.env.SIM_PORT || 3001;

// Body size limit enforced at server level (256KB)
app.use(express.json({ limit: '256kb' }));
app.use(cors({ origin: process.env.SIM_CORS_ORIGIN || '*' }));

// Simulation routes — the only routes on this server
app.use('/simulate', simulateRoutes);

// Root — confirms node identity
app.get('/', (_req, res) => {
  res.json({
    node:        'simulation',
    status:      'ok',
    headless:    true,
    ui_required: false,
    routes: [
      'POST /simulate/run',
      'POST /simulate/replay/:trace_id',
      'GET  /simulate/result/:trace_id',
      'GET  /simulate/health'
    ]
  });
});

// Catch-all 404 — this node does one thing
app.use((_req, res) => {
  res.status(404).json({
    status: 'failed',
    error:  'Unknown route. Simulation node only handles /simulate/* routes.'
  });
});

const server = app.listen(PORT, () => {
  console.log(`[SIM NODE] Headless simulation server running on port ${PORT}`);
  console.log(`[SIM NODE] POST http://localhost:${PORT}/simulate/run`);
  console.log(`[SIM NODE] GET  http://localhost:${PORT}/simulate/health`);
});

module.exports = { app, server };
