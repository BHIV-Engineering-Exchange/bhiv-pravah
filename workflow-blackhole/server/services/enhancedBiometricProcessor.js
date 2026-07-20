const BiometricPunch = require('../models/BiometricPunch');
const DailyAttendance = require('../models/DailyAttendance');
const EmployeeMaster = require('../models/EmployeeMaster');
const User = require('../models/User');
const BiometricUpload = require('../models/BiometricUpload');
const BiometricIdentityResolver = require('../utils/biometricIdentityResolver');
const AttendanceMergeLogic = require('../utils/attendanceMergeLogic');
const XLSX = require('xlsx');
const csv = require('csv-parser');
const fs = require('fs');
const moment = require('moment-timezone');
const mongoose = require('mongoose');

/**
 * ENHANCED BIOMETRIC PROCESSOR
 * - Improved identity resolution
 * - Smart merge logic with 20-minute tolerance
 * - Comprehensive logging and error handling
 * - Duplicate detection and cleaning
 */

class EnhancedBiometricProcessor {
  constructor() {
    this.identityResolver = new BiometricIdentityResolver();
    this.mergeLogic = new AttendanceMergeLogic({
      timezone: 'Asia/Kolkata',
      tolerance: 20,
      minRequiredHours: 4,
      standardShiftHours: 8,
      debug: true
    });
    this.dateFormats = [
      'YYYY-MM-DD HH:mm:ss',
      'DD/MM/YYYY HH:mm:ss',
      'MM/DD/YYYY HH:mm:ss',
      'DD-MM-YYYY HH:mm:ss',
      'YYYY/MM/DD HH:mm:ss',
      'DD/MM/YYYY HH:mm',
      'MM/DD/YYYY HH:mm',
      'YYYY-MM-DD'
    ];
    this.debug = true;
  }

  /**
   * Parse uploaded biometric file (CSV or Excel)
   */
  async parseFile(filePath, fileName, uploadedBy) {
    try {
      const ext = fileName.split('.').pop().toLowerCase();
      let data = [];

      this._log(`📤 Parsing file: ${fileName}`);

      if (ext === 'csv') {
        data = await this.parseCSV(filePath);
      } else if (ext === 'xlsx' || ext === 'xls') {
        data = await this.parseExcel(filePath);
      } else {
        throw new Error('Unsupported file format. Please upload CSV or Excel files.');
      }

      this._log(`✅ Parsed ${data.length} records from ${fileName}`);

      // Create upload record
      const uploadRecord = new BiometricUpload({
        fileName: fileName,
        originalFileName: fileName,
        filePath: filePath,
        fileSize: fs.statSync(filePath).size,
        processedBy: uploadedBy,
        totalRecords: data.length,
        status: 'Processing',
        uploadDate: new Date(),
        processingDetails: {
          startTime: new Date(),
          identityResolutionAttempts: 0,
          duplicatesDetected: 0,
          invalidRecords: 0
        }
      });

      await uploadRecord.save();
      this._log(`📝 Created upload record: ${uploadRecord._id}`);

      // Process the data
      const result = await this.processBiometricData(data, uploadRecord._id);

      // Update upload record with results
      uploadRecord.successfulMatches = result.successfulMatches;
      uploadRecord.discrepancies = result.discrepancies;
      uploadRecord.newRecords = result.newRecords;
      uploadRecord.updatedRecords = result.updatedRecords;
      uploadRecord.status = 'Completed';
      uploadRecord.processedRecords = result.processedRecords;
      uploadRecord.errors = result.errors;
      uploadRecord.ambiguousMatches = result.ambiguousMatches;
      uploadRecord.processingDetails.endTime = new Date();
      uploadRecord.processingDetails.identityResolutionAttempts = result.identityResolutionAttempts;
      uploadRecord.processingDetails.duplicatesDetected = result.duplicatesDetected;

      await uploadRecord.save();
      this._log(`✅ Upload processing complete`);

      return {
        success: true,
        uploadId: uploadRecord._id,
        ...result
      };

    } catch (error) {
      console.error('❌ File parsing error:', error);
      throw error;
    }
  }

