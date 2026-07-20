import express from 'express';
import {
  logExperience,
  getExperiences,
  getExperienceStats,
} from '../controllers/insightflow.controller.js';
import { protect, authorize } from '../middleware/auth.js';

const router = express.Router();

// All routes require authentication
router.use(protect);

// Routes
router.route('/experience').post(logExperience);

router.route('/experiences').get(authorize('admin'), getExperiences);

router.route('/stats').get(authorize('admin'), getExperienceStats);

export default router;