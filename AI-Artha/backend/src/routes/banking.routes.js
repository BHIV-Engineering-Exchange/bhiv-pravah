import express from 'express';
import bankingController from '../controllers/banking.controller.js';
import { protect, authorize } from '../middleware/auth.js';

const router = express.Router();

router.use(protect);

router.post('/payments', bankingController.initiatePayment);
router.get('/payments', bankingController.getPayments);
router.get('/payments/:id', bankingController.getPaymentStatus);
router.post('/payments/:id/process', bankingController.processPayment);
router.post('/payments/:id/retry', bankingController.retryPayment);
router.post('/payments/:id/reverse', bankingController.reversePayment);
router.post('/payments/recover-failed', bankingController.recoverFailedPayments);

router.post('/statements/:id/auto-match', bankingController.autoMatchTransactions);
router.post('/statements/:id/reconcile', bankingController.reconcileBankStatement);

export default router;
