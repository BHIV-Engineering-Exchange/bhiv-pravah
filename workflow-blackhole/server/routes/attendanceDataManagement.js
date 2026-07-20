const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');

// Import all attendance-related models
const Attendance = require('../models/Attendance');
const DailyAttendance = require('../models/DailyAttendance');
const SalaryAttendance = require('../models/SalaryAttendance');
const WorkSession = require('../models/WorkSession');
const EmployeeActivity = require('../models/EmployeeActivity');
const ScreenCapture = require('../models/ScreenCapture');
const MonitoringAlert = require('../models/MonitoringAlert');
const Feedback = require('../models/Feedback');

/**
 * @route   DELETE /api/attendance-data/clear-all
 * @desc    Delete all attendance-related data from MongoDB
 * @access  Admin Only
 * @danger  This will permanently delete ALL attendance data!
 */
router.delete('/clear-all', auth, async (req, res) => {
  try {
    // Security check - Only allow Admin users
    if (req.user.role !== 'Admin') {
      return res.status(403).json({
        success: false,
        error: 'Access denied. Only administrators can perform this action.',
        code: 'ADMIN_REQUIRED'
      });
    }

    // Additional security confirmation
    const { confirmationCode } = req.body;
    if (confirmationCode !== 'DELETE_ALL_ATTENDANCE_DATA') {
      return res.status(400).json({
        success: false,
        error: 'Invalid confirmation code. Please provide the correct confirmation code.',
        code: 'INVALID_CONFIRMATION'
      });
    }

    console.log(`🚨 CRITICAL: Admin ${req.user.email} is attempting to delete ALL attendance data`);

    // Track deletion results
    const deletionResults = {};
    let totalRecordsDeleted = 0;

    // Delete data from each collection
    try {
      // 1. Basic Attendance Records
      const attendanceResult = await Attendance.deleteMany({});
      deletionResults.attendance = attendanceResult.deletedCount;
      totalRecordsDeleted += attendanceResult.deletedCount;
      console.log(`✅ Deleted ${attendanceResult.deletedCount} attendance records`);

      // 2. Daily Attendance Records
      const dailyAttendanceResult = await DailyAttendance.deleteMany({});
      deletionResults.dailyAttendance = dailyAttendanceResult.deletedCount;
      totalRecordsDeleted += dailyAttendanceResult.deletedCount;
      console.log(`✅ Deleted ${dailyAttendanceResult.deletedCount} daily attendance records`);

      // 3. Salary Attendance Data
      const salaryAttendanceResult = await SalaryAttendance.deleteMany({});
      deletionResults.salaryAttendance = salaryAttendanceResult.deletedCount;
      totalRecordsDeleted += salaryAttendanceResult.deletedCount;
      console.log(`✅ Deleted ${salaryAttendanceResult.deletedCount} salary attendance records`);

      // 4. Work Sessions
      const workSessionResult = await WorkSession.deleteMany({});
      deletionResults.workSessions = workSessionResult.deletedCount;
      totalRecordsDeleted += workSessionResult.deletedCount;
      console.log(`✅ Deleted ${workSessionResult.deletedCount} work session records`);

      // 5. Employee Activity Data
      const employeeActivityResult = await EmployeeActivity.deleteMany({});
      deletionResults.employeeActivity = employeeActivityResult.deletedCount;
      totalRecordsDeleted += employeeActivityResult.deletedCount;
      console.log(`✅ Deleted ${employeeActivityResult.deletedCount} employee activity records`);

      // 6. Screen Capture Data
      const screenCaptureResult = await ScreenCapture.deleteMany({});
      deletionResults.screenCaptures = screenCaptureResult.deletedCount;
      totalRecordsDeleted += screenCaptureResult.deletedCount;
      console.log(`✅ Deleted ${screenCaptureResult.deletedCount} screen capture records`);

      // 7. Monitoring Alerts
      const monitoringAlertResult = await MonitoringAlert.deleteMany({});
      deletionResults.monitoringAlerts = monitoringAlertResult.deletedCount;
      totalRecordsDeleted += monitoringAlertResult.deletedCount;
      console.log(`✅ Deleted ${monitoringAlertResult.deletedCount} monitoring alert records`);

      // 8. Attendance-related Feedback
      const feedbackResult = await Feedback.deleteMany({
        type: { $in: ['salary_dispute', 'attendance_query'] }
      });
      deletionResults.attendanceFeedback = feedbackResult.deletedCount;
      totalRecordsDeleted += feedbackResult.deletedCount;
      console.log(`✅ Deleted ${feedbackResult.deletedCount} attendance-related feedback records`);

    } catch (deletionError) {
      console.error('Error during data deletion:', deletionError);
      return res.status(500).json({
        success: false,
        error: 'Failed to delete some attendance data collections',
        details: deletionError.message,
        partialResults: deletionResults
      });
    }

    // Log the complete operation
    console.log(`🎯 COMPLETED: Successfully deleted ${totalRecordsDeleted} total attendance records`);
    console.log(`📊 Breakdown:`, deletionResults);

    // Emit socket event for real-time updates (if available)
    if (req.io) {
      req.io.emit('attendance-data:cleared', {
        adminUser: req.user.email,
        totalDeleted: totalRecordsDeleted,
        timestamp: new Date(),
        breakdown: deletionResults
      });
    }

    // Return success response
    res.json({
      success: true,
      message: `Successfully deleted all attendance-related data from MongoDB`,
      totalRecordsDeleted,
      breakdown: deletionResults,
      timestamp: new Date(),
      executedBy: {
        id: req.user.id,
        email: req.user.email,
        role: req.user.role
      }
    });

  } catch (error) {
    console.error('Critical error in attendance data deletion:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to delete attendance data',
      details: error.message
    });
  }
});

