const express = require('express');
const router = express.Router();
const multer = require('multer');
const ExcelJS = require('exceljs');
const XLSX = require('xlsx');
const fs = require('fs');
const path = require('path');
const moment = require('moment');
const geolib = require('geolib');
const Attendance = require('../models/Attendance');
const BiometricUpload = require('../models/BiometricUpload');
const User = require('../models/User');
const UserTag = require('../models/UserTag');
const auth = require('../middleware/auth');
const adminAuth = require('../middleware/adminAuth');

// Configure multer for Excel file uploads with proper error handling
const upload = multer({
  storage: multer.diskStorage({
    destination: (req, file, cb) => {
      const uploadDir = 'uploads/';
      if (!fs.existsSync(uploadDir)) {
        fs.mkdirSync(uploadDir, { recursive: true });
      }
      cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
      cb(null, `${Date.now()}-${file.originalname}`);
    }
  }),
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB limit
  },
  fileFilter: (req, file, cb) => {
    if (file.mimetype === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
        file.mimetype === 'application/vnd.ms-excel' ||
        file.mimetype === 'text/csv') {
      cb(null, true);
    } else {
      cb(new Error('Only Excel files are allowed'), false);
    }
  }
});

// Upload and process biometric Excel file - FIXED VERSION
router.post('/upload', auth, (req, res) => {
  upload.single('excelFile')(req, res, async (err) => {
    if (err) {
      console.error('Multer error:', err);
      return res.status(400).json({ 
        success: false,
        error: err.message || 'File upload error' 
      });
    }

    try {
      if (!req.file) {
        return res.status(400).json({ 
          success: false,
          error: 'No Excel file uploaded' 
        });
      }

      const workbook = new ExcelJS.Workbook();
      await workbook.xlsx.readFile(req.file.path);
      
      const worksheet = workbook.getWorksheet(1);
      const attendanceData = [];
      const errors = [];
      
      // Process each row (skip header)
      worksheet.eachRow((row, rowNumber) => {
        if (rowNumber === 1) return; // Skip header
        
        try {
          const employeeId = row.getCell(1).value;
          const date = new Date(row.getCell(2).value);
          const timeIn = row.getCell(3).value;
          const timeOut = row.getCell(4).value;
          const deviceId = row.getCell(5).value || 'Unknown';
          const location = row.getCell(6).value || 'Main Office';
          
          if (!employeeId || !date) {
            errors.push(`Row ${rowNumber}: Missing employee ID or date`);
            return;
          }
          
          // Parse time values
          let biometricTimeIn, biometricTimeOut;
          
          if (timeIn) {
            if (typeof timeIn === 'string') {
              const [hours, minutes] = timeIn.split(':');
              biometricTimeIn = new Date(date);
              biometricTimeIn.setHours(parseInt(hours), parseInt(minutes), 0, 0);
            } else if (timeIn instanceof Date) {
              biometricTimeIn = new Date(date);
              biometricTimeIn.setHours(timeIn.getHours(), timeIn.getMinutes(), 0, 0);
            }
          }
          
          if (timeOut) {
            if (typeof timeOut === 'string') {
              const [hours, minutes] = timeOut.split(':');
              biometricTimeOut = new Date(date);
              biometricTimeOut.setHours(parseInt(hours), parseInt(minutes), 0, 0);
            } else if (timeOut instanceof Date) {
              biometricTimeOut = new Date(date);
              biometricTimeOut.setHours(timeOut.getHours(), timeOut.getMinutes(), 0, 0);
            }
          }
          
          attendanceData.push({
            employeeId: employeeId.toString(),
            date: new Date(date.getFullYear(), date.getMonth(), date.getDate()),
            biometricTimeIn,
            biometricTimeOut,
            biometricDeviceId: deviceId,
            biometricLocation: location,
            source: 'Biometric'
          });
          
        } catch (error) {
          errors.push(`Row ${rowNumber}: ${error.message}`);
        }
      });
      
      // Process and save attendance data
      const processedRecords = [];
      const skippedRecords = [];
      
      for (const record of attendanceData) {
        try {
          // Find user by employee ID (assuming it's stored in a custom field or email)
          const user = await User.findOne({
            $or: [
              { email: { $regex: record.employeeId, $options: 'i' } },
              { name: { $regex: record.employeeId, $options: 'i' } }
            ]
          });
          
          if (!user) {
            skippedRecords.push({
              employeeId: record.employeeId,
              reason: 'User not found'
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
            existingRecord.biometricTimeIn = record.biometricTimeIn;
            existingRecord.biometricTimeOut = record.biometricTimeOut;
            existingRecord.biometricDeviceId = record.biometricDeviceId;
            existingRecord.biometricLocation = record.biometricLocation;
            existingRecord.isPresent = true;
            
            if (existingRecord.source === 'StartDay') {
              existingRecord.source = 'Both';
            } else {
              existingRecord.source = 'Biometric';
            }
            
            await existingRecord.save();
            processedRecords.push({
              employeeId: record.employeeId,
              userName: user.name,
              date: record.date,
              action: 'Updated'
            });
          } else {
            // Create new attendance record
            const newAttendance = new Attendance({
              user: user._id,
              date: record.date,
              biometricTimeIn: record.biometricTimeIn,
              biometricTimeOut: record.biometricTimeOut,
              biometricDeviceId: record.biometricDeviceId,
              biometricLocation: record.biometricLocation,
              isPresent: true,
              source: 'Biometric'
            });
            
            await newAttendance.save();
            processedRecords.push({
              employeeId: record.employeeId,
              userName: user.name,
              date: record.date,
              action: 'Created'
            });
          }
          
        } catch (error) {
          skippedRecords.push({
            employeeId: record.employeeId,
            reason: error.message
          });
        }
      }

      // Clean up uploaded file
      try {
        fs.unlinkSync(req.file.path);
      } catch (cleanupError) {
        console.warn('Failed to cleanup uploaded file:', cleanupError);
      }
      
      // Emit socket event for real-time updates
      if (req.io) {
        req.io.emit('attendance:excel-processed', {
          processed: processedRecords.length,
          skipped: skippedRecords.length,
          errors: errors.length
        });
      }
      
      res.json({
        success: true,
        message: 'Excel file processed successfully',
        summary: {
          totalRows: attendanceData.length,
          processed: processedRecords.length,
          skipped: skippedRecords.length,
          errors: errors.length
        },
        details: {
          processedRecords,
          skippedRecords,
          errors
        }
      });
      
    } catch (error) {
      console.error('Excel processing error:', error);
      
      // Clean up uploaded file on error
      if (req.file && req.file.path) {
        try {
          fs.unlinkSync(req.file.path);
        } catch (cleanupError) {
          console.warn('Failed to cleanup uploaded file on error:', cleanupError);
        }
      }
      
      res.status(500).json({ 
        success: false,
        error: 'Failed to process Excel file',
        details: error.message 
      });
    }
  });
});

module.exports = router;