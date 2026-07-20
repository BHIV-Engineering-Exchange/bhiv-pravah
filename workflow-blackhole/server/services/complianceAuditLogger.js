const crypto = require('crypto');
const ComplianceAuditLog = require('../models/ComplianceAuditLog');

const uuidv4 = () => crypto.randomUUID();

class ComplianceAuditLogger {
  constructor() {
    console.log('Initialized ComplianceAuditLogger');
  }

  computeHash(prevHash, entry) {
    const hasher = crypto.createHash('sha256');
    if (prevHash) {
      hasher.update(prevHash);
    }
    hasher.update(JSON.stringify(entry, Object.keys(entry).sort()));
    return hasher.digest('hex');
  }

  async getLastHash() {
    try {
      const lastEntry = await ComplianceAuditLog.findOne()
        .sort({ timestamp: -1 })
        .select('hash');
      
      return lastEntry ? lastEntry.hash : null;
    } catch (error) {
      console.error('Error getting last hash:', error);
      return null;
    }
  }

  async logEvent(userId, action, resource, details = {}, status = 'success') {
    try {
      const eventId = uuidv4();
      const timestamp = new Date();

      const logEntry = {
        eventId,
        timestamp,
        userId,
        action,
        resource,
        status,
        details,
        ipAddress: details.ip_address || null,
        userAgent: details.user_agent || null
      };

      // Get previous hash for chaining
      const prevHash = await this.getLastHash();
      logEntry.prevHash = prevHash;
      logEntry.hash = this.computeHash(prevHash, logEntry);

      // Save to database
      const auditLog = new ComplianceAuditLog(logEntry);
      await auditLog.save();

      console.log(`Audit log entry created: ${eventId}`);
      return eventId;
    } catch (error) {
      console.error('Failed to write audit log:', error);
      throw error;
    }
  }

  async logAccess(actor, action, resource, status = 'success', reason = null, purpose = null, viaEndpoint = null, ipAddress = null, userAgent = null, extra = {}) {
    const details = {
      reason,
      purpose,
      via_endpoint: viaEndpoint,
      ...extra
    };

    if (ipAddress) details.ip_address = ipAddress;
    if (userAgent) details.user_agent = userAgent;

    return await this.logEvent(actor, action, resource, details, status);
  }

  async getLogs(startDate = null, endDate = null, userId = null, action = null, limit = 100) {
    try {
      const query = {};

      // Date range filter
      if (startDate || endDate) {
        query.timestamp = {};
        if (startDate) {
          query.timestamp.$gte = new Date(startDate);
        }
        if (endDate) {
          query.timestamp.$lte = new Date(endDate);
        }
      }

      // User filter
      if (userId) {
        query.userId = userId;
      }

      // Action filter
      if (action) {
        query.action = action;
      }

      const logs = await ComplianceAuditLog.find(query)
        .sort({ timestamp: -1 })
        .limit(limit)
        .lean();

      return logs.map(log => ({
        event_id: log.eventId,
        timestamp: log.timestamp.toISOString(),
        user_id: log.userId,
        action: log.action,
        resource: log.resource,
        status: log.status,
        details: log.details,
        ip_address: log.ipAddress,
        user_agent: log.userAgent,
        prev_hash: log.prevHash,
        hash: log.hash
      }));
    } catch (error) {
      console.error('Error getting logs:', error);
      throw error;
    }
  }

  async applyRetentionPolicy(retentionDays = 90) {
    try {
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - retentionDays);

      // Log the retention policy application
      await this.logEvent(
        'system',
        'apply_retention_policy',
        'audit_logs',
        { 
          reason: 'retention_policy', 
          retention_days: retentionDays,
          cutoff_date: cutoffDate.toISOString()
        }
      );

      // Delete old logs
      const result = await ComplianceAuditLog.deleteMany({
        timestamp: { $lt: cutoffDate }
      });

      console.log(`Deleted ${result.deletedCount} old audit log entries`);
      return { success: true, logs_deleted: result.deletedCount };
    } catch (error) {
      console.error('Error applying retention policy:', error);
      throw error;
    }
  }
}

const auditLogger = new ComplianceAuditLogger();

module.exports = { ComplianceAuditLogger, auditLogger };