  /**
   * Parse CSV file
   */
  parseCSV(filePath) {
    return new Promise((resolve, reject) => {
      const results = [];
      fs.createReadStream(filePath)
        .pipe(csv())
        .on('data', (data) => results.push(data))
        .on('end', () => resolve(results))
        .on('error', (error) => reject(error));
    });
  }

  /**
   * Parse Excel file
   */
  async parseExcel(filePath) {
    try {
      const workbook = XLSX.readFile(filePath);
      const sheetName = workbook.SheetNames[0];
      const sheet = workbook.Sheets[sheetName];
      const data = XLSX.utils.sheet_to_json(sheet);
      return data;
    } catch (error) {
      throw new Error('Failed to parse Excel file: ' + error.message);
    }
  }

  /**
   * Process biometric data with identity resolution
   */
  async processBiometricData(data, uploadBatchId) {
    const result = {
      successfulMatches: 0,
      discrepancies: 0,
      newRecords: 0,
      updatedRecords: 0,
      processedRecords: 0,
      errors: [],
      ambiguousMatches: [],
      identityResolutionAttempts: 0,
      duplicatesDetected: 0
    };

    // Fetch all employees for identity resolution
    const employees = await EmployeeMaster.find({})
      .select('_id user firstName lastName biometric_code email department')
      .lean();

    this._log(`📋 Loaded ${employees.length} employees for identity matching`);

    // Detect duplicates
    const duplicateCheckResult = await this.detectDuplicates(data);
    result.duplicatesDetected = duplicateCheckResult.duplicateCount;

    if (duplicateCheckResult.duplicateCount > 0) {
      this._log(`⚠️  Found ${duplicateCheckResult.duplicateCount} duplicate punches`);
      // Remove duplicates - keep first occurrence
      const uniqueData = duplicateCheckResult.uniqueRecords;
      this._log(`Removed ${data.length - uniqueData.length} duplicates`);
      // Continue with unique records
      data = uniqueData;
    }

    for (const row of data) {
      try {
        result.identityResolutionAttempts++;

        // Extract raw fields
        const rawEmployeeId = this.extractField(row, [
          'employee_id', 'employeeid', 'emp_id', 'empid', 
          'id', 'employee', 'staff_id', 'staffid'
        ]);

        const rawBiometricId = this.extractField(row, [
          'biometric_id', 'biometricid', 'card_no', 'cardno',
          'badge_id', 'badgeid', 'device_id', 'emp_code'
        ]);

        const rawName = this.extractField(row, [
          'name', 'employee_name', 'full_name', 'fullname',
          'employee'
        ]);

        const punchTimeStr = this.extractField(row, [
          'punch_time', 'punchtime', 'time', 'timestamp',
          'datetime', 'date_time', 'clock_time', 'date'
        ]);

        // Validate required fields
        if (!punchTimeStr) {
          result.errors.push({
            row: row,
            error: 'Missing punch time'
          });
          result.discrepancies++;
          continue;
        }

        // Parse punch time
        const punchTime = this.parseDateTime(punchTimeStr);
        if (!punchTime) {
          result.errors.push({
            row: row,
            error: `Invalid punch time format: ${punchTimeStr}`
          });
          result.discrepancies++;
          continue;
        }

        const punchDate = moment(punchTime).tz('Asia/Kolkata').startOf('day').toDate();

        // IDENTITY RESOLUTION
        let resolvedEmployee = null;
        let resolutionResult = null;

        // Try to resolve using available identifiers
        if (rawBiometricId || rawName) {
          resolutionResult = await this.identityResolver.mapBiometricToEmployee(
            rawBiometricId,
            rawName,
            employees
          );

          if (resolutionResult.success) {
            const employeeRecord = employees.find(e => e._id.toString() === resolutionResult.employeeId.toString());
            if (employeeRecord) {
              resolvedEmployee = employeeRecord;
              this._log(`✅ Resolved: "${rawName}" (ID: ${rawBiometricId}) → ${employeeRecord.firstName} ${employeeRecord.lastName}`);
            }
          } else if (resolutionResult.errorCode === 'AMBIGUOUS_MATCH') {
            result.ambiguousMatches.push({
              row: row,
              biometricId: rawBiometricId,
              biometricName: rawName,
              candidates: resolutionResult.candidates
            });
            this._log(`⚠️  AMBIGUOUS: "${rawName}" (ID: ${rawBiometricId}) matches multiple employees`);
            result.discrepancies++;
            continue;
          } else {
            this._log(`❌ UNRESOLVED: "${rawName}" (ID: ${rawBiometricId}) - ${resolutionResult.error}`);
            result.errors.push({
              row: row,
              error: `Identity resolution failed: ${resolutionResult.error}`
            });
            result.discrepancies++;
            continue;
          }
        } else {
          result.errors.push({
            row: row,
            error: 'Missing both biometric ID and name'
          });
          result.discrepancies++;
          continue;
        }

        // Create or update biometric punch
        const existingPunch = await BiometricPunch.findOne({
          user: resolvedEmployee.user,
          date: punchDate,
          punchTime: punchTime
        });

        let punchRecord;
        if (existingPunch) {
          // Update existing
          existingPunch.biometricId = rawBiometricId;
          existingPunch.uploadBatch = uploadBatchId;
          existingPunch.rawData = row;
          await existingPunch.save();
          result.updatedRecords++;
          this._log(`📝 Updated punch record`);
        } else {
          // Create new
          punchRecord = new BiometricPunch({
            employeeId: resolvedEmployee._id,
            user: resolvedEmployee.user,
            biometricId: rawBiometricId,
            punchTime: punchTime,
            date: punchDate,
            punchType: 'Unknown', // Will be determined during merge
            uploadBatch: uploadBatchId,
            rawData: row,
            isProcessed: false
          });
          await punchRecord.save();
          result.newRecords++;
          this._log(`➕ Created new punch record`);
        }

        result.processedRecords++;
        result.successfulMatches++;

      } catch (error) {
        console.error('Error processing row:', error);
        result.errors.push({
          row: row,
          error: error.message
        });
        result.discrepancies++;
      }
    }

    this._log(`\n📊 PROCESSING SUMMARY:`);
    this._log(`  Total records: ${result.processedRecords}`);
    this._log(`  Successful: ${result.successfulMatches}`);
    this._log(`  Errors: ${result.errors.length}`);
    this._log(`  Ambiguous: ${result.ambiguousMatches.length}`);
    this._log(`  Duplicates removed: ${result.duplicatesDetected}`);

    return result;
  }

