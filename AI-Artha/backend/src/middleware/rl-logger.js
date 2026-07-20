import insightflowService from '../services/insightflow.service.js';
import logger from '../config/logger.js';
import crypto from 'crypto';

/**
 * Middleware to automatically log RL experiences
 */
export const rlLogger = (action, getState = null, getNextState = null) => {
  return async (req, res, next) => {
    const startTime = Date.now();
    
    // Generate session ID if not present
    if (!req.sessionId) {
      req.sessionId = req.headers['x-session-id'] || 
                     `session-${Date.now()}-${crypto.randomBytes(4).toString('hex')}`;
    }
    
    // Capture initial state
    const initialState = getState ? getState(req) : {
      method: req.method,
      path: req.path,
      userRole: req.user?.role,
      timestamp: new Date().toISOString(),
    };
    
    // Store original json method
    const originalJson = res.json.bind(res);
    
    res.json = function(data) {
      const endTime = Date.now();
      const duration = endTime - startTime;
      
      // Capture next state
      const nextState = getNextState ? getNextState(req, res, data) : {
        success: data.success,
        statusCode: res.statusCode,
        hasData: !!data.data,
        timestamp: new Date().toISOString(),
      };
      
      // Calculate reward
      const outcome = {
        errorOccurred: !data.success,
        duration,
        statusCode: res.statusCode,
      };
      
      const reward = insightflowService.calculateReward(action, outcome);
      
      // Log experience asynchronously (don't block response)
      if (req.user) {
        insightflowService.logExperience({
          sessionId: req.sessionId,
          userId: req.user._id,
          state: initialState,
          action,
          reward,
          nextState,
          isTerminal: res.statusCode >= 400 || action.includes('complete'),
          metadata: {
            duration,
            errorOccurred: !data.success,
            errorType: data.success ? null : data.message,
            userRole: req.user.role,
            timestamp: new Date(),
          },
        }).catch(err => {
          logger.warn('Failed to log RL experience:', err.message);
        });
      }
      
      return originalJson(data);
    };
    
    next();
  };
};

/**
 * State extractors for common scenarios
 */
export const stateExtractors = {
  invoice: {
    create: (req) => ({
      screen: 'invoice_create',
      hasCustomer: !!req.body.customerName,
      hasItems: !!(req.body.items || req.body.lines),
      itemCount: (req.body.items || req.body.lines || []).length,
      totalAmount: req.body.totalAmount,
    }),
    
    send: (req) => ({
      screen: 'invoice_send',
      invoiceId: req.params.id,
      action: 'send_invoice',
    }),
    
    payment: (req) => ({
      screen: 'invoice_payment',
      invoiceId: req.params.id,
      paymentAmount: req.body.amount,
      paymentMethod: req.body.paymentMethod,
    }),
  },
  
  expense: {
    create: (req) => ({
      screen: 'expense_create',
      hasVendor: !!req.body.vendor,
      category: req.body.category,
      amount: req.body.amount,
      hasReceipts: !!(req.files && req.files.length > 0),
      receiptCount: req.files ? req.files.length : 0,
    }),
    
    approve: (req) => ({
      screen: 'expense_approve',
      expenseId: req.params.id,
      action: 'approve_expense',
    }),
    
    record: (req) => ({
      screen: 'expense_record',
      expenseId: req.params.id,
      action: 'record_expense',
    }),
  },
  
  ledger: {
    create: (req) => ({
      screen: 'ledger_create',
      hasDescription: !!req.body.description,
      lineCount: (req.body.lines || []).length,
      totalDebit: (req.body.lines || []).reduce((sum, line) => 
        sum + parseFloat(line.debit || 0), 0),
      totalCredit: (req.body.lines || []).reduce((sum, line) => 
        sum + parseFloat(line.credit || 0), 0),
    }),
    
    post: (req) => ({
      screen: 'ledger_post',
      entryId: req.params.id,
      action: 'post_entry',
    }),
  },
};

/**
 * Next state extractors
 */
export const nextStateExtractors = {
  success: (req, res, data) => ({
    success: true,
    entityId: data.data?._id,
    entityType: data.data?.constructor?.modelName,
    statusCode: res.statusCode,
    timestamp: new Date().toISOString(),
  }),
  
  error: (req, res, data) => ({
    success: false,
    errorMessage: data.message,
    statusCode: res.statusCode,
    timestamp: new Date().toISOString(),
  }),
};