const BiometricPunch = require('../models/BiometricPunch');
const DailyAttendance = require('../models/DailyAttendance');
const EmployeeMaster = require('../models/EmployeeMaster');
const User = require('../models/User');
const BiometricUpload = require('../models/BiometricUpload');
const XLSX = require('xlsx');
const csv = require('csv-parser');
const fs = require('fs');
const moment = require('moment');

class BiometricProcessor {
  constructor() {
    this.dateFormats = [
      'YYYY-MM-DD HH:mm:ss',
      'DD/MM/YYYY HH:mm:ss',
      'MM/DD/YYYY HH:mm:ss',
      'DD-MM-YYYY HH:mm:ss',
      'YYYY/MM/DD HH:mm:ss',
      'DD/MM/YYYY HH:mm',
      'MM/DD/YYYY HH:mm'
    ];
  }

  /**
   * Parse uploaded biometric file (CSV or Excel)
   */
  async parseFile(filePath, fileName, uploadedBy) {
    try {
      const ext = fileName.split('.').pop().toLowerCase();
      let data = [];

      if (ext === 'csv') {
        data = await this.parseCSV(filePath);
      } else if (ext === 'xlsx' || ext === 'xls') {
        data = await this.parseExcel(filePath);
      } else {
        throw new Error('Unsupported file format. Please upload CSV or Excel files.');
      }

      // Create upload record
      const uploadRecord = new BiometricUpload({
        fileName: fileName,
        originalFileName: fileName,
        filePath: filePath,
        fileSize: fs.statSync(filePath).size,
        processedBy: uploadedBy,
        totalRecords: data.length,
        status: 'Processing',
        uploadDate: new Date()
      });

      await uploadRecord.save();

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

      await uploadRecord.save();

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
   * Process biometric data and create punch records
   */
  async processBiometricData(data, uploadBatchId) {
    const result = {
      successfulMatches: 0,
      discrepancies: 0,
      newRecords: 0,
      updatedRecords: 0,
      processedRecords: 0,
      errors: []
    };

    for (const row of data) {
      try {
        // Extract employee identifier (try multiple common field names)
        const employeeId = this.extractField(row, [
          'employee_id', 'employeeid', 'emp_id', 'empid', 
          'id', 'employee', 'staff_id', 'staffid'
        ]);

        // Extract biometric ID if available
        const biometricId = this.extractField(row, [
          'biometric_id', 'biometricid', 'card_no', 'cardno',
          'badge_id', 'badgeid', 'device_id'
        ]);

        // Extract punch time
        const punchTimeStr = this.extractField(row, [
          'punch_time', 'punchtime', 'time', 'timestamp',
          'datetime', 'date_time', 'clock_time'
        ]);

        if (!employeeId || !punchTimeStr) {
          result.errors.push({
            row: row,
            error: 'Missing employee ID or punch time'
          });
          result.discrepancies++;
          continue;
        }

        // Parse the punch time
        const punchTime = this.parseDateTime(punchTimeStr);
        if (!punchTime) {
          result.errors.push({
            row: row,
            error: 'Invalid date/time format: ' + punchTimeStr
          });
          result.discrepancies++;
          continue;
        }

        // Extract date (without time)
        const date = new Date(punchTime);
        date.setHours(0, 0, 0, 0);

        // Extract additional fields
        const deviceId = this.extractField(row, ['device_id', 'deviceid', 'machine', 'terminal']);
        const location = this.extractField(row, ['location', 'site', 'branch']);

        // Find matching user
        const user = await this.findMatchingUser(employeeId, biometricId);

        // Create biometric punch record
        const punch = new BiometricPunch({
          employeeId: employeeId,
          biometricId: biometricId,
          user: user?._id,
          punchTime: punchTime,
          date: date,
          deviceId: deviceId,
          location: location,
          uploadBatch: uploadBatchId,
          isProcessed: false,
          rawData: row
        });

        await punch.save();

        if (user) {
          result.successfulMatches++;
        } else {
          result.discrepancies++;
          result.errors.push({
            employeeId: employeeId,
            biometricId: biometricId,
            error: 'No matching user found'
          });
        }

        result.newRecords++;
        result.processedRecords++;

      } catch (error) {
        console.error('Error processing row:', error);
        result.errors.push({
          row: row,
          error: error.message
        });
        result.discrepancies++;
      }
    }

    return result;
  }

  /**
   * Group punches by employee and date, then derive attendance
   */
  async deriveDailyAttendance(startDate, endDate) {
    try {
      const start = new Date(startDate);
      start.setHours(0, 0, 0, 0);
      
      const end = new Date(endDate);
      end.setHours(23, 59, 59, 999);

      // Find all unprocessed punches in date range
      const punches = await BiometricPunch.find({
        date: { $gte: start, $lte: end },
        user: { $exists: true, $ne: null }
      }).sort({ punchTime: 1 });

      console.log(`📊 Processing ${punches.length} biometric punches...`);

      // Group by user and date
      const grouped = {};
      
      for (const punch of punches) {
        const userId = punch.user.toString();
        const dateKey = punch.date.toISOString().split('T')[0];
        const key = `${userId}_${dateKey}`;

        if (!grouped[key]) {
          grouped[key] = {
            user: punch.user,
            date: punch.date,
            punches: []
          };
        }

        grouped[key].punches.push(punch);
      }

      // Process each group
      const results = {
        created: 0,
        updated: 0,
        errors: []
      };

      for (const key in grouped) {
        try {
          const group = grouped[key];
          await this.createOrUpdateAttendance(group);
          results.created++;
        } catch (error) {
          console.error(`Error processing attendance for ${key}:`, error);
          results.errors.push({
            key: key,
            error: error.message
          });
        }
      }

      // Mark absent days
      await this.markAbsentDays(start, end);

      return results;

    } catch (error) {
      console.error('❌ Error deriving daily attendance:', error);
      throw error;
    }
  }

  /**
   * Create or update daily attendance from punch data
   */
  async createOrUpdateAttendance(group) {
    try {
      const { user, date, punches } = group;

      // Sort punches by time
      punches.sort((a, b) => a.punchTime - b.punchTime);

      // First punch = In, Last punch = Out
      const firstPunch = punches[0];
      const lastPunch = punches[punches.length - 1];

      // Check if last punch is too close to first (less than 30 minutes)
      const timeDiff = (lastPunch.punchTime - firstPunch.punchTime) / (1000 * 60);
      
      let punchOut = null;
      if (timeDiff > 30 && punches.length > 1) {
        punchOut = lastPunch.punchTime;
      }

      // Calculate worked hours
      let totalHours = 0;
      let regularHours = 0;
      let overtimeHours = 0;

      if (punchOut) {
        const hours = (punchOut - firstPunch.punchTime) / (1000 * 60 * 60);
        totalHours = Math.round(hours * 100) / 100;
        
        const standardHours = 8;
        regularHours = Math.min(totalHours, standardHours);
        overtimeHours = Math.max(0, totalHours - standardHours);
      } else {
        // Only punch in, no punch out - mark as incomplete
        // Assume still working or forgot to punch out
        totalHours = 0;
      }

      // Determine status
      let status = 'Present';
      if (totalHours === 0 && !punchOut) {
        status = 'Absent'; // No punch out means incomplete
      } else if (totalHours < 4) {
        status = 'Half Day';
      } else if (firstPunch.punchTime.getHours() > 9) {
        status = 'Late';
      }

      // Get employee master for salary calculation
      const employeeMaster = await EmployeeMaster.findOne({ user: user });
      const hourlyRate = employeeMaster?.calculatedHourlyRate || 0;

      // Find or create attendance record
      const attendance = await DailyAttendance.findOneAndUpdate(
        { user: user, date: date },
        {
          $set: {
            biometricTimeIn: firstPunch.punchTime,
            biometricTimeOut: punchOut,
            biometricDeviceId: firstPunch.deviceId,
            biometricLocation: firstPunch.location,
            totalHoursWorked: totalHours,
            regularHours: regularHours,
            overtimeHours: overtimeHours,
            status: status,
            isPresent: totalHours > 0,
            isVerified: true,
            verificationMethod: 'Biometric',
            hasDiscrepancy: !punchOut && punches.length > 0,
            discrepancyType: !punchOut && punches.length > 0 ? 'Missing Data' : null,
            discrepancyDetails: !punchOut && punches.length > 0 ? {
              description: 'Missing punch out time - incomplete record'
            } : null,
            dailyWage: hourlyRate * regularHours,
            earnedAmount: (hourlyRate * regularHours) + (hourlyRate * overtimeHours * 1.5)
          }
        },
        { upsert: true, new: true }
      );

      // Mark punches as processed
      await BiometricPunch.updateMany(
        { _id: { $in: punches.map(p => p._id) } },
        { 
          $set: { 
            isProcessed: true,
            processedIntoAttendance: attendance._id,
            punchType: punches[0]._id.equals(firstPunch._id) ? 'In' : 
                      punches[punches.length - 1]._id.equals(lastPunch._id) ? 'Out' : 'Unknown'
          }
        }
      );

      return attendance;

    } catch (error) {
      console.error('Error creating/updating attendance:', error);
      throw error;
    }
  }

  /**
   * Mark absent days for employees with no punches
   */
  async markAbsentDays(startDate, endDate) {
    try {
      // Get all active users
      const users = await User.find({ stillExist: 1 }).select('_id');
      
      // For each day in range
      const currentDate = new Date(startDate);
      
      while (currentDate <= endDate) {
        const dateOnly = new Date(currentDate);
        dateOnly.setHours(0, 0, 0, 0);

        // Skip weekends (Saturday = 6, Sunday = 0)
        const dayOfWeek = currentDate.getDay();
        if (dayOfWeek !== 0 && dayOfWeek !== 6) {
          
          for (const user of users) {
            // Check if attendance exists
            const existing = await DailyAttendance.findOne({
              user: user._id,
              date: dateOnly
            });

            if (!existing) {
              // No attendance record - mark as absent
              await DailyAttendance.create({
                user: user._id,
                date: dateOnly,
                status: 'Absent',
                isPresent: false,
                totalHoursWorked: 0,
                regularHours: 0,
                overtimeHours: 0,
                verificationMethod: 'Manual',
                earnedAmount: 0
              });
            }
          }
        }

        currentDate.setDate(currentDate.getDate() + 1);
      }

    } catch (error) {
      console.error('Error marking absent days:', error);
    }
  }

  /**
   * Helper: Extract field from row with multiple possible names
   */
  extractField(row, possibleNames) {
    for (const name of possibleNames) {
      const lowerName = name.toLowerCase();
      for (const key in row) {
        if (key.toLowerCase() === lowerName || 
            key.toLowerCase().replace(/[_\s-]/g, '') === lowerName.replace(/[_\s-]/g, '')) {
          return row[key];
        }
      }
    }
    return null;
  }

  /**
   * Helper: Parse date/time string with multiple formats
   */
  parseDateTime(dateTimeStr) {
    if (!dateTimeStr) return null;

    // Try moment with multiple formats
    for (const format of this.dateFormats) {
      const parsed = moment(dateTimeStr, format, true);
      if (parsed.isValid()) {
        return parsed.toDate();
      }
    }

    // Try native Date parsing as fallback
    const date = new Date(dateTimeStr);
    if (!isNaN(date.getTime())) {
      return date;
    }

    return null;
  }

  /**
   * Helper: Find matching user by employee ID or biometric ID
   */
  async findMatchingUser(employeeId, biometricId) {
    try {
      // First try employee master
      let employeeMaster = await EmployeeMaster.findOne({
        $or: [
          { employeeId: employeeId },
          { biometricId: biometricId }
        ]
      });

      if (employeeMaster) {
        return await User.findById(employeeMaster.user);
      }

      // Try finding user by email if employeeId looks like email
      if (employeeId && employeeId.includes('@')) {
        return await User.findOne({ email: employeeId });
      }

      // Try finding by name (less reliable)
      if (employeeId) {
        return await User.findOne({ 
          name: new RegExp(employeeId, 'i') 
        });
      }

      return null;

    } catch (error) {
      console.error('Error finding matching user:', error);
      return null;
    }
  }
}

module.exports = new BiometricProcessor();
