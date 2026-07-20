import express from 'express';
import auditController from '../controllers/audit.controller.js';
import { protect, authorize } from '../middleware/auth.js';

const router = express.Router();

router.use(protect);

router.get('/trail/:entityType/:entityId', auditController.getEntityAuditTrail);
router.get('/summary', auditController.getAuditSummary);
router.get('/verify-chain', auditController.verifyAuditChain);
router.get('/export', auditController.exportAuditTrail);

export default router;
