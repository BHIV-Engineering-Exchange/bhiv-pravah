import express from 'express';
import caWorkflowController from '../controllers/caWorkflow.controller.js';
import { protect, authorize } from '../middleware/auth.js';

const router = express.Router();

router.use(protect);

router.get('/periods', caWorkflowController.getPeriods);
router.post('/periods', caWorkflowController.getOrCreatePeriod);
router.post('/periods/:periodId/month-close', caWorkflowController.monthClose);
router.post('/periods/:periodId/quarter-close', caWorkflowController.quarterClose);
router.post('/periods/:periodId/annual-close', caWorkflowController.annualClose);
router.get('/periods/:periodId/trial-balance', caWorkflowController.generateTrialBalance);

export default router;
