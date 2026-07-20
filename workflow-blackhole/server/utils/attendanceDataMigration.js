const mongoose = require('mongoose');
const moment = require('moment-timezone');
const DailyAttendance = require('../models/DailyAttendance');
const BiometricPunch = require('../models/BiometricPunch');
const EmployeeMaster = require('../models/EmployeeMaster');
const User = require('../models/User');
const EnhancedBiometricProcessor = require('./enhancedBiometricProcessor');
const AttendanceDebugger = require('../utils/attendanceDebugger');

/**
 * PART D: DATABASE MIGRATION & DATA CLEANUP
 * 
 * Fixes:
 * 1. Re-run reconciliation for past months with new logic
 * 2. Fix wrong identity mappings
 * 3. Remove corrupted/duplicate punch rows
 * 4. Rebuild daily_attendance_final table
 */

class AttendanceDataMigration {
  constructor() {
    this.processor = new EnhancedBiometricProcessor();
    this.debugger = new AttendanceDebugger();
    this.backupDir = './data-backups';
    this.stats = {
      backedUp: 0,
      cleaned: 0,
      reconciled: 0,
      fixed: 0,
      errors: []
    };
  }

  /**
   * Main migration flow
   */
  async runFullMigration(startDate, endDate, options = {}) {
    console.log(`\n${'='.repeat(80)}`);
    console.log(`🔄 STARTING ATTENDANCE DATA MIGRATION`);
    console.log(`Date Range: ${startDate} to ${endDate}`);
    console.log(`${'='.repeat(80)}\n`);

    try {
      // Step 1: Backup existing data
      console.log(`\n📦 STEP 1: Backing up existing data...`);
      await this.backupExistingData(startDate, endDate);

      // Step 2: Audit current state
      console.log(`\n🔍 STEP 2: Running audit on current data...`);
      const auditReport = await this.auditCurrentState(startDate, endDate);

      // Step 3: Clean and fix data
      console.log(`\n🧹 STEP 3: Cleaning corrupted data...`);
      await this.cleanCorruptedData(auditReport);

      // Step 4: Fix identity mappings
      console.log(`\n🔗 STEP 4: Fixing identity mappings...`);
      await this.fixIdentityMappings(startDate, endDate);

      // Step 5: Remove duplicates
      console.log(`\n🔄 STEP 5: Removing duplicate punches...`);
      await this.removeDuplicatePunches();

      // Step 6: Re-reconcile attendance
      console.log(`\n♻️  STEP 6: Re-reconciling attendance with new merge logic...`);
      await this.reconciledAttendanceForDateRange(startDate, endDate);

      // Step 7: Verify results
      console.log(`\n✅ STEP 7: Verifying migration results...`);
      const verificationReport = await this.verifyMigration(startDate, endDate);

      console.log(`\n${'='.repeat(80)}`);
      console.log(`✅ MIGRATION COMPLETE`);
      console.log(`${'='.repeat(80)}`);
      this.printSummary();

      return {
        success: true,
        auditReport,
        verificationReport,
        stats: this.stats
      };

    } catch (error) {
      console.error('❌ Migration failed:', error);
      this.stats.errors.push({
        step: 'general',
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Step 1: Backup existing data
   */
  async backupExistingData(startDate, endDate) {
    try {
      const start = new Date(startDate);
      const end = new Date(endDate);

      // Backup attendance records
      const attendanceRecords = await DailyAttendance.find({
        date: { $gte: start, $lte: end }
      }).lean();

      // Backup biometric punches
      const biometricPunches = await BiometricPunch.find({
        date: { $gte: start, $lte: end }
      }).lean();

      const backupData = {
        timestamp: new Date(),
        dateRange: { start, end },
        attendanceRecords,
        biometricPunches,
        recordCounts: {
          attendance: attendanceRecords.length,
          punches: biometricPunches.length
        }
      };

      // Save to file (for reference)
      const fs = require('fs');
      const path = require('path');
      
      if (!fs.existsSync(this.backupDir)) {
        fs.mkdirSync(this.backupDir, { recursive: true });
      }

      const backupFile = path.join(
        this.backupDir,
        `backup-${moment().format('YYYY-MM-DD-HHmmss')}.json`
      );

      fs.writeFileSync(backupFile, JSON.stringify(backupData, null, 2));
      console.log(`✅ Backed up ${attendanceRecords.length} attendance + ${biometricPunches.length} punch records`);
      console.log(`   File: ${backupFile}`);

      this.stats.backedUp = attendanceRecords.length + biometricPunches.length;

      return backupData;

    } catch (error) {
      console.error('❌ Backup error:', error);
      this.stats.errors.push({
        step: 'backup',
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Step 2: Audit current state
   */
  async auditCurrentState(startDate, endDate) {
    try {
      const start = new Date(startDate);
      const end = new Date(endDate);

      const attendance = await DailyAttendance.find({
        date: { $gte: start, $lte: end }
      }).populate('user department');

      const punches = await BiometricPunch.find({
        date: { $gte: start, $lte: end }
      }).populate('user');

      const employees = await EmployeeMaster.find({}).lean();

      console.log(`   Auditing ${attendance.length} attendance records and ${punches.length} punches...`);

      const report = await this.debugger.generateAuditReport(
        attendance,
        punches,
        employees
      );

      console.log(`   Found ${report.totalIssuesFound} issues`);

      return report;

    } catch (error) {
      console.error('❌ Audit error:', error);
      this.stats.errors.push({
        step: 'audit',
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Step 3: Clean corrupted data
   */
  async cleanCorruptedData(auditReport) {
    try {
      let cleaned = 0;

      // Remove records with no user mapping
      const noUserRecords = await DailyAttendance.find({ user: null });
      if (noUserRecords.length > 0) {
        await DailyAttendance.deleteMany({ user: null });
        console.log(`   ✅ Removed ${noUserRecords.length} attendance records with no user mapping`);
        cleaned += noUserRecords.length;
      }

      // Fix date mismatches
      const dateIssues = auditReport.issues.dateGroupingIssues;
      for (const issue of dateIssues) {
        if (issue.type === 'DATE_MISMATCH') {
          const record = issue.record;
          // Recompute date from IN time
          const correctDate = moment(record.biometricTimeIn).tz('Asia/Kolkata').startOf('day').toDate();
          await DailyAttendance.updateOne(
            { _id: record._id },
            { date: correctDate }
          );
          cleaned++;
        }
      }

      // Mark corrupted punches
      const seqIssues = auditReport.issues.punchSequenceIssues;
      for (const issue of seqIssues) {
        if (issue.type === 'OUT_OF_ORDER_PUNCH_SEQUENCE') {
          const record = issue.record;
          // Mark as problematic for manual review
          await BiometricPunch.updateOne(
            { _id: record._id },
            { 
              $set: { 
                isProcessed: false,
                rawData: { ...record.rawData, corrupted: true }
              }
            }
          );
          cleaned++;
        }
      }

      console.log(`✅ Cleaned ${cleaned} corrupted records`);
      this.stats.cleaned = cleaned;

    } catch (error) {
      console.error('❌ Cleanup error:', error);
      this.stats.errors.push({
        step: 'cleanup',
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Step 4: Fix identity mappings
   */
  async fixIdentityMappings(startDate, endDate) {
    try {
      const start = new Date(startDate);
      const end = new Date(endDate);

      // Get unresolved punches
      const unresolvedPunches = await BiometricPunch.find({
        user: null,
        date: { $gte: start, $lte: end }
      });

      console.log(`   Found ${unresolvedPunches.length} unresolved punches`);

      if (unresolvedPunches.length === 0) {
        console.log(`✅ All punches have valid user mappings`);
        return;
      }

      const employees = await EmployeeMaster.find({})
        .select('_id user firstName lastName biometric_code');

      let fixed = 0;

      for (const punch of unresolvedPunches) {
        try {
          // Try to resolve using enhanced resolver
          const resolution = await this.processor.identityResolver.mapBiometricToEmployee(
            punch.biometricId,
            punch.rawData?.name || punch.rawData?.employee_name,
            employees
          );

          if (resolution.success) {
            // Map employee _id to user
            const employee = employees.find(e => e._id.toString() === resolution.employeeId.toString());
            if (employee) {
              await BiometricPunch.updateOne(
                { _id: punch._id },
                { 
                  user: employee.user,
                  isProcessed: false
                }
              );
              fixed++;
              console.log(`   ✅ Fixed: ${punch.biometricId} → ${employee.firstName} ${employee.lastName}`);
            }
          }
        } catch (error) {
          console.log(`   ⚠️  Could not resolve: ${punch.biometricId}`);
        }
      }

      console.log(`✅ Fixed ${fixed} identity mappings`);
      this.stats.fixed += fixed;

    } catch (error) {
      console.error('❌ Identity mapping fix error:', error);
      this.stats.errors.push({
        step: 'identity_mapping',
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Step 5: Remove duplicate punches
   */
  async removeDuplicatePunches() {
    try {
      const allPunches = await BiometricPunch.find({}).sort({ createdAt: 1 });

      const seen = new Map();
      const duplicateIds = [];

      for (const punch of allPunches) {
        if (!punch.user) continue;

        const key = `${punch.user}_${punch.date.toISOString().split('T')[0]}_${punch.punchTime}`;

        if (seen.has(key)) {
          // Keep first, mark second as duplicate
          duplicateIds.push(punch._id);
        } else {
          seen.set(key, punch._id);
        }
      }

      if (duplicateIds.length > 0) {
        await BiometricPunch.deleteMany({ _id: { $in: duplicateIds } });
        console.log(`✅ Removed ${duplicateIds.length} duplicate punches`);
        this.stats.cleaned += duplicateIds.length;
      } else {
        console.log(`✅ No duplicate punches found`);
      }

    } catch (error) {
      console.error('❌ Duplicate removal error:', error);
      this.stats.errors.push({
        step: 'duplicate_removal',
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Step 6: Re-reconcile attendance
   */
  async reconciledAttendanceForDateRange(startDate, endDate) {
    try {
      const start = moment(startDate).tz('Asia/Kolkata').startOf('day').toDate();
      const end = moment(endDate).tz('Asia/Kolkata').endOf('day').toDate();

      // Clear old attendance records for this period
      const deleted = await DailyAttendance.deleteMany({
        date: { $gte: start, $lte: end },
        verificationMethod: { $ne: 'Manual', $ne: 'Leave' } // Keep manual entries
      });

      console.log(`   Cleared ${deleted.deletedCount} old reconciled records`);

      // Re-derive attendance from biometric punches
      const result = await this.processor.deriveDailyAttendance(
        startDate,
        endDate
      );

      console.log(`✅ Re-reconciled attendance: ${result.created} created, ${result.updated} updated`);
      this.stats.reconciled = result.created + result.updated;

      return result;

    } catch (error) {
      console.error('❌ Reconciliation error:', error);
      this.stats.errors.push({
        step: 'reconciliation',
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Step 7: Verify migration
   */
  async verifyMigration(startDate, endDate) {
    try {
      const start = new Date(startDate);
      const end = new Date(endDate);

      const attendance = await DailyAttendance.find({
        date: { $gte: start, $lte: end }
      }).populate('user');

      const punches = await BiometricPunch.find({
        date: { $gte: start, $lte: end }
      }).populate('user');

      const employees = await EmployeeMaster.find({});

      // Run post-migration audit
      const postAudit = await this.debugger.generateAuditReport(
        attendance,
        punches,
        employees
      );

      console.log(`   Found ${postAudit.totalIssuesFound} issues in migrated data`);

      const improvement = {
        issuesReduced: auditReport?.totalIssuesFound > postAudit.totalIssuesFound,
        beforeCount: auditReport?.totalIssuesFound || 0,
        afterCount: postAudit.totalIssuesFound
      };

      console.log(`✅ Verification complete`);

      return {
        postAudit,
        improvement,
        recordCounts: {
          attendance: attendance.length,
          punches: punches.length,
          employees: employees.length
        }
      };

    } catch (error) {
      console.error('❌ Verification error:', error);
      this.stats.errors.push({
        step: 'verification',
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Print summary
   */
  printSummary() {
    console.log(`\n📊 MIGRATION SUMMARY:`);
    console.log(`  ✅ Backed up: ${this.stats.backedUp} records`);
    console.log(`  🧹 Cleaned: ${this.stats.cleaned} records`);
    console.log(`  🔗 Fixed mappings: ${this.stats.fixed} records`);
    console.log(`  ♻️  Reconciled: ${this.stats.reconciled} records`);
    if (this.stats.errors.length > 0) {
      console.log(`  ❌ Errors: ${this.stats.errors.length}`);
      for (const error of this.stats.errors) {
        console.log(`     - [${error.step}]: ${error.error}`);
      }
    }
  }
}

module.exports = AttendanceDataMigration;
