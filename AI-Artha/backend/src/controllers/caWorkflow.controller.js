import caWorkflowService from '../services/caWorkflow.service.js';
import logger from '../config/logger.js';

class CAWorkflowController {
  async getPeriods(req, res) {
    try {
      const periods = await caWorkflowService.getPeriods(req.query);
      res.json({ success: true, data: periods });
    } catch (err) {
      res.status(500).json({ success: false, message: err.message });
    }
  }

  async getOrCreatePeriod(req, res) {
    try {
      const period = await caWorkflowService.getOrCreatePeriod(req.body);
      res.json({ success: true, data: period });
    } catch (err) {
      res.status(400).json({ success: false, message: err.message });
    }
  }

  async monthClose(req, res) {
    try {
      const period = await caWorkflowService.monthClose(req.params.periodId, req.user._id);
      res.json({ success: true, data: period, message: 'Month closed successfully' });
    } catch (err) {
      logger.error('Month close error:', err);
      res.status(400).json({ success: false, message: err.message });
    }
  }

  async quarterClose(req, res) {
    try {
      const period = await caWorkflowService.quarterClose(req.params.periodId, req.user._id);
      res.json({ success: true, data: period, message: 'Quarter closed successfully' });
    } catch (err) {
      logger.error('Quarter close error:', err);
      res.status(400).json({ success: false, message: err.message });
    }
  }

  async annualClose(req, res) {
    try {
      const period = await caWorkflowService.annualClose(req.params.periodId, req.user._id);
      res.json({ success: true, data: period, message: 'Annual close completed' });
    } catch (err) {
      logger.error('Annual close error:', err);
      res.status(400).json({ success: false, message: err.message });
    }
  }

  async generateTrialBalance(req, res) {
    try {
      const trialBalance = await caWorkflowService.generateTrialBalance(req.params.periodId);
      res.json({ success: true, data: trialBalance });
    } catch (err) {
      res.status(400).json({ success: false, message: err.message });
    }
  }
}

export default new CAWorkflowController();
