#!/usr/bin/env node

/**
 * QUICK START SCRIPT FOR BIOMETRIC SYSTEM MIGRATION
 * 
 * Usage:
 * node server/scripts/biometric-quickstart.js --action=migrate --start=2024-01-01 --end=2024-12-31
 */

const mongoose = require('mongoose');
const moment = require('moment-timezone');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

const AttendanceDataMigration = require('../utils/attendanceDataMigration');
const AttendanceDebugger = require('../utils/attendanceDebugger');
const EnhancedBiometricProcessor = require('../services/enhancedBiometricProcessor');

// Parse command line arguments
const args = process.argv.slice(2).reduce((acc, arg) => {
  const [key, value] = arg.replace('--', '').split('=');
  acc[key] = value;
  return acc;
}, {});

const action = args.action || 'help';
const startDate = args.start || moment().subtract(1, 'month').format('YYYY-MM-DD');
const endDate = args.end || moment().format('YYYY-MM-DD');

console.log(`
╔════════════════════════════════════════════════════════════╗
║    BIOMETRIC ATTENDANCE SYSTEM - QUICK START               ║
╚════════════════════════════════════════════════════════════╝

Action: ${action}
Start Date: ${startDate}
End Date: ${endDate}
`);

async function runAction() {
  try {
    // Connect to MongoDB
    await mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/workflow', {
      useNewUrlParser: true,
      useUnifiedTopology: true
    });
    console.log('✅ Connected to MongoDB');

    switch (action) {
      case 'audit':
        await runAudit();
        break;

      case 'migrate':
        await runMigration();
        break;

      case 'derive':
        await deriveDailyAttendance();
        break;

      case 'cleanup':
        await cleanupData();
        break;

      case 'check-health':
        await checkHealth();
        break;

      case 'help':
      default:
        showHelp();
        break;
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  } finally {
    await mongoose.connection.close();
    console.log('\n✅ Connection closed');
  }
}

async function runAudit() {
  console.log('\n📋 Running audit...\n');

  const DailyAttendance = require('../models/DailyAttendance');
  const BiometricPunch = require('../models/BiometricPunch');
  const EmployeeMaster = require('../models/EmployeeMaster');

  const start = new Date(startDate);
  const end = new Date(endDate);

  const attendance = await DailyAttendance.find({
    date: { $gte: start, $lte: end }
  }).populate('user');

  const punches = await BiometricPunch.find({
    date: { $gte: start, $lte: end }
  }).populate('user');

  const employees = await EmployeeMaster.find({});

  const debugger = new AttendanceDebugger();
  const report = await debugger.generateAuditReport(attendance, punches, employees);

  console.log('\n📊 AUDIT SUMMARY');
  console.log('═'.repeat(60));
  console.log(`Total Attendance Records: ${report.summary.totalAttendanceRecords}`);
  console.log(`Total Biometric Punches: ${report.summary.totalBiometricPunches}`);
  console.log(`Total Employees: ${report.summary.totalEmployees}`);
  console.log(`\nIssues Found: ${report.totalIssuesFound}`);
  console.log('─'.repeat(60));

  for (const category in report.issues) {
    const issues = report.issues[category];
    if (Array.isArray(issues) && issues.length > 0) {
      console.log(`\n⚠️  ${category}: ${issues.length}`);
      for (let i = 0; i < Math.min(3, issues.length); i++) {
        console.log(`   - ${issues[i].type}: ${issues[i].message}`);
      }
      if (issues.length > 3) {
        console.log(`   ... and ${issues.length - 3} more`);
      }
    }
  }

  const recommendations = debugger.generateFixRecommendations(report);
  console.log('\n💡 RECOMMENDATIONS');
  console.log('─'.repeat(60));
  for (const rec of recommendations) {
    console.log(`\n${rec.category} (Priority: ${rec.priority})`);
    for (const fix of rec.fixes) {
      console.log(`  • ${fix}`);
    }
  }
}

async function runMigration() {
  console.log('\n🔄 Starting full migration...\n');

  const migration = new AttendanceDataMigration();
  const result = await migration.runFullMigration(startDate, endDate);

  console.log('\n');
  console.log('═'.repeat(60));
  console.log('MIGRATION COMPLETE');
  console.log('═'.repeat(60));

  if (result.stats) {
    console.log(`\n✅ Backed up: ${result.stats.backedUp} records`);
    console.log(`🧹 Cleaned: ${result.stats.cleaned} records`);
    console.log(`🔗 Fixed mappings: ${result.stats.fixed} records`);
    console.log(`♻️  Reconciled: ${result.stats.reconciled} records`);

    if (result.stats.errors.length > 0) {
      console.log(`\n❌ Errors: ${result.stats.errors.length}`);
      for (const error of result.stats.errors) {
        console.log(`   - [${error.step}]: ${error.error}`);
      }
    }
  }
}

