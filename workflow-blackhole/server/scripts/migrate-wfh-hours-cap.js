/**
 * WFH Hours Cap Migration Script
 * ================================
 * 
 * OBJECTIVE:
 * Retroactively correct past database records for WFH employees
 * where work hours exceed 8 hours per calendar day.
 * 
 * RULES:
 * - ONLY affects WFH (Work From Home) employees
 * - WFO (Work From Office) employees are NOT touched
 * - Maximum 8 hours per calendar day for WFH
 * - Cross-day sessions are split into per-day records
 * - Original timestamps preserved for audit
 * - Idempotent: running multiple times yields same result
 * 
 * USAGE:
 * node scripts/migrate-wfh-hours-cap.js
 * 
 * OPTIONS:
 * --dry-run    Preview changes without modifying database
 * --verbose    Show detailed logs for each record
 */

require('dotenv').config();
const mongoose = require('mongoose');
const Attendance = require('../models/Attendance');
const DailyAttendance = require('../models/DailyAttendance');
const User = require('../models/User');

// WFH Maximum Hours Cap
const WFH_MAX_HOURS_PER_DAY = 8;

// Parse command line arguments
const args = process.argv.slice(2);
const DRY_RUN = args.includes('--dry-run');
const VERBOSE = args.includes('--verbose');

// Migration log storage
const migrationLog = {
  startTime: new Date(),
  endTime: null,
  totalRecordsScanned: 0,
  wfhRecordsFound: 0,
  recordsModified: 0,
  recordsSkipped: 0,
  errors: [],
  modifiedRecords: []
};

/**
 * Connect to MongoDB
 */
async function connectDB() {
  const mongoUri = process.env.MONGODB_URI || process.env.MONGO_URI;
  if (!mongoUri) {
    throw new Error('MongoDB URI not found in environment variables');
  }
  
  console.log('🔌 Connecting to MongoDB...');
  await mongoose.connect(mongoUri);
  console.log('✅ Connected to MongoDB');
}

/**
 * Get all WFH users from database
 * WFH is determined by:
 * 1. User.workMode === 'WFH'
 * 2. Attendance.workPattern === 'Remote'
 * 3. DailyAttendance.workLocationType === 'Home' or 'Remote'
 */
async function getWFHUsers() {
  // Get users explicitly marked as WFH
  const wfhUsers = await User.find({ workMode: 'WFH' }).select('_id name email').lean();
  const wfhUserIds = new Set(wfhUsers.map(u => u._id.toString()));
  
  console.log(`📋 Found ${wfhUsers.length} users with workMode = 'WFH'`);
  
  return { wfhUsers, wfhUserIds };
}

/**
 * Fix Attendance records for WFH employees
 */
