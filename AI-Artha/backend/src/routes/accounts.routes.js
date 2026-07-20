import express from 'express';
import { body } from 'express-validator';
import {
  getAccounts,
  getAccount,
  createAccount,
  updateAccount,
  deactivateAccount,
  seedAccounts,
} from '../controllers/accounts.controller.js';
import { protect, authorize } from '../middleware/auth.js';
import { validate, auditLogger } from '../middleware/security.js';
import { cacheMiddleware } from '../middleware/cache.js';

const router = express.Router();

// Validation rules
const accountValidation = [
  body('code').trim().notEmpty().withMessage('Account code is required'),
  body('name').trim().notEmpty().withMessage('Account name is required'),
  body('type').isIn(['Asset', 'Liability', 'Equity', 'Income', 'Expense']).withMessage('Invalid account type'),
  body('normalBalance').isIn(['debit', 'credit']).withMessage('Normal balance must be debit or credit'),
];

// All routes require authentication
router.use(protect);

// Routes
router
  .route('/')
  .get(getAccounts)
  .post(
    authorize('admin', 'accountant'),
    accountValidation,
    validate,
    auditLogger('account.create', 'ChartOfAccounts'),
    createAccount
  );

// Seed route must come before /:id to avoid conflicts
router
  .route('/seed')
  .post(
    authorize('admin'),
    auditLogger('accounts.seed', 'ChartOfAccounts'),
    seedAccounts
  );

router
  .route('/:id')
  .get(cacheMiddleware(1800), getAccount)
  .put(
    authorize('admin', 'accountant'),
    accountValidation,
    validate,
    auditLogger('account.update', 'ChartOfAccounts'),
    updateAccount
  )
  .delete(
    authorize('admin'),
    auditLogger('account.deactivate', 'ChartOfAccounts'),
    deactivateAccount
  );







export default router;