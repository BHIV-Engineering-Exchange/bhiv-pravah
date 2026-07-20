const ExcelJS = require('exceljs');
const User = require('../models/User');
const Attendance = require('../models/Attendance');

class ExcelProcessor {
  constructor() {
    this.supportedFormats = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel'
    ];
  }

  /**
   * Validate Excel file format
   */
  validateFile(file) {
    if (!file) {
      throw new Error('No file provided');
    }

    if (!this.supportedFormats.includes(file.mimetype)) {
      throw new Error('Invalid file format. Only Excel files (.xlsx, .xls) are supported');
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      throw new Error('File size too large. Maximum size is 10MB');
    }

    return true;
  }

  /**
   * Parse Excel file and extract attendance data
   */
  async parseAttendanceFile(fileBuffer, options = {}) {
    try {
      const workbook = new ExcelJS.Workbook();
      await workbook.xlsx.load(fileBuffer);
      
      const worksheet = workbook.getWorksheet(1);
      if (!worksheet) {
        throw new Error('No worksheet found in Excel file');
      }

      const attendanceData = [];
      const errors = [];
      const warnings = [];

      // Expected column mapping (can be customized)
      const columnMapping = options.columnMapping || {
        employeeId: 1,
        date: 2,
        timeIn: 3,
        timeOut: 4,
        deviceId: 5,
        location: 6
      };

      // Validate headers
      const headerRow = worksheet.getRow(1);
      const expectedHeaders = ['Employee ID', 'Date', 'Time In', 'Time Out', 'Device ID', 'Location'];
      
      let rowCount = 0;
      worksheet.eachRow((row, rowNumber) => {
        if (rowNumber === 1) {
          // Validate headers
          const headers = [];
          for (let i = 1; i <= 6; i++) {
            headers.push(row.getCell(i).value);
          }
          
          // Check if headers match expected format
          const headerMatch = expectedHeaders.every((header, index) => {
            const cellValue = headers[index];
            return cellValue && cellValue.toString().toLowerCase().includes(header.toLowerCase().split(' ')[0]);
          });

          if (!headerMatch) {
            warnings.push('Headers may not match expected format. Expected: Employee ID, Date, Time In, Time Out, Device ID, Location');
          }
          return;
        }

        rowCount++;
        
        try {
          const employeeId = this.getCellValue(row, columnMapping.employeeId);
          const date = this.getCellValue(row, columnMapping.date);
          const timeIn = this.getCellValue(row, columnMapping.timeIn);
          const timeOut = this.getCellValue(row, columnMapping.timeOut);
          const deviceId = this.getCellValue(row, columnMapping.deviceId) || 'Unknown';
          const location = this.getCellValue(row, columnMapping.location) || 'Main Office';

          // Skip empty rows
          if (!employeeId && !date) {
            return;
          }

          // Validate required fields
          if (!employeeId) {
            errors.push(`Row ${rowNumber}: Missing employee ID`);
            return;
          }

          if (!date) {
            errors.push(`Row ${rowNumber}: Missing date`);
            return;
          }

          // Parse and validate date
          let parsedDate;
          try {
            parsedDate = this.parseDate(date);
          } catch (dateError) {
            errors.push(`Row ${rowNumber}: Invalid date format - ${dateError.message}`);
            return;
          }

          // Parse time values
          const biometricTimeIn = this.parseTime(timeIn, parsedDate);
          const biometricTimeOut = this.parseTime(timeOut, parsedDate);

          // Validate time logic
          if (biometricTimeIn && biometricTimeOut && biometricTimeIn >= biometricTimeOut) {
            warnings.push(`Row ${rowNumber}: Time out is not after time in`);
          }

          attendanceData.push({
            employeeId: employeeId.toString().trim(),
            date: new Date(parsedDate.getFullYear(), parsedDate.getMonth(), parsedDate.getDate()),
            biometricTimeIn,
            biometricTimeOut,
            biometricDeviceId: deviceId.toString(),
            biometricLocation: location.toString(),
            source: 'Biometric',
            rawData: {
              row: rowNumber,
              originalDate: date,
              originalTimeIn: timeIn,
              originalTimeOut: timeOut
            }
          });

        } catch (error) {
          errors.push(`Row ${rowNumber}: ${error.message}`);
        }
      });

      return {
        success: true,
        data: attendanceData,
        summary: {
          totalRows: rowCount,
          validRecords: attendanceData.length,
          errors: errors.length,
          warnings: warnings.length
        },
        errors,
        warnings
      };

    } catch (error) {
      throw new Error(`Failed to parse Excel file: ${error.message}`);
    }
  }

  /**
   * Process attendance data and save to database
   */
  async processAttendanceData(attendanceData, options = {}) {
    const processedRecords = [];
    const skippedRecords = [];
    const userCache = new Map();

    for (const record of attendanceData) {
      try {
        // Find user (with caching)
        let user = userCache.get(record.employeeId);
        if (!user) {
          user = await this.findUserByEmployeeId(record.employeeId);
          if (user) {
            userCache.set(record.employeeId, user);
          }
        }

        if (!user) {
          skippedRecords.push({
            employeeId: record.employeeId,
            date: record.date,
            reason: 'User not found in system'
          });
          continue;
        }

        // Check if attendance record already exists
        const existingRecord = await Attendance.findOne({
          user: user._id,
          date: record.date
        });

        if (existingRecord) {
          // Update existing record with biometric data
          const updated = await this.updateAttendanceRecord(existingRecord, record);
          processedRecords.push({
            employeeId: record.employeeId,
            userName: user.name,
            date: record.date,
            action: 'Updated',
            changes: updated.changes
          });
        } else {
          // Create new attendance record
          const newAttendance = await this.createAttendanceRecord(user._id, record);
          processedRecords.push({
            employeeId: record.employeeId,
            userName: user.name,
            date: record.date,
            action: 'Created',
            recordId: newAttendance._id
          });
        }

      } catch (error) {
        skippedRecords.push({
          employeeId: record.employeeId,
          date: record.date,
          reason: error.message
        });
      }
    }

    return {
      processed: processedRecords,
      skipped: skippedRecords,
      summary: {
        totalRecords: attendanceData.length,
        processed: processedRecords.length,
        skipped: skippedRecords.length,
        successRate: Math.round((processedRecords.length / attendanceData.length) * 100)
      }
    };
  }

  /**
   * Helper methods
   */
  getCellValue(row, columnIndex) {
    const cell = row.getCell(columnIndex);
    return cell.value;
  }

  parseDate(dateValue) {
    if (dateValue instanceof Date) {
      return dateValue;
    }

    if (typeof dateValue === 'string') {
      const parsed = new Date(dateValue);
      if (isNaN(parsed.getTime())) {
        throw new Error(`Invalid date: ${dateValue}`);
      }
      return parsed;
    }

    if (typeof dateValue === 'number') {
      // Excel serial date
      const excelEpoch = new Date(1900, 0, 1);
      const days = dateValue - 2; // Excel has a leap year bug
      return new Date(excelEpoch.getTime() + days * 24 * 60 * 60 * 1000);
    }

    throw new Error(`Unsupported date format: ${typeof dateValue}`);
  }

  parseTime(timeValue, baseDate) {
    if (!timeValue) return null;

    const date = new Date(baseDate);

    if (timeValue instanceof Date) {
      date.setHours(timeValue.getHours(), timeValue.getMinutes(), timeValue.getSeconds());
      return date;
    }

    if (typeof timeValue === 'string') {
      const timeMatch = timeValue.match(/(\d{1,2}):(\d{2})(?::(\d{2}))?/);
      if (timeMatch) {
        const hours = parseInt(timeMatch[1]);
        const minutes = parseInt(timeMatch[2]);
        const seconds = parseInt(timeMatch[3] || '0');
        date.setHours(hours, minutes, seconds);
        return date;
      }
    }

    if (typeof timeValue === 'number') {
      // Excel time serial (fraction of a day)
      const totalMinutes = Math.round(timeValue * 24 * 60);
      const hours = Math.floor(totalMinutes / 60);
      const minutes = totalMinutes % 60;
      date.setHours(hours, minutes, 0);
      return date;
    }

    return null;
  }

  async findUserByEmployeeId(employeeId) {
    // Try multiple search strategies
    const searchStrategies = [
      { email: { $regex: employeeId, $options: 'i' } },
      { name: { $regex: employeeId, $options: 'i' } },
      { 'employeeId': employeeId }, // If you have a dedicated employeeId field
    ];

    for (const strategy of searchStrategies) {
      const user = await User.findOne(strategy);
      if (user) return user;
    }

    return null;
  }

  async updateAttendanceRecord(existingRecord, newData) {
    const changes = [];

    if (newData.biometricTimeIn) {
      existingRecord.biometricTimeIn = newData.biometricTimeIn;
      changes.push('biometric time in');
    }

    if (newData.biometricTimeOut) {
      existingRecord.biometricTimeOut = newData.biometricTimeOut;
      changes.push('biometric time out');
    }

    existingRecord.biometricDeviceId = newData.biometricDeviceId;
    existingRecord.biometricLocation = newData.biometricLocation;

    if (existingRecord.source === 'StartDay') {
      existingRecord.source = 'Both';
      changes.push('source updated to Both');
    } else {
      existingRecord.source = 'Biometric';
    }

    await existingRecord.save();
    return { record: existingRecord, changes };
  }

  async createAttendanceRecord(userId, data) {
    const newAttendance = new Attendance({
      user: userId,
      date: data.date,
      biometricTimeIn: data.biometricTimeIn,
      biometricTimeOut: data.biometricTimeOut,
      biometricDeviceId: data.biometricDeviceId,
      biometricLocation: data.biometricLocation,
      source: 'Biometric'
    });

    return await newAttendance.save();
  }

  /**
   * Generate Excel template for attendance data
   */
  async generateTemplate() {
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet('Attendance Template');

    // Add headers
    const headers = ['Employee ID', 'Date', 'Time In', 'Time Out', 'Device ID', 'Location'];
    worksheet.addRow(headers);

    // Style headers
    const headerRow = worksheet.getRow(1);
    headerRow.font = { bold: true };
    headerRow.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FFE0E0E0' }
    };

    // Add sample data
    worksheet.addRow(['EMP001', '2025-08-07', '09:00', '17:30', 'DEVICE_01', 'Main Office']);
    worksheet.addRow(['EMP002', '2025-08-07', '09:15', '17:45', 'DEVICE_01', 'Main Office']);

    // Auto-fit columns
    worksheet.columns.forEach(column => {
      column.width = 15;
    });

    return workbook;
  }
}

module.exports = new ExcelProcessor();