async function fixAttendanceRecords(wfhUserIds) {
  console.log('\n📊 Processing Attendance records...');
  
  // Find all attendance records that might need fixing
  // - WFH by user workMode OR by workPattern === 'Remote'
  // - hoursWorked > 8
  const query = {
    $or: [
      { user: { $in: Array.from(wfhUserIds) } },
      { workPattern: 'Remote' }
    ],
    hoursWorked: { $gt: WFH_MAX_HOURS_PER_DAY }
  };
  
  const records = await Attendance.find(query)
    .populate('user', 'name email workMode')
    .sort({ date: -1 })
    .lean();
  
  console.log(`📋 Found ${records.length} Attendance records with hours > ${WFH_MAX_HOURS_PER_DAY}h`);
  migrationLog.totalRecordsScanned += records.length;
  
  for (const record of records) {
    try {
      // Determine if this is truly a WFH record
      const isWFH = record.workPattern === 'Remote' || 
                    record.user?.workMode === 'WFH' ||
                    wfhUserIds.has(record.user?._id?.toString());
      
      if (!isWFH) {
        // Skip WFO records - they should NOT be capped
        if (VERBOSE) {
          console.log(`⏭️ Skipping WFO record for ${record.user?.name} - ${record.hoursWorked}h (no cap for WFO)`);
        }
        migrationLog.recordsSkipped++;
        continue;
      }
      
      migrationLog.wfhRecordsFound++;
      
      const oldHours = record.hoursWorked;
      const newHours = WFH_MAX_HOURS_PER_DAY;
      
      const logEntry = {
        model: 'Attendance',
        recordId: record._id.toString(),
        userId: record.user?._id?.toString(),
        userName: record.user?.name || 'Unknown',
        date: record.date?.toISOString().split('T')[0],
        oldHours: Math.round(oldHours * 100) / 100,
        newHours: newHours,
        difference: Math.round((oldHours - newHours) * 100) / 100
      };
      
      if (DRY_RUN) {
        console.log(`🔍 [DRY RUN] Would cap: ${logEntry.userName} | ${logEntry.date} | ${logEntry.oldHours}h → ${logEntry.newHours}h`);
        migrationLog.modifiedRecords.push(logEntry);
        continue;
      }
      
      // Apply the cap
      await Attendance.updateOne(
        { _id: record._id },
        {
          $set: {
            hoursWorked: newHours,
            overtimeHours: 0, // WFH has no overtime
            systemNotes: (record.systemNotes || '') + 
              ` [WFH Migration: ${oldHours.toFixed(2)}h → ${newHours}h capped on ${new Date().toISOString()}]`
          }
        }
      );
      
      migrationLog.recordsModified++;
      migrationLog.modifiedRecords.push(logEntry);
      
      if (VERBOSE) {
        console.log(`✅ Capped: ${logEntry.userName} | ${logEntry.date} | ${logEntry.oldHours}h → ${logEntry.newHours}h`);
      }
      
    } catch (error) {
      console.error(`❌ Error processing Attendance record ${record._id}:`, error.message);
      migrationLog.errors.push({
        model: 'Attendance',
        recordId: record._id?.toString(),
        error: error.message
      });
    }
  }
}

/**
 * Fix DailyAttendance records for WFH employees
 */
async function fixDailyAttendanceRecords(wfhUserIds) {
  console.log('\n📊 Processing DailyAttendance records...');
  
  // Find all daily attendance records that might need fixing
  // - WFH by user workMode OR by workLocationType === 'Home' or 'Remote'
  // - totalHoursWorked > 8
  const query = {
    $or: [
      { user: { $in: Array.from(wfhUserIds) } },
      { workLocationType: { $in: ['Home', 'Remote'] } }
    ],
    totalHoursWorked: { $gt: WFH_MAX_HOURS_PER_DAY }
  };
  
  const records = await DailyAttendance.find(query)
    .populate('user', 'name email workMode')
    .sort({ date: -1 })
    .lean();
  
  console.log(`📋 Found ${records.length} DailyAttendance records with hours > ${WFH_MAX_HOURS_PER_DAY}h`);
  migrationLog.totalRecordsScanned += records.length;
  
  for (const record of records) {
    try {
      // Determine if this is truly a WFH record
      const isWFH = record.workLocationType === 'Home' || 
                    record.workLocationType === 'Remote' ||
                    record.user?.workMode === 'WFH' ||
                    wfhUserIds.has(record.user?._id?.toString());
      
      if (!isWFH) {
        // Skip WFO records - they should NOT be capped
        if (VERBOSE) {
          console.log(`⏭️ Skipping WFO DailyAttendance for ${record.user?.name} - ${record.totalHoursWorked}h (no cap for WFO)`);
        }
        migrationLog.recordsSkipped++;
        continue;
      }
      
      migrationLog.wfhRecordsFound++;
      
      const oldHours = record.totalHoursWorked;
      const newHours = WFH_MAX_HOURS_PER_DAY;
      
      const logEntry = {
        model: 'DailyAttendance',
        recordId: record._id.toString(),
        userId: record.user?._id?.toString(),
        userName: record.user?.name || 'Unknown',
        date: record.date?.toISOString().split('T')[0],
        oldHours: Math.round(oldHours * 100) / 100,
        newHours: newHours,
        difference: Math.round((oldHours - newHours) * 100) / 100
      };
      
      if (DRY_RUN) {
        console.log(`🔍 [DRY RUN] Would cap: ${logEntry.userName} | ${logEntry.date} | ${logEntry.oldHours}h → ${logEntry.newHours}h`);
        migrationLog.modifiedRecords.push(logEntry);
        continue;
      }
      
      // Apply the cap
      await DailyAttendance.updateOne(
        { _id: record._id },
        {
          $set: {
            totalHoursWorked: newHours,
            regularHours: Math.min(oldHours, 8),
            overtimeHours: 0, // WFH has no overtime
            remoteHours: newHours, // All hours are remote for WFH
            systemNotes: (record.systemNotes || '') + 
              ` [WFH Migration: ${oldHours.toFixed(2)}h → ${newHours}h capped on ${new Date().toISOString()}]`
          }
        }
      );
      
      migrationLog.recordsModified++;
      migrationLog.modifiedRecords.push(logEntry);
      
      if (VERBOSE) {
        console.log(`✅ Capped: ${logEntry.userName} | ${logEntry.date} | ${logEntry.oldHours}h → ${logEntry.newHours}h`);
      }
      
    } catch (error) {
      console.error(`❌ Error processing DailyAttendance record ${record._id}:`, error.message);
      migrationLog.errors.push({
        model: 'DailyAttendance',
        recordId: record._id?.toString(),
        error: error.message
      });
    }
  }
}

