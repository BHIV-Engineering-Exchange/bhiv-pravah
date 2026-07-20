import express from 'express';
import tantraController from '../controllers/tantra.controller.js';
import tantraExecutionChain from '../services/tantraExecutionChain.service.js';
import { protect } from '../middleware/auth.js';
import logger from '../config/logger.js';

const router = express.Router();

// Public endpoints
router.post('/register', tantraController.register);
router.post('/heartbeat', tantraController.heartbeat);
router.get('/health', tantraController.getSystemHealth);
router.get('/metrics', tantraController.getMetrics);

// Protected endpoints
router.use(protect);

router.post('/events', tantraController.emitEvent);
router.get('/metadata', tantraController.getOperationalMetadata);
router.get('/dashboard', tantraController.getDashboardData);
router.get('/evidence/:traceId', tantraController.getEvidenceByTrace);
router.get('/evidence', tantraController.getEvidenceSummary);

// ─── TANTRA Execution Chain ──────────────────────────────────────────────

router.post('/chain/execute', async (req, res) => {
  try {
    const result = await tantraExecutionChain.executeChain(req.body);
    res.json({ success: true, data: result });
  } catch (err) {
    logger.error('TANTRA chain execute error:', err);
    res.status(500).json({ success: false, message: err.message });
  }
});

router.get('/chain/:chainId', (req, res) => {
  try {
    const chain = tantraExecutionChain.getChain(req.params.chainId);
    if (!chain) {
      return res.status(404).json({ success: false, message: 'Chain not found' });
    }
    res.json({ success: true, data: chain });
  } catch (err) {
    logger.error('TANTRA chain get error:', err);
    res.status(500).json({ success: false, message: err.message });
  }
});

router.get('/chain/trace/:traceId', (req, res) => {
  try {
    const chains = tantraExecutionChain.getChainsByTrace(req.params.traceId);
    res.json({ success: true, data: chains });
  } catch (err) {
    logger.error('TANTRA chain trace error:', err);
    res.status(500).json({ success: false, message: err.message });
  }
});

router.get('/chain/stats', (req, res) => {
  try {
    const stats = tantraExecutionChain.getChainStats();
    res.json({ success: true, data: stats });
  } catch (err) {
    logger.error('TANTRA chain stats error:', err);
    res.status(500).json({ success: false, message: err.message });
  }
});

export default router;