async function deriveDailyAttendance() {
  console.log('\n📊 Deriving daily attendance...\n');

  const processor = new EnhancedBiometricProcessor();
  const result = await processor.deriveDailyAttendance(startDate, endDate);

  console.log('\n✅ DERIVATION COMPLETE');
  console.log(`   Created: ${result.created}`);
  console.log(`   Updated: ${result.updated}`);
  console.log(`   Marked Absent: ${result.markedAbsent?.markedAbsent || 0}`);
  console.log(`   Errors: ${result.errors.length}`);
}

async function cleanupData() {
  console.log('\n🧹 Cleaning up duplicate punches...\n');

  const BiometricPunch = require('../models/BiometricPunch');

  const allPunches = await BiometricPunch.find({}).sort({ createdAt: 1 });

  const seen = new Map();
  const duplicateIds = [];

  for (const punch of allPunches) {
    if (!punch.user) continue;

    const key = `${punch.user}_${punch.date.toISOString().split('T')[0]}_${punch.punchTime}`;

    if (seen.has(key)) {
      duplicateIds.push(punch._id);
    } else {
      seen.set(key, punch._id);
    }
  }

  if (duplicateIds.length > 0) {
    await BiometricPunch.deleteMany({ _id: { $in: duplicateIds } });
    console.log(`✅ Removed ${duplicateIds.length} duplicate punches`);
  } else {
    console.log('✅ No duplicates found');
  }
}

async function checkHealth() {
  console.log('\n🏥 Checking system health...\n');

  const DailyAttendance = require('../models/DailyAttendance');
  const BiometricPunch = require('../models/BiometricPunch');
  const EmployeeMaster = require('../models/EmployeeMaster');
  const User = require('../models/User');

  const stats = {};

  stats.totalUsers = await User.countDocuments({ isActive: true });
  stats.totalEmployees = await EmployeeMaster.countDocuments();
  stats.totalAttendanceRecords = await DailyAttendance.countDocuments();
  stats.totalBiometricPunches = await BiometricPunch.countDocuments();
  stats.unprocessedPunches = await BiometricPunch.countDocuments({ isProcessed: false });
  stats.unverifiedAttendance = await DailyAttendance.countDocuments({ isVerified: false });

  console.log('📊 SYSTEM HEALTH');
  console.log('═'.repeat(60));
  console.log(`Active Users: ${stats.totalUsers}`);
  console.log(`Employees Configured: ${stats.totalEmployees}`);
  console.log(`Attendance Records: ${stats.totalAttendanceRecords}`);
  console.log(`Biometric Punches: ${stats.totalBiometricPunches}`);
  console.log(`Unprocessed Punches: ${stats.unprocessedPunches}`);
  console.log(`Unverified Attendance: ${stats.unverifiedAttendance}`);

  // Health checks
  const health = {
    connected: true,
    dataExists: stats.totalAttendanceRecords > 0,
    biometricDataExists: stats.totalBiometricPunches > 0,
    employeesMapped: stats.totalEmployees > 0,
    processingHealthy: stats.unprocessedPunches < stats.totalBiometricPunches * 0.1
  };

  console.log('\n🔍 HEALTH CHECKS');
  console.log('─'.repeat(60));
  console.log(`✅ Database Connected: ${health.connected ? 'YES' : 'NO'}`);
  console.log(`✅ Attendance Data: ${health.dataExists ? 'EXISTS' : 'MISSING'}`);
  console.log(`✅ Biometric Data: ${health.biometricDataExists ? 'EXISTS' : 'MISSING'}`);
  console.log(`✅ Employees Mapped: ${health.employeesMapped ? 'YES' : 'NO'}`);
  console.log(`✅ Processing Status: ${health.processingHealthy ? 'HEALTHY' : 'NEEDS ATTENTION'}`);
}

function showHelp() {
  console.log(`
AVAILABLE COMMANDS:

  node biometric-quickstart.js --action=audit \\
    --start=2024-01-01 --end=2024-12-31
    
    Run audit on attendance data for date range

  node biometric-quickstart.js --action=migrate \\
    --start=2024-01-01 --end=2024-12-31
    
    Run full migration (backup, clean, reconcile)

  node biometric-quickstart.js --action=derive \\
    --start=2024-01-01 --end=2024-12-31
    
    Derive daily attendance from biometric punches

  node biometric-quickstart.js --action=cleanup
    
    Remove duplicate punches

  node biometric-quickstart.js --action=check-health
    
    Check system health and status

  node biometric-quickstart.js --action=help
    
    Show this help message

EXAMPLES:

  # Audit last month
  node biometric-quickstart.js --action=audit

  # Migrate specific month
  node biometric-quickstart.js --action=migrate \\
    --start=2024-12-01 --end=2024-12-31

  # Check system health
  node biometric-quickstart.js --action=check-health
  `);
}

// Run the selected action
runAction().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