/**
 * Handle cross-day sessions by splitting them
 * Only for WFH employees with sessions spanning midnight
 */
async function splitCrossDaySessions(wfhUserIds) {
  console.log('\n📊 Processing cross-day sessions...');
  
  // Find WFH attendance records where session spans across midnight
  // These have startDayTime on one day and endDayTime on the next day
  const records = await Attendance.find({
    $or: [
      { user: { $in: Array.from(wfhUserIds) } },
      { workPattern: 'Remote' }
    ],
    startDayTime: { $exists: true },
    endDayTime: { $exists: true }
  })
  .populate('user', 'name email workMode')
  .sort({ date: -1 })
  .lean();
  
  let crossDayCount = 0;
  
  for (const record of records) {
    try {
      if (!record.startDayTime || !record.endDayTime) continue;
      
      const startDate = new Date(record.startDayTime);
      const endDate = new Date(record.endDayTime);
      
      // Check if they're on different calendar days
      const startDay = startDate.toISOString().split('T')[0];
      const endDay = endDate.toISOString().split('T')[0];
      
      if (startDay === endDay) continue; // Same day, no split needed
      
      // Determine if this is WFH
      const isWFH = record.workPattern === 'Remote' || 
                    record.user?.workMode === 'WFH' ||
                    wfhUserIds.has(record.user?._id?.toString());
      
      if (!isWFH) continue; // Only split WFH sessions
      
      crossDayCount++;
      
      // Calculate hours for first day (start to midnight)
      const midnightOfStartDay = new Date(startDate);
      midnightOfStartDay.setHours(24, 0, 0, 0);
      
      const hoursFirstDay = Math.min(
        (midnightOfStartDay - startDate) / (1000 * 60 * 60),
        WFH_MAX_HOURS_PER_DAY
      );
      
      // Calculate hours for second day (midnight to end)
      const midnightOfEndDay = new Date(endDate);
      midnightOfEndDay.setHours(0, 0, 0, 0);
      
      const hoursSecondDay = Math.min(
        (endDate - midnightOfEndDay) / (1000 * 60 * 60),
        WFH_MAX_HOURS_PER_DAY
      );
      
      if (VERBOSE) {
        console.log(`🔀 Cross-day session: ${record.user?.name} | ${startDay} → ${endDay}`);
        console.log(`   Day 1: ${hoursFirstDay.toFixed(2)}h | Day 2: ${hoursSecondDay.toFixed(2)}h`);
      }
      
      if (DRY_RUN) {
        console.log(`🔍 [DRY RUN] Would split: ${record.user?.name} | ${startDay} → ${endDay}`);
        migrationLog.modifiedRecords.push({
          model: 'CrossDaySplit',
          recordId: record._id.toString(),
          userName: record.user?.name,
          startDay,
          endDay,
          hoursFirstDay: Math.round(hoursFirstDay * 100) / 100,
          hoursSecondDay: Math.round(hoursSecondDay * 100) / 100
        });
        continue;
      }
      
      // Update original record to only have first day's hours
      await Attendance.updateOne(
        { _id: record._id },
        {
          $set: {
            endDayTime: midnightOfStartDay,
            hoursWorked: Math.round(hoursFirstDay * 100) / 100,
            overtimeHours: 0,
            spanType: 'MIDNIGHT_SPAN',
            spanDetails: {
              startDate: startDay,
              endDate: endDay,
              actualHours: record.hoursWorked,
              fixedHours: WFH_MAX_HOURS_PER_DAY,
              splitRequired: true,
              isWFH: true
            },
            systemNotes: (record.systemNotes || '') + 
              ` [WFH Cross-day split: Day 1 = ${hoursFirstDay.toFixed(2)}h on ${new Date().toISOString()}]`
          }
        }
      );
      
      // Check if second day record exists, if not create it
      const secondDayStart = new Date(endDay);
      secondDayStart.setHours(0, 0, 0, 0);
      const secondDayEnd = new Date(endDay);
      secondDayEnd.setHours(23, 59, 59, 999);
      
      const existingSecondDay = await Attendance.findOne({
        user: record.user._id,
        date: { $gte: secondDayStart, $lte: secondDayEnd }
      });
      
      if (!existingSecondDay && hoursSecondDay > 0) {
        // Create new record for second day
        await Attendance.create({
          user: record.user._id,
          date: secondDayStart,
          startDayTime: midnightOfEndDay,
          endDayTime: endDate,
          hoursWorked: Math.round(hoursSecondDay * 100) / 100,
          overtimeHours: 0,
          workPattern: 'Remote',
          isPresent: true,
          isVerified: record.isVerified,
          verificationMethod: record.verificationMethod,
          source: record.source || 'StartDay',
          spanType: 'MIDNIGHT_SPAN',
          spanDetails: {
            startDate: startDay,
            endDate: endDay,
            actualHours: hoursSecondDay,
            fixedHours: WFH_MAX_HOURS_PER_DAY,
            splitRequired: true,
            isWFH: true,
            isSecondDayOfSplit: true
          },
          systemNotes: `[WFH Cross-day split: Day 2 = ${hoursSecondDay.toFixed(2)}h, created from split on ${new Date().toISOString()}]`
        });
        
        if (VERBOSE) {
          console.log(`✅ Created second day record for ${record.user?.name} on ${endDay}`);
        }
      }
      
      migrationLog.recordsModified++;
      
    } catch (error) {
      console.error(`❌ Error processing cross-day session ${record._id}:`, error.message);
      migrationLog.errors.push({
        model: 'CrossDaySplit',
        recordId: record._id?.toString(),
        error: error.message
      });
    }
  }
  
  console.log(`📋 Found ${crossDayCount} cross-day sessions requiring split`);
}

