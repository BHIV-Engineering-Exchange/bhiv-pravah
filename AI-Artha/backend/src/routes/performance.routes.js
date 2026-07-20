import express from 'express';
import {
  getMetrics,
  getHealthStatus,
  resetMetrics,
} from '../controllers/performance.controller.js';
import { protect, authorize } from '../middleware/auth.js';
import { auditLogger } from '../middleware/security.js';

const router = express.Router();

// All routes require authentication and admin role
router.use(protect);
router.use(authorize('admin'));

// Routes
router.route('/metrics').get(getMetrics);

router.route('/health').get(getHealthStatus);

router
  .route('/reset')
  .post(
    auditLogger('performance.metrics_reset', 'System'),
    resetMetrics
  );

export default router;