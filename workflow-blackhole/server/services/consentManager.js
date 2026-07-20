const Consent = require('../models/Consent');
const { auditLogger } = require('./complianceAuditLogger');

class ConsentManager {
  constructor() {
    this.defaultRetentionDays = 90;
  }

  async setConsent(employeeId, monitoringEnabled, retentionDays = null, dataCategories = null, requesterId = 'system') {
    try {
      const retention = retentionDays || this.defaultRetentionDays;
      const expirationDate = new Date();
      expirationDate.setDate(expirationDate.getDate() + retention);

      const consentData = {
        employeeId,
        monitoringEnabled,
        retentionDays: retention,
        dataCategories: dataCategories || ['all'],
        expirationDate,
        lastUpdatedBy: requesterId,
        isActive: true
      };

      // Upsert consent record
      const consent = await Consent.findOneAndUpdate(
        { employeeId },
        consentData,
        { upsert: true, new: true, runValidators: true }
      );

      // Log the consent change
      await auditLogger.logEvent(
        requesterId,
        'set_consent',
        `employee/${employeeId}/consent`,
        {
          monitoringEnabled,
          retentionDays: retention,
          dataCategories: dataCategories || ['all']
        }
      );

      return {
        employee_id: consent.employeeId,
        monitoring_enabled: consent.monitoringEnabled,
        retention_days: consent.retentionDays,
        expiration_date: consent.expirationDate.toISOString(),
        data_categories: consent.dataCategories,
        last_updated: consent.lastUpdated.toISOString(),
        success: true
      };
    } catch (error) {
      console.error('Error setting consent:', error);
      throw error;
    }
  }

  async getConsent(employeeId) {
    try {
      const consent = await Consent.findOne({ 
        employeeId, 
        isActive: true 
      });

      if (!consent) {
        return null;
      }

      // Log consent access
      await auditLogger.logEvent(
        'system',
        'access_consent',
        `employee/${employeeId}/consent`,
        { accessType: 'read' }
      );

      return {
        employee_id: consent.employeeId,
        monitoring_enabled: consent.monitoringEnabled,
        retention_days: consent.retentionDays,
        expiration_date: consent.expirationDate.toISOString(),
        data_categories: consent.dataCategories,
        last_updated: consent.lastUpdated.toISOString()
      };
    } catch (error) {
      console.error('Error getting consent:', error);
      throw error;
    }
  }

  async isMonitoringAllowed(employeeId) {
    try {
      const consent = await this.getConsent(employeeId);
      
      if (!consent) {
        return false;
      }

      // Check if consent has expired
      const expirationDate = new Date(consent.expiration_date);
      if (new Date() > expirationDate) {
        console.warn(`Consent for employee ${employeeId} has expired`);
        return false;
      }

      return consent.monitoring_enabled;
    } catch (error) {
      console.error('Error checking monitoring permission:', error);
      return false;
    }
  }

  async getAllConsents(activeOnly = true) {
    try {
      const query = activeOnly ? { isActive: true } : {};
      
      if (activeOnly) {
        // Also filter by expiration date
        query.expirationDate = { $gt: new Date() };
      }

      const consents = await Consent.find(query).sort({ lastUpdated: -1 });

      return consents.map(consent => ({
        employee_id: consent.employeeId,
        monitoring_enabled: consent.monitoringEnabled,
        retention_days: consent.retentionDays,
        expiration_date: consent.expirationDate.toISOString(),
        data_categories: consent.dataCategories,
        last_updated: consent.lastUpdated.toISOString()
      }));
    } catch (error) {
      console.error('Error getting all consents:', error);
      throw error;
    }
  }

  async applyRetentionPolicy() {
    try {
      const now = new Date();
      
      // Find expired consents
      const expiredConsents = await Consent.find({
        expirationDate: { $lt: now },
        isActive: true
      });

      let deletedCount = 0;

      for (const consent of expiredConsents) {
        // Log the deletion
        await auditLogger.logEvent(
          'system',
          'delete_consent',
          `employee/${consent.employeeId}/consent`,
          { reason: 'retention_policy_expired' }
        );

        // Mark as inactive instead of deleting for audit purposes
        await Consent.findByIdAndUpdate(consent._id, { isActive: false });
        deletedCount++;
      }

      console.log(`Applied retention policy: ${deletedCount} consent records expired`);
      return deletedCount;
    } catch (error) {
      console.error('Error applying retention policy:', error);
      throw error;
    }
  }
}

module.exports = new ConsentManager();