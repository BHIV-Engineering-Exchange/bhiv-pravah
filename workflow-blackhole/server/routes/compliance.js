const express = require('express');
const router = express.Router();
const consentManager = require('../services/consentManager');
const { auditLogger } = require('../services/complianceAuditLogger');
const { verifyComplianceApiKey, logComplianceAccess } = require('../middleware/complianceAuth');

// Apply middleware to all compliance routes
router.use(verifyComplianceApiKey);
router.use(logComplianceAccess);

// Set consent preferences
router.post('/consent', async (req, res) => {
  try {
    const { employee_id, monitoring_enabled, retention_days, data_categories } = req.body;
    const requesterId = req.complianceUser.id;

    if (!employee_id || typeof monitoring_enabled !== 'boolean') {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'employee_id and monitoring_enabled are required'
      });
    }

    const result = await consentManager.setConsent(
      employee_id,
      monitoring_enabled,
      retention_days,
      data_categories,
      requesterId
    );

    // Additional API-specific logging
    await auditLogger.logEvent(
      requesterId,
      'api_set_consent',
      `employee/${employee_id}/consent`,
      {
        ip_address: req.complianceUser.ipAddress,
        user_agent: req.complianceUser.userAgent,
        request_data: req.body
      }
    );

    res.json({
      ...result,
      status: 'success'
    });
  } catch (error) {
    console.error('Error setting consent:', error);
    res.status(500).json({
      error: 'Failed to set consent',
      message: error.message
    });
  }
});

// Get consent for specific employee
router.get('/consent/:employee_id', async (req, res) => {
  try {
    const { employee_id } = req.params;
    const requesterId = req.complianceUser.id;

    const result = await consentManager.getConsent(employee_id);

    if (!result) {
      return res.status(404).json({
        error: 'Not found',
        message: `No consent record found for employee ${employee_id}`
      });
    }

    // Log access to consent data
    await auditLogger.logEvent(
      requesterId,
      'api_get_consent',
      `employee/${employee_id}/consent`,
      {
        ip_address: req.complianceUser.ipAddress,
        user_agent: req.complianceUser.userAgent
      }
    );

    res.json({
      ...result,
      status: 'success'
    });
  } catch (error) {
    console.error('Error getting consent:', error);
    res.status(500).json({
      error: 'Failed to get consent',
      message: error.message
    });
  }
});

// List all consents
router.get('/consent', async (req, res) => {
  try {
    const activeOnly = req.query.active_only !== 'false';
    const requesterId = req.complianceUser.id;

    const results = await consentManager.getAllConsents(activeOnly);

    // Log access to consent list
    await auditLogger.logEvent(
      requesterId,
      'api_list_consents',
      'employee/consent',
      {
        ip_address: req.complianceUser.ipAddress,
        user_agent: req.complianceUser.userAgent,
        active_only: activeOnly,
        count: results.length
      }
    );

    // Add status to each result
    const resultsWithStatus = results.map(result => ({
      ...result,
      status: 'success'
    }));

    res.json(resultsWithStatus);
  } catch (error) {
    console.error('Error listing consents:', error);
    res.status(500).json({
      error: 'Failed to list consents',
      message: error.message
    });
  }
});

// Get audit logs
router.post('/audit-logs', async (req, res) => {
  try {
    const { start_date, end_date, user_id, action, limit = 100 } = req.body;
    const requesterId = req.complianceUser.id;

    const logs = await auditLogger.getLogs(start_date, end_date, user_id, action, limit);

    // Log access to audit logs
    await auditLogger.logEvent(
      requesterId,
      'api_get_audit_logs',
      'audit_logs',
      {
        ip_address: req.complianceUser.ipAddress,
        user_agent: req.complianceUser.userAgent,
        filters: req.body,
        results_count: logs.length
      }
    );

    res.json(logs);
  } catch (error) {
    console.error('Error getting audit logs:', error);
    res.status(500).json({
      error: 'Failed to get audit logs',
      message: error.message
    });
  }
});

// Apply retention policy
router.post('/apply-retention', async (req, res) => {
  try {
    const requesterId = req.complianceUser.id;
    const retentionDays = parseInt(process.env.AUDIT_LOG_RETENTION_DAYS) || 90;

    // Apply retention policies
    const consentDeleted = await consentManager.applyRetentionPolicy();
    const logsResult = await auditLogger.applyRetentionPolicy(retentionDays);
    const logsDeleted = logsResult.logs_deleted || 0;

    // Log retention policy application
    await auditLogger.logAccess(
      requesterId,
      'apply_retention_policy',
      'system',
      'success',
      'scheduled_or_manual',
      'retention_enforcement',
      '/compliance/apply-retention',
      req.complianceUser.ipAddress,
      req.complianceUser.userAgent,
      {
        consent_records_deleted: consentDeleted,
        log_files_deleted: logsDeleted,
        retention_days: retentionDays
      }
    );

    res.json({
      status: 'success',
      consent_records_deleted: consentDeleted,
      log_files_deleted: logsDeleted,
      retention_days: retentionDays
    });
  } catch (error) {
    console.error('Error applying retention policy:', error);
    res.status(500).json({
      error: 'Failed to apply retention policy',
      message: error.message
    });
  }
});

// EMS event forwarding
router.post('/ems-forward', async (req, res) => {
  try {
    const {
      actor,
      action,
      resource,
      status = 'success',
      reason,
      purpose,
      ems_trace_id,
      ems_source,
      details
    } = req.body;

    if (!actor || !action || !resource) {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'actor, action, and resource are required'
      });
    }

    await auditLogger.logAccess(
      actor,
      action,
      resource,
      status,
      reason,
      purpose,
      '/compliance/ems-forward',
      req.complianceUser.ipAddress,
      req.complianceUser.userAgent,
      {
        ems_trace_id,
        ems_source,
        details: details || {}
      }
    );

    res.json({
      status: 'ok',
      ingested: true
    });
  } catch (error) {
    console.error('EMS forward error:', error);
    res.status(500).json({
      error: 'Failed to ingest EMS event',
      message: error.message
    });
  }
});

// Health check
router.get('/health', async (req, res) => {
  try {
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      components: {
        consent_manager: 'operational',
        audit_logger: 'operational'
      }
    });
  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

module.exports = router;