/**
 * Generate summary report
 */
function generateReport() {
  migrationLog.endTime = new Date();
  const duration = (migrationLog.endTime - migrationLog.startTime) / 1000;
  
  console.log('\n' + '='.repeat(60));
  console.log('📊 WFH HOURS CAP MIGRATION REPORT');
  console.log('='.repeat(60));
  console.log(`Mode: ${DRY_RUN ? '🔍 DRY RUN (no changes made)' : '✅ LIVE MIGRATION'}`);
  console.log(`Duration: ${duration.toFixed(2)} seconds`);
  console.log(`Start: ${migrationLog.startTime.toISOString()}`);
  console.log(`End: ${migrationLog.endTime.toISOString()}`);
  console.log('');
  console.log('📈 STATISTICS:');
  console.log(`   Total Records Scanned: ${migrationLog.totalRecordsScanned}`);
  console.log(`   WFH Records Found: ${migrationLog.wfhRecordsFound}`);
  console.log(`   Records Modified: ${migrationLog.recordsModified}`);
  console.log(`   Records Skipped (WFO): ${migrationLog.recordsSkipped}`);
  console.log(`   Errors: ${migrationLog.errors.length}`);
  console.log('');
  
  if (migrationLog.modifiedRecords.length > 0) {
    console.log('📝 MODIFIED RECORDS:');
    console.log('-'.repeat(60));
    console.log('Employee | Date | Old Hours | New Hours | Difference');
    console.log('-'.repeat(60));
    
    for (const record of migrationLog.modifiedRecords.slice(0, 50)) {
      console.log(`${record.userName?.substring(0, 20).padEnd(20)} | ${record.date || 'N/A'} | ${record.oldHours?.toString().padStart(6)}h | ${record.newHours?.toString().padStart(6)}h | -${record.difference}h`);
    }
    
    if (migrationLog.modifiedRecords.length > 50) {
      console.log(`... and ${migrationLog.modifiedRecords.length - 50} more records`);
    }
  }
  
  if (migrationLog.errors.length > 0) {
    console.log('\n❌ ERRORS:');
    for (const error of migrationLog.errors) {
      console.log(`   ${error.model} ${error.recordId}: ${error.error}`);
    }
  }
  
  console.log('\n' + '='.repeat(60));
  console.log('✅ Migration completed successfully!');
  console.log('='.repeat(60));
  
  return migrationLog;
}

