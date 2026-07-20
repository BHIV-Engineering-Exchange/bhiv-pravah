import tantraService from '../services/tantra.service.js';
import observabilityService from '../services/observability.service.js';
import evidenceAutomationService from '../services/evidenceAutomation.service.js';
import logger from '../config/logger.js';

class TantraController {
  async register(req, res) {
    try {
      const registration = await tantraService.register(req.body);
      res.json({ success: true, data: registration });
    } catch (err) {
      res.status(400).json({ success: false, message: err.message });
    }
  }

  async heartbeat(req, res) {
    try {
      const status = await tantraService.heartbeat();
      res.json({ success: true, data: status });
    } catch (err) {
      res.status(500).json({ success: false, message: err.message });
    }
  }

  async emitEvent(req, res) {
    try {
      const event = await tantraService.emitEvent(req.body);
      res.json({ success: true, data: event });
    } catch (err) {
      res.status(400).json({ success: false, message: err.message });
    }
  }

  async getOperationalMetadata(req, res) {
    try {
      const metadata = await tantraService.getOperationalMetadata();
      res.json({ success: true, data: metadata });
    } catch (err) {
      res.status(500).json({ success: false, message: err.message });
    }
  }

  async getSystemHealth(req, res) {
    try {
      const health = await observabilityService.getSystemHealth();
      res.status(health.status === 'healthy' ? 200 : 503).json({ success: health.status === 'healthy', data: health });
    } catch (err) {
      res.status(500).json({ success: false, message: err.message });
    }
  }

  async getMetrics(req, res) {
    try {
      const metrics = observabilityService.getMetrics();
      res.json({ success: true, data: metrics });
    } catch (err) {
      res.status(500).json({ success: false, message: err.message });
    }
  }

  async getDashboardData(req, res) {
    try {
      const data = await observabilityService.getDashboardData();
      res.json({ success: true, data });
    } catch (err) {
      res.status(500).json({ success: false, message: err.message });
    }
  }

  async getEvidenceByTrace(req, res) {
    try {
      const evidence = await evidenceAutomationService.getEvidenceByTrace(req.params.traceId);
      res.json({ success: true, data: evidence });
    } catch (err) {
      res.status(500).json({ success: false, message: err.message });
    }
  }

  async getEvidenceSummary(req, res) {
    try {
      const summary = await evidenceAutomationService.getEvidenceSummary(req.query);
      res.json({ success: true, data: summary });
    } catch (err) {
      res.status(500).json({ success: false, message: err.message });
    }
  }
}

export default new TantraController();
