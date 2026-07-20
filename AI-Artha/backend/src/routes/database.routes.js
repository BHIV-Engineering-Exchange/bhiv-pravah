import express from 'express';
import {
  getDatabaseStats,
  getCollectionStats,
  getIndexInfo,
  getOptimizationSuggestions,
  createIndexes,
} from '../controllers/database.controller.js';
import { protect, authorize } from '../middleware/auth.js';
import { auditLogger } from '../middleware/security.js';

const router = express.Router();

// All routes require authentication and admin role
router.use(protect);
router.use(authorize('admin'));

// Routes
router.route('/stats').get(getDatabaseStats);

router.route('/collections').get(getCollectionStats);

router.route('/indexes')
  .get(getIndexInfo)
  .post(
    auditLogger('database.indexes_created', 'System'),
    createIndexes
  );

router.route('/optimize').get(getOptimizationSuggestions);

export default router;