/**
 * @route   GET /api/attendance-data/stats
 * @desc    Get statistics of attendance-related data (for confirmation before deletion)
 * @access  Admin Only
 */
router.get('/stats', auth, async (req, res) => {
  try {
    // Security check - Only allow Admin users
    if (req.user.role !== 'Admin') {
      return res.status(403).json({
        success: false,
        error: 'Access denied. Only administrators can view this data.',
        code: 'ADMIN_REQUIRED'
      });
    }

    // Get counts from each collection
    const stats = {};
    let totalRecords = 0;

    try {
      // Count documents in each collection
      stats.attendance = await Attendance.countDocuments();
      stats.dailyAttendance = await DailyAttendance.countDocuments();
      stats.salaryAttendance = await SalaryAttendance.countDocuments();
      stats.workSessions = await WorkSession.countDocuments();
      stats.employeeActivity = await EmployeeActivity.countDocuments();
      stats.screenCaptures = await ScreenCapture.countDocuments();
      stats.monitoringAlerts = await MonitoringAlert.countDocuments();
      stats.attendanceFeedback = await Feedback.countDocuments({
        type: { $in: ['salary_dispute', 'attendance_query'] }
      });

      // Calculate total
      totalRecords = Object.values(stats).reduce((sum, count) => sum + count, 0);

      // Get additional metadata
      const oldestAttendance = await Attendance.findOne().sort({ createdAt: 1 }).select('createdAt');
      const newestAttendance = await Attendance.findOne().sort({ createdAt: -1 }).select('createdAt');

      res.json({
        success: true,
        totalRecords,
        breakdown: stats,
        dateRange: {
          oldest: oldestAttendance?.createdAt || null,
          newest: newestAttendance?.createdAt || null
        },
        warning: 'This data will be permanently deleted if you proceed with the clear operation.',
        confirmationRequired: 'DELETE_ALL_ATTENDANCE_DATA'
      });

    } catch (countError) {
      console.error('Error counting attendance data:', countError);
      res.status(500).json({
        success: false,
        error: 'Failed to retrieve attendance data statistics',
        details: countError.message
      });
    }

  } catch (error) {
    console.error('Error in attendance data stats:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get attendance data statistics',
      details: error.message
    });
  }
});

