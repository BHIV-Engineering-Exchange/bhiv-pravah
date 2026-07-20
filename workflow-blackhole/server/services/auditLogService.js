
const AuditLog = require('../models/AuditLog');

class AuditLogService {
  async log(user, action, resource, resourceId) {
    try {
      const logEntry = new AuditLog({
        user,
        action,
        resource,
        resourceId,
      });
      await logEntry.save();
    } catch (error) {
      console.error('Error logging audit event:', error);
    }
  }
}

module.exports = new AuditLogService();
