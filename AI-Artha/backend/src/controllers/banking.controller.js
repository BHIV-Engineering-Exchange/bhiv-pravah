import bankingService from '../services/banking.service.js';
import logger from '../config/logger.js';

class BankingController {
  async initiatePayment(req, res) {
    try {
      const payment = await bankingService.initiatePayment({
        ...req.body,
        traceId: req.traceId,
      }, req.user._id);
      res.status(201).json({ success: true, data: payment });
    } catch (err) {
      logger.error('Initiate payment error:', err);
      res.status(400).json({ success: false, message: err.message });
    }
  }

  async processPayment(req, res) {
    try {
      const payment = await bankingService.processPayment(req.params.id, req.body, req.user._id);
      res.json({ success: true, data: payment });
    } catch (err) {
      logger.error('Process payment error:', err);
      res.status(400).json({ success: false, message: err.message });
    }
  }

  async retryPayment(req, res) {
    try {
      const payment = await bankingService.retryPayment(req.params.id, req.user._id);
      res.json({ success: true, data: payment });
    } catch (err) {
      logger.error('Retry payment error:', err);
      res.status(400).json({ success: false, message: err.message });
    }
  }

  async reversePayment(req, res) {
    try {
      const payment = await bankingService.reversePayment(req.params.id, req.body.reason, req.user._id);
      res.json({ success: true, data: payment });
    } catch (err) {
      logger.error('Reverse payment error:', err);
      res.status(400).json({ success: false, message: err.message });
    }
  }

  async getPaymentStatus(req, res) {
    try {
      const payment = await bankingService.getPaymentStatus(req.params.id);
      res.json({ success: true, data: payment });
    } catch (err) {
      res.status(404).json({ success: false, message: err.message });
    }
  }

  async getPayments(req, res) {
    try {
      const result = await bankingService.getPayments(req.query, {
        page: parseInt(req.query.page) || 1,
        limit: parseInt(req.query.limit) || 20,
      });
      res.json({ success: true, data: result });
    } catch (err) {
      res.status(500).json({ success: false, message: err.message });
    }
  }

  async autoMatchTransactions(req, res) {
    try {
      const matches = await bankingService.autoMatchTransactions(req.params.id, req.user._id);
      res.json({ success: true, data: matches });
    } catch (err) {
      res.status(400).json({ success: false, message: err.message });
    }
  }

  async reconcileBankStatement(req, res) {
    try {
      const result = await bankingService.reconcileBankStatement(req.params.id, req.body.matches, req.user._id);
      res.json({ success: true, data: result });
    } catch (err) {
      res.status(400).json({ success: false, message: err.message });
    }
  }

  async recoverFailedPayments(req, res) {
    try {
      const results = await bankingService.recoverFailedPayments();
      res.json({ success: true, data: results });
    } catch (err) {
      res.status(500).json({ success: false, message: err.message });
    }
  }
}

export default new BankingController();
