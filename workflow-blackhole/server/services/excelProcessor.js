const XLSX = require('xlsx');
const moment = require('moment');
const User = require('../models/User');
const Attendance = require('../models/Attendance');
const BiometricUpload = require('../models/BiometricUpload');

class ExcelProcessor {
  constructor() {
    this.defaultColumnMappings = {
      employeeId: ['employee_id', 'emp_id', 'id', 'employee id', 'emp id'],
      employeeName: ['employee_name', 'emp_name', 'name', 'employee name', 'emp name', 'full name'],
      date: ['date', 'attendance_date', 'work_date', 'day'],
      timeIn: ['time_in', 'in_time', 'check_in', 'start_time', 'punch_in', 'entry_time'],
      timeOut: ['time_out', 'out_time', 'check_out', 'end_time', 'punch_out', 'exit_time'],
      deviceId: ['device_id', 'device', 'terminal_id', 'machine_id'],
      location: ['location', 'office', 'branch', 'site']
    };
  }

  async processExcelFile(filePath, uploadRecord) {
    try {
      console.log('Starting Excel processing for:', filePath);
      
      // Read the Excel file
      const workbook = XLSX.readFile(filePath);
      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      
      // Convert to JSON
      const rawData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
      
      if (rawData.length < 2) {
        throw new Error('Excel file must contain at least a header row and one data row');
      }

      const headers = rawData[0].map(h => String(h).toLowerCase().trim());
      const dataRows = rawData.slice(1);

      // Update upload record with preview
      uploadRecord.preview = {
        headers: rawData[0],
        sampleRows: dataRows.slice(0, 5),
        totalRows: dataRows.length,
        detectedFormat: this.detectFormat(headers)
      };

      // Auto-detect column mappings
      const columnMappings = this.detectColumnMappings(headers);
      uploadRecord.mappingConfig = columnMappings;

      console.log('Detected column mappings:', columnMappings);

      // Process each row
      const processedData = [];
      const errors = [];
      const warnings = [];

      for (let i = 0; i < dataRows.length; i++) {
        const row = dataRows[i];
        const rowIndex = i + 2; // +2 because Excel is 1-indexed and we skipped header

        try {
          const processedRow = await this.processRow(row, headers, columnMappings, rowIndex);
          if (processedRow) {
            processedData.push(processedRow);
          }
        } catch (error) {
          errors.push({
            row: rowIndex,
            error: error.message,
            data: row
          });
          uploadRecord.addError(rowIndex, error.message, row);
        }
      }

      // Update upload record
      uploadRecord.totalRecords = dataRows.length;
      uploadRecord.successfulMatches = processedData.length;
      uploadRecord.errorLog = errors;
      uploadRecord.warningLog = warnings;

      // Generate summary
      const summary = this.generateSummary(processedData);
      uploadRecord.summary = summary;

      // Compare with existing attendance data
      const comparisonResults = await this.compareWithStartDayData(processedData, uploadRecord);
      uploadRecord.comparisonResults = comparisonResults;
      uploadRecord.discrepancies = comparisonResults.filter(r => r.discrepancy.hasDiscrepancy).length;

      await uploadRecord.updateStatus('Completed');

      console.log(`Excel processing completed. Processed: ${processedData.length}, Errors: ${errors.length}`);

      return {
        success: true,
        processedData,
        summary,
        comparisonResults,
        errors,
        warnings
      };

    } catch (error) {
      console.error('Excel processing error:', error);
      await uploadRecord.updateStatus('Failed');
      uploadRecord.addError(0, error.message);
      await uploadRecord.save();
      throw error;
    }
  }

  detectFormat(headers) {
    const standardHeaders = ['employee_id', 'date', 'time_in', 'time_out'];
    const matchCount = headers.filter(h => 
      standardHeaders.some(sh => h.includes(sh.toLowerCase()))
    ).length;

    if (matchCount >= 3) return 'Standard';
    if (matchCount >= 2) return 'Custom';
    return 'Unknown';
  }

  detectColumnMappings(headers) {
    const mappings = {};

    for (const [field, possibleNames] of Object.entries(this.defaultColumnMappings)) {
      const matchedIndex = headers.findIndex(header => 
        possibleNames.some(name => header.includes(name.toLowerCase()))
      );
      
      if (matchedIndex !== -1) {
        mappings[`${field}Column`] = headers[matchedIndex];
      }
    }

    return mappings;
  }