  /**
   * Detect duplicate punches
   */
  async detectDuplicates(data) {
    const seen = new Set();
    const uniqueRecords = [];
    let duplicateCount = 0;

    for (const record of data) {
      const bioId = this.extractField(record, ['biometric_id', 'emp_code', 'id']);
      const timeStr = this.extractField(record, ['punch_time', 'time', 'date', 'timestamp']);

      const key = `${bioId}_${timeStr}`;

      if (seen.has(key)) {
        duplicateCount++;
        this._log(`🔄 Duplicate detected: ${key}`);
      } else {
        seen.add(key);
        uniqueRecords.push(record);
      }
    }

    return { uniqueRecords, duplicateCount };
  }

  /**
   * Derive daily attendance from biometric punches
   */
  async deriveDailyAttendance(startDate, endDate) {
    try {
      const start = moment(startDate).tz('Asia/Kolkata').startOf('day').toDate();
      const end = moment(endDate).tz('Asia/Kolkata').endOf('day').toDate();

      this._log(`\n📊 Deriving attendance from ${moment(start).format('YYYY-MM-DD')} to ${moment(end).format('YYYY-MM-DD')}`);

      // Find all punches in date range
      const punches = await BiometricPunch.find({
        date: { $gte: start, $lte: end },
        user: { $exists: true, $ne: null }
      })
        .populate('user', 'name email')
        .sort({ user: 1, date: 1, punchTime: 1 });

      this._log(`Found ${punches.length} total biometric punches`);

      // Group by user and date
      const grouped = {};

      for (const punch of punches) {
        const userId = punch.user._id.toString();
        const dateKey = moment(punch.date).tz('Asia/Kolkata').format('YYYY-MM-DD');
        const key = `${userId}_${dateKey}`;

        if (!grouped[key]) {
          grouped[key] = {
            user: punch.user,
            date: punch.date,
            userId: userId,
            dateKey: dateKey,
            punches: []
          };
        }

        grouped[key].punches.push(punch);
      }

      this._log(`Grouped into ${Object.keys(grouped).length} user-day combinations`);

      // Process each group
      const results = {
        created: 0,
        updated: 0,
        errors: [],
        mergeDetails: []
      };

      for (const key in grouped) {
        try {
          const group = grouped[key];
          const mergeDetail = await this.createOrUpdateAttendanceWithMergeLogic(group);
          if (mergeDetail.status === 'created') {
            results.created++;
          } else {
            results.updated++;
          }
          results.mergeDetails.push(mergeDetail);
        } catch (error) {
          console.error(`Error processing attendance for ${key}:`, error);
          results.errors.push({
            key: key,
            error: error.message
          });
        }
      }

      // Mark absent days
      const absentResult = await this.markAbsentDays(start, end);
      results.markedAbsent = absentResult;

      this._log(`✅ Attendance derivation complete: ${results.created} created, ${results.updated} updated`);

      return results;

    } catch (error) {
      console.error('❌ Error deriving daily attendance:', error);
      throw error;
    }
  }