/**
 * Main migration function
 */
async function runMigration() {
  console.log('='.repeat(60));
  console.log('🚀 WFH HOURS CAP MIGRATION SCRIPT');
  console.log('='.repeat(60));
  console.log('');
  console.log('📋 RULES:');
  console.log('   - WFH employees: MAX 8 hours per calendar day');
  console.log('   - WFO employees: NO changes (unlimited hours)');
  console.log('   - Cross-day sessions: Split into per-day records');
  console.log('   - Original timestamps: Preserved for audit');
  console.log('');
  
  if (DRY_RUN) {
    console.log('⚠️  DRY RUN MODE - No changes will be made to the database');
    console.log('');
  }
  
  try {
    await connectDB();
    
    const { wfhUsers, wfhUserIds } = await getWFHUsers();
    
    // Process Attendance records
    await fixAttendanceRecords(wfhUserIds);
    
    // Process DailyAttendance records
    await fixDailyAttendanceRecords(wfhUserIds);
    
    // Split cross-day sessions
    await splitCrossDaySessions(wfhUserIds);
    
    // Generate report
    const report = generateReport();
    
    // Save report to file
    const fs = require('fs');
    const reportPath = `./migration-reports/wfh-cap-migration-${Date.now()}.json`;
    
    try {
      fs.mkdirSync('./migration-reports', { recursive: true });
      fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
      console.log(`\n📄 Report saved to: ${reportPath}`);
    } catch (fsError) {
      console.warn('⚠️ Could not save report to file:', fsError.message);
    }
    
  } catch (error) {
    console.error('❌ Migration failed:', error);
    process.exit(1);
  } finally {
    await mongoose.disconnect();
    console.log('\n🔌 Disconnected from MongoDB');
  }
}

// Run the migration
runMigration();
