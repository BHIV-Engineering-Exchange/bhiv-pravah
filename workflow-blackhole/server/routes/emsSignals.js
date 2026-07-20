const express = require('express');
const router = express.Router();
const emsSignals = require('../services/ems_signals');
const auth = require('../middleware/auth');

/**
 * EMS Signal API Routes
 * Endpoints for receiving and managing real-time employee activity signals
 */

// Initialize employee signal tracking
router.post('/signals/init', async (req, res) => {
  try {
    const { employeeId, sessionId } = req.body;

    if (!employeeId || !sessionId) {
      return res.status(400).json({ 
        error: 'employeeId and sessionId are required' 
      });
    }

    emsSignals.initializeEmployee(employeeId, sessionId);

    res.json({
      success: true,
      message: 'Signal tracking initialized',
      employeeId,
      sessionId,
      timestamp: new Date()
    });
  } catch (error) {
    console.error('Error initializing signal tracking:', error);
    res.status(500).json({ error: 'Failed to initialize signal tracking' });
  }
});

// Receive batch signals from client
router.post('/signals', async (req, res) => {
  try {
    const { employeeId, sessionId, signals } = req.body;

    if (!employeeId || !signals || !Array.isArray(signals)) {
      return res.status(400).json({ 
        error: 'employeeId and signals array are required' 
      });
    }

    // Process each signal
    let processed = 0;
    for (const signal of signals) {
      try {
        switch (signal.type) {
          case 'window_focus':
            emsSignals.captureWindowFocus(employeeId, signal.value, signal.metadata);
            break;
          
          case 'keystroke':
          case 'keystroke_rate':
            emsSignals.captureKeystroke(employeeId, signal.metadata);
            break;
          
          case 'mouse_movement':
            emsSignals.captureMouseMovement(employeeId, signal.metadata);
            break;
          
          case 'scroll_depth':
            emsSignals.captureScrollDepth(employeeId, signal.metadata);
            break;
          
          case 'task_tab_active':
            emsSignals.captureTaskTabActive(employeeId, signal.metadata);
            break;
          
          case 'app_switch':
            emsSignals.captureAppSwitch(employeeId, signal.metadata);
            break;
          
          case 'browser_hidden':
            emsSignals.captureBrowserHidden(employeeId, signal.value, signal.metadata);
            break;
          
          default:
            console.warn(`Unknown signal type: ${signal.type}`);
        }
        processed++;
      } catch (err) {
        console.error(`Error processing signal ${signal.type}:`, err);
      }
    }

    // Get current state
    const currentState = emsSignals.getSignalState(employeeId);

    res.json({
      success: true,
      received: signals.length,
      processed: processed,
      employeeId,
      currentState: currentState?.currentState,
      statistics: currentState?.statistics,
      timestamp: new Date()
    });

  } catch (error) {
    console.error('Error processing signals:', error);
    res.status(500).json({ error: 'Failed to process signals' });
  }
});

// Receive individual signal (real-time)
router.post('/signals/realtime', async (req, res) => {
  try {
    const { employeeId, type, value, metadata } = req.body;

    if (!employeeId || !type) {
      return res.status(400).json({ 
        error: 'employeeId and type are required' 
      });
    }

    // Process signal immediately
    switch (type) {
      case 'window_focus':
        emsSignals.captureWindowFocus(employeeId, value, metadata);
        break;
      
      case 'keystroke':
        emsSignals.captureKeystroke(employeeId, metadata);
        break;
      
      case 'mouse_movement':
        emsSignals.captureMouseMovement(employeeId, metadata);
        break;
      
      case 'scroll_depth':
        emsSignals.captureScrollDepth(employeeId, metadata);
        break;
      
      case 'task_tab_active':
        emsSignals.captureTaskTabActive(employeeId, metadata);
        break;
      
      case 'app_switch':
        emsSignals.captureAppSwitch(employeeId, metadata);
        break;
      
      case 'browser_hidden':
        emsSignals.captureBrowserHidden(employeeId, value, metadata);
        break;
      
      default:
        return res.status(400).json({ error: `Unknown signal type: ${type}` });
    }

    res.json({
      success: true,
      type,
      timestamp: new Date()
    });

  } catch (error) {
    console.error('Error processing real-time signal:', error);
    res.status(500).json({ error: 'Failed to process signal' });
  }
});

// Get signal state for employee
router.get('/signals/:employeeId', async (req, res) => {
  try {
    const { employeeId } = req.params;
    
    const state = emsSignals.getSignalState(employeeId);
    
    if (!state) {
      return res.status(404).json({ 
        error: 'Employee not found or not being tracked' 
      });
    }

    res.json(state);
  } catch (error) {
    console.error('Error fetching signal state:', error);
    res.status(500).json({ error: 'Failed to fetch signal state' });
  }
});

// Get signals in time range
router.get('/signals/:employeeId/history', async (req, res) => {
  try {
    const { employeeId } = req.params;
    const { startTime, endTime } = req.query;

    const start = startTime ? parseInt(startTime) : Date.now() - 3600000; // Last hour
    const end = endTime ? parseInt(endTime) : Date.now();

    const signals = emsSignals.getSignals(employeeId, start, end);

    res.json({
      employeeId,
      timeRange: { startTime: start, endTime: end },
      signals,
      count: signals.length
    });
  } catch (error) {
    console.error('Error fetching signal history:', error);
    res.status(500).json({ error: 'Failed to fetch signal history' });
  }
});

// Get live capture proof (for testing)
router.get('/signals/:employeeId/proof', async (req, res) => {
  try {
    const { employeeId } = req.params;
    
    const proof = emsSignals.getLiveCaptureProof(employeeId);
    
    if (!proof) {
      return res.status(404).json({ 
        error: 'Employee not found or not being tracked' 
      });
    }

    res.json(proof);
  } catch (error) {
    console.error('Error generating proof:', error);
    res.status(500).json({ error: 'Failed to generate proof' });
  }
});

// Stop tracking employee
router.post('/signals/:employeeId/stop', async (req, res) => {
  try {
    const { employeeId } = req.params;
    
    emsSignals.stopTracking(employeeId);

    res.json({
      success: true,
      message: 'Signal tracking stopped',
      employeeId,
      timestamp: new Date()
    });
  } catch (error) {
    console.error('Error stopping tracking:', error);
    res.status(500).json({ error: 'Failed to stop tracking' });
  }
});

// Clear employee signals
router.delete('/signals/:employeeId', async (req, res) => {
  try {
    const { employeeId } = req.params;
    
    emsSignals.clearEmployeeSignals(employeeId);

    res.json({
      success: true,
      message: 'Signals cleared',
      employeeId,
      timestamp: new Date()
    });
  } catch (error) {
    console.error('Error clearing signals:', error);
    res.status(500).json({ error: 'Failed to clear signals' });
  }
});

module.exports = router;