  /**
   * Create or update attendance using merge logic
   */
  async createOrUpdateAttendanceWithMergeLogic(group) {
    const { user, date, punches } = group;

    // Sort punches by time
    punches.sort((a, b) => new Date(a.punchTime) - new Date(b.punchTime));

    this._log(`\n👤 Processing: ${user.name} on ${moment(date).format('YYYY-MM-DD')}`);
    this._log(`   Punches: ${punches.length}`);

    // Extract earliest IN and latest OUT
    const bio_in = punches.length > 0 ? punches[0].punchTime : null;
    let bio_out = null;

    if (punches.length > 1) {
      // Check if last punch is different from first (not same punch)
      const timeDiff = (punches[punches.length - 1].punchTime - bio_in) / (1000 * 60);
      if (timeDiff > 30) {
        bio_out = punches[punches.length - 1].punchTime;
      }
    }

    // Get existing workflow attendance
    const existingAttendance = await DailyAttendance.findOne({
      user: user._id,
      date: date
    });

    const wf_in = existingAttendance?.startDayTime || null;
    const wf_out = existingAttendance?.endDayTime || null;

    // Apply merge logic
    const mergeData = {
      employee_id: user._id,
      date: date,
      wf_in: wf_in,
      wf_out: wf_out,
      bio_in: bio_in,
      bio_out: bio_out
    };

    const merged = await this.mergeLogic.mergeAttendance(mergeData);

    // Get employee master for salary
    const employeeMaster = await EmployeeMaster.findOne({ user: user._id });

    // Calculate salary impact
    const hourlyRate = employeeMaster?.calculatedHourlyRate || 0;
    const dailyRate = employeeMaster?.calculatedDailyRate || 0;

    const basicSalaryForDay = this._calculateDaySalary(
      merged.worked_hours_decimal,
      hourlyRate,
      dailyRate
    );

    // Create or update attendance record
    const attendanceUpdate = {
      $set: {
        user: user._id,
        date: date,
        biometricTimeIn: merged.final_in,
        biometricTimeOut: merged.final_out,
        totalHoursWorked: merged.worked_hours_decimal,
        isPresent: merged.is_present,
        status: merged.status,
        verificationMethod: 'Biometric',
        basicSalaryForDay: basicSalaryForDay,
        attendanceMergeDetails: {
          case: merged.merge_case,
          remarks: merged.merge_remarks,
          wfTimeIn: wf_in,
          wfTimeOut: wf_out,
          bioTimeIn: bio_in,
          bioTimeOut: bio_out,
          timeDifferences: merged.time_diffs
        }
      }
    };

    const attendance = await DailyAttendance.findOneAndUpdate(
      { user: user._id, date: date },
      attendanceUpdate,
      { upsert: true, new: true }
    );

    // Mark punches as processed
    for (const punch of punches) {
      punch.isProcessed = true;
      punch.processedIntoAttendance = attendance._id;
      await punch.save();
    }

    this._log(`   Final IN: ${moment(merged.final_in).format('HH:mm:ss')}`);
    this._log(`   Final OUT: ${merged.final_out ? moment(merged.final_out).format('HH:mm:ss') : 'N/A'}`);
    this._log(`   Worked: ${merged.worked_hours_decimal}h | Status: ${merged.status}`);
    this._log(`   Case: ${merged.merge_case} | ${merged.merge_remarks}`);

    return {
      user: user._id,
      date: date,
      status: existingAttendance ? 'updated' : 'created',
      mergeDetails: merged,
      attendance: attendance._id
    };
  }

