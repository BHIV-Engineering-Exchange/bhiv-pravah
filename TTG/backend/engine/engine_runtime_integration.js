/**
 * Engine Socket Integration for Runtime Events
 * Adds runtime event processing to the existing engine socket
 * 
 * This module extends engine_socket.js with consequence system integration
 */

const { setupRuntimeEventHandler, getPipelineStatistics } = require('../dispatcher_event_pipeline');

/**
 * Integrate runtime event processing with engine socket
 * @param {Object} socket - Engine socket instance
 * @param {Object} io - Socket.IO instance for broadcasting
 * @param {Object} context - Socket context
 */
function integrateRuntimeEventProcessing(socket, io, context = {}) {
  const { engineId, userId } = context;

  console.log('[ENGINE INTEGRATION] Adding runtime event processing for:', engineId);

  // Setup runtime event handler
  setupRuntimeEventHandler(socket, { engineId, userId });

  // Add pipeline statistics endpoint
  socket.on('get_pipeline_stats', () => {
    const stats = getPipelineStatistics();
    socket.emit('pipeline_stats', stats);
  });

  // Broadcast pipeline events to dashboard
  const { pipelineEvents } = require('../dispatcher_event_pipeline');

  pipelineEvents.on('event_processed', (data) => {
    // Broadcast to all dashboard clients
    io.emit('runtime_event_processed', {
      event_type: data.event.event_type,
      event_id: data.event.event_id,
      jobs_dispatched: data.result.jobs_dispatched,
      critical: data.critical,
      timestamp: data.timestamp
    });
  });

  console.log('[ENGINE INTEGRATION] Runtime event processing enabled');
}

/**
 * Add runtime event processing to existing engine socket setup
 * This function should be called from engine_socket.js
 * 
 * @param {Object} engineNS - Engine namespace
 * @param {Object} io - Socket.IO instance
 */
function enhanceEngineSocket(engineNS, io) {
  console.log('[ENGINE INTEGRATION] Enhancing engine socket with runtime event processing');

  // Intercept connection event to add runtime event handlers
  const originalConnectionHandler = engineNS._events.connection;

  engineNS.on('connection', (socket) => {
    // Let original handler run first
    if (originalConnectionHandler) {
      // Original handler already attached, just add our integration
    }

    // Add runtime event processing after authentication
    setTimeout(() => {
      if (socket.engineId) {
        integrateRuntimeEventProcessing(socket, io, {
          engineId: socket.engineId,
          userId: socket.userId || 'unknown'
        });
      }
    }, 100);
  });

  console.log('[ENGINE INTEGRATION] Engine socket enhanced successfully');
}

module.exports = {
  integrateRuntimeEventProcessing,
  enhanceEngineSocket
};
