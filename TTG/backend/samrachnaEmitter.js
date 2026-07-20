'use strict';

/**
 * samrachnaEmitter.js
 *
 * Emits ecosystem execution events to the frontend Samrachna panel
 * via Socket.IO after every TANTRA spine execution.
 *
 * All routes (SVACS, NamamiGange, NICAI, UICICS) call this after execution.
 */

function emitToSamrachna(event) {
  try {
    const app = global._app;
    if (!app) return;
    const io = app.get('io');
    if (!io) return;
    io.emit('samrachna:event', {
      ...event,
      timestamp: event.timestamp || new Date().toISOString()
    });
  } catch { /* non-blocking */ }
}

module.exports = { emitToSamrachna };