  /**
   * Mark days with no attendance as absent
   */
  async markAbsentDays(startDate, endDate) {
    try {
      const start = moment(startDate).tz('Asia/Kolkata').startOf('day');
      const end = moment(endDate).tz('Asia/Kolkata').endOf('day');

      // Get all active users
      const users = await User.find({ isActive: true }).select('_id');

      let markedAbsent = 0;

      for (const user of users) {
        // Check each day in range
        let currentDay = moment(start);

        while (currentDay <= end) {
          // Skip weekends
          if (currentDay.day() !== 0 && currentDay.day() !== 6) {
            const dayStart = currentDay.clone().startOf('day').toDate();
            const dayEnd = currentDay.clone().endOf('day').toDate();

            // Check if attendance exists
            const attendance = await DailyAttendance.findOne({
              user: user._id,
              date: { $gte: dayStart, $lte: dayEnd }
            });

            if (!attendance) {
              // Mark absent
              await DailyAttendance.create({
                user: user._id,
                date: dayStart,
                status: 'Absent',
                isPresent: false,
                verificationMethod: 'Auto'
              });
              markedAbsent++;
            }
          }

          currentDay.add(1, 'day');
        }
      }

      return { markedAbsent };

    } catch (error) {
      console.error('Error marking absent days:', error);
      throw error;
    }
  }

  /**
   * Helper: Calculate day salary
   */
  _calculateDaySalary(workedHours, hourlyRate, dailyRate) {
    if (hourlyRate > 0) {
      return workedHours * hourlyRate;
    } else if (dailyRate > 0) {
      return (workedHours / 8) * dailyRate;
    }
    return 0;
  }

  /**
   * Helper: Extract field from row
   */
  extractField(row, fieldNames) {
    if (!row) return null;

    for (const fieldName of fieldNames) {
      const key = Object.keys(row).find(k => 
        k.toLowerCase().trim() === fieldName.toLowerCase().trim()
      );

      if (key && row[key]) {
        return row[key].toString().trim();
      }
    }

    return null;
  }

  /**
   * Helper: Parse date/time
   */
  parseDateTime(dateStr) {
    if (!dateStr) return null;

    for (const format of this.dateFormats) {
      const parsed = moment(dateStr, format, true);
      if (parsed.isValid()) {
        return parsed.tz('Asia/Kolkata').toDate();
      }
    }

    return null;
  }

  /**
   * Logging helper
   */
  _log(message) {
    if (this.debug) {
      console.log(`[BiometricProcessor] ${message}`);
    }
  }
}

module.exports = EnhancedBiometricProcessor;