/**
 * @route   DELETE /api/attendance-data/clear-by-date
 * @desc    Delete attendance data within a specific date range
 * @access  Admin Only
 */
router.delete('/clear-by-date', auth, async (req, res) => {
  try {
    // Security check - Only allow Admin users
    if (req.user.role !== 'Admin') {
      return res.status(403).json({
        success: false,
        error: 'Access denied. Only administrators can perform this action.',
        code: 'ADMIN_REQUIRED'
      });
    }

    const { startDate, endDate, confirmationCode } = req.body;

    // Validate input
    if (!startDate || !endDate) {
      return res.status(400).json({
        success: false,
        error: 'Start date and end date are required',
        code: 'MISSING_DATES'
      });
    }

    if (confirmationCode !== 'DELETE_ATTENDANCE_DATA_BY_DATE') {
      return res.status(400).json({
        success: false,
        error: 'Invalid confirmation code for date range deletion',
        code: 'INVALID_CONFIRMATION'
      });
    }

    const start = new Date(startDate);
    const end = new Date(endDate);

    // Validate date range
    if (start >= end) {
      return res.status(400).json({
        success: false,
        error: 'Start date must be before end date',
        code: 'INVALID_DATE_RANGE'
      });
    }

    console.log(`🚨 Admin ${req.user.email} deleting attendance data from ${start} to ${end}`);

    const dateFilter = {
      $or: [
        { createdAt: { $gte: start, $lte: end } },
        { date: { $gte: start, $lte: end } },
        { timestamp: { $gte: start, $lte: end } }
      ]
    };

    // Track deletion results
    const deletionResults = {};
    let totalRecordsDeleted = 0;

    // Delete data from each collection within date range
    const attendanceResult = await Attendance.deleteMany({ date: { $gte: start, $lte: end } });
    deletionResults.attendance = attendanceResult.deletedCount;
    totalRecordsDeleted += attendanceResult.deletedCount;

    const dailyAttendanceResult = await DailyAttendance.deleteMany({ date: { $gte: start, $lte: end } });
    deletionResults.dailyAttendance = dailyAttendanceResult.deletedCount;
    totalRecordsDeleted += dailyAttendanceResult.deletedCount;

    const workSessionResult = await WorkSession.deleteMany({ date: { $gte: start, $lte: end } });
    deletionResults.workSessions = workSessionResult.deletedCount;
    totalRecordsDeleted += workSessionResult.deletedCount;

    const employeeActivityResult = await EmployeeActivity.deleteMany({ timestamp: { $gte: start, $lte: end } });
    deletionResults.employeeActivity = employeeActivityResult.deletedCount;
    totalRecordsDeleted += employeeActivityResult.deletedCount;

    const screenCaptureResult = await ScreenCapture.deleteMany({ timestamp: { $gte: start, $lte: end } });
    deletionResults.screenCaptures = screenCaptureResult.deletedCount;
    totalRecordsDeleted += screenCaptureResult.deletedCount;

    const monitoringAlertResult = await MonitoringAlert.deleteMany({ timestamp: { $gte: start, $lte: end } });
    deletionResults.monitoringAlerts = monitoringAlertResult.deletedCount;
    totalRecordsDeleted += monitoringAlertResult.deletedCount;

    res.json({
      success: true,
      message: `Successfully deleted attendance data from ${startDate} to ${endDate}`,
      dateRange: { startDate, endDate },
      totalRecordsDeleted,
      breakdown: deletionResults,
      timestamp: new Date(),
      executedBy: {
        id: req.user.id,
        email: req.user.email,
        role: req.user.role
      }
    });

  } catch (error) {
    console.error('Error in date range attendance data deletion:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to delete attendance data by date range',
      details: error.message
    });
  }
});

module.exports = router;