  async processRow(row, headers, mappings, rowIndex) {
    const data = {};

    // Extract data based on mappings
    for (const [field, columnName] of Object.entries(mappings)) {
      const fieldName = field.replace('Column', '');
      const columnIndex = headers.indexOf(columnName);
      
      if (columnIndex !== -1 && row[columnIndex] !== undefined) {
        data[fieldName] = row[columnIndex];
      }
    }

    // Validate required fields
    if (!data.employeeId && !data.employeeName) {
      throw new Error('Employee ID or Name is required');
    }

    if (!data.date) {
      throw new Error('Date is required');
    }

    if (!data.timeIn) {
      throw new Error('Time In is required');
    }

    // Parse and validate date
    const parsedDate = this.parseDate(data.date);
    if (!parsedDate.isValid()) {
      throw new Error(`Invalid date format: ${data.date}`);
    }

    // Parse times
    const timeIn = this.parseTime(data.timeIn, parsedDate);
    const timeOut = data.timeOut ? this.parseTime(data.timeOut, parsedDate) : null;

    // Find user
    const user = await this.findUser(data.employeeId, data.employeeName);
    if (!user) {
      throw new Error(`Employee not found: ${data.employeeId || data.employeeName}`);
    }

    return {
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        employeeId: data.employeeId
      },
      date: parsedDate.toDate(),
      biometricTimeIn: timeIn,
      biometricTimeOut: timeOut,
      deviceId: data.deviceId || 'Unknown',
      location: data.location || 'Main Office',
      hoursWorked: timeOut ? moment(timeOut).diff(moment(timeIn), 'hours', true) : 0,
      rawData: data
    };
  }

  parseDate(dateValue) {
    // Try multiple date formats
    const formats = [
      'YYYY-MM-DD',
      'MM/DD/YYYY',
      'DD/MM/YYYY',
      'DD-MM-YYYY',
      'MM-DD-YYYY',
      'YYYY/MM/DD'
    ];

    for (const format of formats) {
      const parsed = moment(dateValue, format, true);
      if (parsed.isValid()) {
        return parsed;
      }
    }

    // Try Excel date number
    if (typeof dateValue === 'number') {
      const excelDate = XLSX.SSF.parse_date_code(dateValue);
      return moment(new Date(excelDate.y, excelDate.m - 1, excelDate.d));
    }

    return moment(dateValue);
  }

  parseTime(timeValue, baseDate) {
    if (!timeValue) return null;

    // If it's already a Date object
    if (timeValue instanceof Date) {
      return timeValue;
    }

    // If it's a number (Excel time format)
    if (typeof timeValue === 'number') {
      const hours = Math.floor(timeValue * 24);
      const minutes = Math.floor((timeValue * 24 * 60) % 60);
      return baseDate.clone().hour(hours).minute(minutes).second(0).toDate();
    }

    // Parse time string
    const timeStr = String(timeValue).trim();
    const timeFormats = ['HH:mm:ss', 'HH:mm', 'h:mm A', 'h:mm:ss A', 'HH.mm', 'HHmm'];

    for (const format of timeFormats) {
      const parsed = moment(timeStr, format, true);
      if (parsed.isValid()) {
        return baseDate.clone()
          .hour(parsed.hour())
          .minute(parsed.minute())
          .second(parsed.second())
          .toDate();
      }
    }

    throw new Error(`Invalid time format: ${timeValue}`);
  }

  async findUser(employeeId, employeeName) {
    let user = null;

    // Try to find by employee ID first
    if (employeeId) {
      const UserTag = require('../models/UserTag');
      const userTag = await UserTag.findOne({ 
        $or: [
          { employeeId: employeeId },
          { 'user.employeeId': employeeId }
        ]
      }).populate('user');
      
      if (userTag && userTag.user) {
        user = userTag.user;
      }
    }

    // If not found, try by name
    if (!user && employeeName) {
      user = await User.findOne({
        name: { $regex: new RegExp(employeeName, 'i') }
      });
    }

    // If still not found, try by email (if employeeId looks like email)
    if (!user && employeeId && employeeId.includes('@')) {
      user = await User.findOne({ email: employeeId.toLowerCase() });
    }

    return user;
  }

  generateSummary(processedData) {
    if (processedData.length === 0) {
      return {
        dateRange: { start: null, end: null },
        employeesProcessed: [],
        departmentsAffected: [],
        averageWorkingHours: 0,
        totalWorkingDays: 0,
        attendanceRate: 0
      };
    }

    const dates = processedData.map(d => d.date).sort();
    const employees = [...new Set(processedData.map(d => d.user.id))];
    const totalHours = processedData.reduce((sum, d) => sum + (d.hoursWorked || 0), 0);

    return {
      dateRange: {
        start: dates[0],
        end: dates[dates.length - 1]
      },
      employeesProcessed: employees,
      departmentsAffected: [], // Will be populated later
      averageWorkingHours: totalHours / processedData.length,
      totalWorkingDays: processedData.length,
      attendanceRate: 100 // Will be calculated based on expected vs actual
    };
  }

  async compareWithStartDayData(processedData, uploadRecord) {
    const comparisonResults = [];

    for (const biometricRecord of processedData) {
      try {
        // Find corresponding start day attendance
        const startDayRecord = await Attendance.findOne({
          user: biometricRecord.user.id,
          date: {
            $gte: moment(biometricRecord.date).startOf('day').toDate(),
            $lte: moment(biometricRecord.date).endOf('day').toDate()
          }
        });

        const comparison = {
          date: biometricRecord.date,
          employee: biometricRecord.user,
          biometric: {
            timeIn: biometricRecord.biometricTimeIn,
            timeOut: biometricRecord.biometricTimeOut,
            deviceId: biometricRecord.deviceId,
            location: biometricRecord.location
          },
          startDay: startDayRecord ? {
            timeIn: startDayRecord.startDayTime,
            timeOut: startDayRecord.endDayTime,
            location: startDayRecord.startDayLocation
          } : null,
          discrepancy: {
            hasDiscrepancy: false,
            timeInDiff: 0,
            timeOutDiff: 0,
            locationMismatch: false,
            notes: ''
          },
          recommendation: {
            action: 'Accept Biometric',
            confidence: 1.0,
            reason: 'No start day record found'
          }
        };

        if (startDayRecord) {
          // Calculate time differences
          const timeInDiff = Math.abs(
            moment(biometricRecord.biometricTimeIn).diff(moment(startDayRecord.startDayTime), 'minutes')
          );
          
          let timeOutDiff = 0;
          if (biometricRecord.biometricTimeOut && startDayRecord.endDayTime) {
            timeOutDiff = Math.abs(
              moment(biometricRecord.biometricTimeOut).diff(moment(startDayRecord.endDayTime), 'minutes')
            );
          }

          // Determine if there's a discrepancy (threshold: 15 minutes)
          const hasTimeDiscrepancy = timeInDiff > 15 || timeOutDiff > 15;
          
          comparison.discrepancy = {
            hasDiscrepancy: hasTimeDiscrepancy,
            timeInDiff,
            timeOutDiff,
            locationMismatch: false, // Will implement location comparison later
            notes: hasTimeDiscrepancy ? `Time difference: In ${timeInDiff}min, Out ${timeOutDiff}min` : ''
          };

          // Generate recommendation
          if (!hasTimeDiscrepancy) {
            comparison.recommendation = {
              action: 'Accept Biometric',
              confidence: 0.95,
              reason: 'Times match within acceptable range'
            };
          } else if (timeInDiff <= 30 && timeOutDiff <= 30) {
            comparison.recommendation = {
              action: 'Accept Biometric',
              confidence: 0.7,
              reason: 'Minor time difference, biometric likely more accurate'
            };
          } else {
            comparison.recommendation = {
              action: 'Manual Review',
              confidence: 0.3,
              reason: 'Significant time difference requires review'
            };
          }
        }

        comparisonResults.push(comparison);

      } catch (error) {
        console.error('Error comparing record:', error);
        uploadRecord.addWarning(0, `Comparison error for ${biometricRecord.user.name}: ${error.message}`);
      }
    }

    return comparisonResults;
  }
}

module.exports = new ExcelProcessor();
