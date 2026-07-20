const express = require('express');
const router = express.Router();
const multer = require('multer');
const ExcelJS = require('exceljs');
const XLSX = require('xlsx');
const fs = require('fs');
const geolib = require('geolib');
const Attendance = require('../models/Attendance');
const User = require('../models/User');
const UserTag = require('../models/UserTag');
const auth = require('../middleware/auth');
const adminAuth = require('../middleware/adminAuth');

// Configure multer for Excel file uploads
const upload = multer({
  storage: multer.diskStorage({
    destination: (req, file, cb) => {
      cb(null, 'uploads/');
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

// Office coordinates - Blackhole Infiverse LLP Mumbai
// Address: Road Number 3, near Hathi Circle, above Bright Connection, Kala Galli, Motilal Nagar II, Goregaon West, Mumbai, Maharashtra
const OFFICE_COORDINATES = {
  latitude: parseFloat(process.env.OFFICE_LAT) || 19.158900,
  longitude: parseFloat(process.env.OFFICE_LNG) || 72.838645
};
const OFFICE_RADIUS = parseInt(process.env.OFFICE_RADIUS) || 100; // meters
const MAX_WORKING_HOURS = parseInt(process.env.MAX_WORKING_HOURS) || 8;
const AUTO_END_DAY_ENABLED = process.env.AUTO_END_DAY_ENABLED === 'true';
const OFFICE_ADDRESS = 'Blackhole Infiverse LLP, Road Number 3, near Hathi Circle, above Bright Connection, Kala Galli, Motilal Nagar II, Goregaon West, Mumbai, Maharashtra';

// Enhanced start day with geolocation validation and work from home option
router.post('/start-day/:userId', auth, async (req, res) => {
  try {
    const { userId } = req.params;
    const { latitude, longitude, address, accuracy, workFromHome, homeLocation } = req.body;
    
    // Verify user authorization
    if (req.user.id !== userId && req.user.role !== 'Admin') {
      return res.status(403).json({ error: 'Not authorized' });
    }
    
    // Validate geolocation
    if (!latitude || !longitude) {
      return res.status(400).json({ 
        error: 'Geolocation data required',
        code: 'LOCATION_REQUIRED'
      });
    }
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // Check if user has already started day
    const existingRecord = await Attendance.findOne({
      user: userId,
      date: today
    });
    
    if (existingRecord && existingRecord.startDayTime) {
      return res.status(400).json({ 
        error: 'Day already started',
        startTime: existingRecord.startDayTime,
        code: 'DAY_ALREADY_STARTED'
      });
    }
    
    let workLocationType = 'Office';
    let locationValidated = false;
    
    if (workFromHome) {
      // Work from home - lock the location
      workLocationType = 'Home';
      locationValidated = true;
      
      console.log(`📍 User ${userId} starting work from home at coordinates: ${latitude}, ${longitude}`);
    } else {
      // Check if user is within office radius
      const distance = geolib.getDistance(
        { latitude: OFFICE_COORDINATES.latitude, longitude: OFFICE_COORDINATES.longitude },
        { latitude, longitude }
      );
      
      if (distance > OFFICE_RADIUS) {
        return res.status(400).json({
          error: `You must be within ${OFFICE_RADIUS}m of office premises to start your day.`,
          distance: distance,
          allowedRadius: OFFICE_RADIUS,
          officeAddress: OFFICE_ADDRESS,
          officeCoordinates: OFFICE_COORDINATES,
          code: 'LOCATION_TOO_FAR',
          suggestion: 'Either go to office or select "Work From Home" option'
        });
      }
      
      workLocationType = 'Office';
      locationValidated = true;
      
      console.log(`🏢 User ${userId} starting work from office at distance: ${distance}m`);
    }
    
    const startTime = new Date();
    
    // Create or update attendance record
    let attendanceRecord;
    
    if (existingRecord) {
      // Update existing record
      existingRecord.startDayTime = startTime;
      existingRecord.startDayLocation = {
        latitude,
        longitude,
        address: address || (workFromHome ? 'Work From Home' : 'Office Location'),
        accuracy
      };
      existingRecord.workPattern = workFromHome ? 'Remote' : 'Regular';
      existingRecord.isPresent = true;
      existingRecord.isVerified = locationValidated;
      
      if (existingRecord.source === 'Biometric') {
        existingRecord.source = 'Both';
      } else {
        existingRecord.source = 'StartDay';
      }
      
      attendanceRecord = existingRecord;
    } else {
      // Create new record
      attendanceRecord = new Attendance({
        user: userId,
        date: today,
        startDayTime: startTime,
        startDayLocation: {
          latitude,
          longitude,
          address: address || (workFromHome ? 'Work From Home' : 'Office Location'),
          accuracy
        },
        workPattern: workFromHome ? 'Remote' : 'Regular',
        isPresent: true,
        isVerified: locationValidated,
        source: 'StartDay'
      });
    }
    
    await attendanceRecord.save();
    
    // Also create/update DailyAttendance record for enhanced tracking
    const DailyAttendance = require('../models/DailyAttendance');
    
    let dailyRecord = await DailyAttendance.findOne({
      user: userId,
      date: today
    });
    
    if (dailyRecord) {
      // Update existing daily record
      dailyRecord.startDayTime = startTime;
      dailyRecord.startDayLocation = {
        latitude,
        longitude,
        address: address || (workFromHome ? 'Work From Home' : 'Office Location'),
        accuracy
      };
      dailyRecord.workLocationType = workLocationType;
      dailyRecord.isPresent = true;
      dailyRecord.status = 'Present';
      dailyRecord.source = 'StartDay';
    } else {
      // Create new daily record
      dailyRecord = new DailyAttendance({
        user: userId,
        date: today,
        startDayTime: startTime,
        startDayLocation: {
          latitude,
          longitude,
          address: address || (workFromHome ? 'Work From Home' : 'Office Location'),
          accuracy
        },
        workLocationType: workLocationType,
        isPresent: true,
        status: 'Present',
        source: 'StartDay'
      });
    }
    
    await dailyRecord.save();
    
    // 🎯 FIXED: Only update existing aim with work location, DON'T create default aims
    const Aim = require('../models/Aim');
    let todayAim = await Aim.findOne({
      user: userId,
      date: {
        $gte: today,
        $lt: new Date(today.getTime() + 24 * 60 * 60 * 1000)
      }
    });
    
    if (todayAim) {
      // Update existing aim with work location
      todayAim.workLocation = workLocationType;
      await todayAim.save();
      console.log(`🏢 Updated existing aim work location to ${workLocationType} for user ${userId}`);
    } else {
      console.log(`🎯 No existing aim found for user ${userId} - user will need to set their own aim manually`);
    }
    
    // Emit socket event
    if (req.io) {
      req.io.emit('attendance:day-started', {
        userId,
        startTime,
        location: { latitude, longitude, address },
        workLocationType
      });
    }
    
    res.json({
      success: true,
      message: `Day started successfully${workFromHome ? ' from home' : ' from office'}!`,
      startTime,
      location: { latitude, longitude, address },
      workLocationType,
      distanceFromOffice: workFromHome ? null : geolib.getDistance(
        { latitude: OFFICE_COORDINATES.latitude, longitude: OFFICE_COORDINATES.longitude },
        { latitude, longitude }
      )
    });
    
  } catch (error) {
    console.error('Start day error:', error);
    res.status(500).json({ 
      error: 'Failed to start day',
      details: error.message 
    });
  }
});

// 🔧 FIXED: Enhanced end day with ONLY progress validation (aim validation removed)
router.post('/end-day/:userId', auth, async (req, res) => {
  try {
    const { userId } = req.params;
    const { latitude, longitude, address, accuracy, notes } = req.body;
    
    // Verify user authorization
    if (req.user.id !== userId && req.user.role !== 'Admin') {
      return res.status(403).json({ error: 'Not authorized' });
    }
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    const attendanceRecord = await Attendance.findOne({
      user: userId,
      date: today
    });
    
    if (!attendanceRecord || !attendanceRecord.startDayTime) {
      return res.status(400).json({ 
        error: 'Day not started yet. Please start your day first.',
        code: 'DAY_NOT_STARTED'
      });
    }
    
    if (attendanceRecord.endDayTime) {
      return res.status(400).json({ 
        error: 'Day already ended',
        endTime: attendanceRecord.endDayTime,
        code: 'DAY_ALREADY_ENDED'
      });
    }
    
    // =====================================
    // MANDATORY VALIDATIONS BEFORE END DAY
    // =====================================
    
    // ✅ ONLY CHECK PROGRESS - AIM VALIDATION REMOVED
    const Progress = require('../models/Progress');
    const todayProgress = await Progress.findOne({
      user: userId,
      date: {
        $gte: today,
        $lt: tomorrow
      }
    });
    
    // Check if progress has any meaningful content
    const hasProgressContent = todayProgress && (
      (todayProgress.notes && todayProgress.notes.trim() !== '') ||
      (todayProgress.achievements && todayProgress.achievements.trim() !== '') ||
      (todayProgress.blockers && todayProgress.blockers.trim() !== '')
    );
    
    if (!hasProgressContent) {
      return res.status(400).json({
        error: 'Please set your daily progress before ending your day',
        code: 'PROGRESS_NOT_SET',
        message: 'Daily progress with notes is mandatory before ending work day',
        requirement: 'You must describe your daily accomplishments or tasks completed'
      });
    }
    
    // 🎯 Get aim for reference but don't block end-day if not completed
    const Aim = require('../models/Aim');
    const todayAim = await Aim.findOne({
      user: userId,
      date: {
        $gte: today,
        $lt: tomorrow
      }
    });
    
    console.log(`✅ Progress validation passed for user ${userId} - Progress: ${hasProgressContent ? 'Yes' : 'No'} (notes: ${!!todayProgress?.notes}, achievements: ${!!todayProgress?.achievements}, blockers: ${!!todayProgress?.blockers}), Aim: ${todayAim?.completionStatus || 'No aim set'}`);
    
    // =====================================
    // PROCEED WITH END DAY
    // =====================================
    
    const endTime = new Date();
    
    attendanceRecord.endDayTime = endTime;
    if (latitude && longitude) {
      attendanceRecord.endDayLocation = {
        latitude,
        longitude,
        address,
        accuracy
      };
    }
    
    if (notes) {
      attendanceRecord.employeeNotes = notes;
    }

    // Calculate detailed working hours BEFORE saving
    const startTime = attendanceRecord.startDayTime;
    const totalMilliseconds = endTime - startTime;
    const totalMinutes = Math.floor(totalMilliseconds / (1000 * 60));
    const hoursWorked = totalMilliseconds / (1000 * 60 * 60);

    // Update attendance record with calculated values
    attendanceRecord.hoursWorked = Math.round(hoursWorked * 100) / 100;
    attendanceRecord.isPresent = true;
    
    // Calculate overtime if applicable
    const standardHours = 8;
    if (hoursWorked > standardHours) {
      attendanceRecord.overtimeHours = Math.round((hoursWorked - standardHours) * 100) / 100;
    } else {
      attendanceRecord.overtimeHours = 0;
    }

    // Mark as verified since it's manually ended with validations
    attendanceRecord.isVerified = true;
    attendanceRecord.approvalStatus = 'Auto-Approved';

    await attendanceRecord.save();
    
    // Update DailyAttendance record as well
    const DailyAttendance = require('../models/DailyAttendance');
    const dailyRecord = await DailyAttendance.findOne({
      user: userId,
      date: today
    });
    
    if (dailyRecord) {
      dailyRecord.endDayTime = endTime;
      if (latitude && longitude) {
        dailyRecord.endDayLocation = {
          latitude,
          longitude,
          address,
          accuracy
        };
      }
      dailyRecord.totalHoursWorked = Math.round(hoursWorked * 100) / 100;
      dailyRecord.isPresent = true;
      dailyRecord.status = 'Present';
      dailyRecord.dailyProgressCompleted = true;
      dailyRecord.dailyAimCompleted = todayAim ? (todayAim.completionStatus !== 'Pending') : false;
      dailyRecord.aimCompletionStatus = todayAim?.completionStatus || 'Not Set';
      dailyRecord.aimCompletionComment = todayAim?.completionComment || '';
      
      await dailyRecord.save();
    }
    
    // Emit socket event
    if (req.io) {
      req.io.emit('attendance:day-ended', {
        userId,
        endTime,
        hoursWorked: attendanceRecord.hoursWorked,
        progressCompleted: true,
        aimCompleted: todayAim ? (todayAim.completionStatus !== 'Pending') : false
      });
    }
    
    res.json({
      success: true,
      message: `Day ended successfully! You worked ${attendanceRecord.hoursWorked} hours today.`,
      data: {
        endTime,
        startTime: attendanceRecord.startDayTime,
        hoursWorked: attendanceRecord.hoursWorked,
        overtimeHours: attendanceRecord.overtimeHours,
        isOvertime: attendanceRecord.overtimeHours > 0,
        attendanceId: attendanceRecord._id,
        validations: {
          progressCompleted: true,
          aimCompleted: todayAim ? (todayAim.completionStatus !== 'Pending') : false,
          aimStatus: todayAim?.completionStatus || 'Not Set'
        }
      }
    });

  } catch (error) {
    console.error('End day error:', error);
    res.status(500).json({ 
      error: 'Failed to end day',
      details: error.message 
    });
  }
});

// Auto end day for employees who exceed maximum working hours
router.post('/auto-end-day', auth, async (req, res) => {
  try {
    if (!AUTO_END_DAY_ENABLED) {
      return res.status(400).json({ error: 'Auto end day is disabled' });
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Find all attendance records that started today but haven't ended
    const activeAttendance = await Attendance.find({
      date: today,
      startDayTime: { $exists: true },
      endDayTime: { $exists: false }
    }).populate('user', 'name email');

    const autoEndedUsers = [];
    const currentTime = new Date();

    for (const record of activeAttendance) {
      const hoursWorked = (currentTime - record.startDayTime) / (1000 * 60 * 60);

      if (hoursWorked >= MAX_WORKING_HOURS) {
        // Auto end the day
        record.endDayTime = currentTime;
        record.employeeNotes = `Auto-ended after ${MAX_WORKING_HOURS} hours of work`;
        record.autoEnded = true;

        await record.save();

        autoEndedUsers.push({
          userId: record.user._id,
          userName: record.user.name,
          hoursWorked: Math.round(hoursWorked * 100) / 100,
          autoEndTime: currentTime
        });

        // Emit socket event
        if (req.io) {
          req.io.emit('attendance:auto-day-ended', {
            userId: record.user._id,
            userName: record.user.name,
            endTime: currentTime,
            hoursWorked: record.hoursWorked,
            reason: 'Exceeded maximum working hours'
          });
        }
      }
    }

    res.json({
      success: true,
      message: `Auto-ended ${autoEndedUsers.length} user(s)`,
      autoEndedUsers,
      maxWorkingHours: MAX_WORKING_HOURS
    });

  } catch (error) {
    console.error('Auto end day error:', error);
    res.status(500).json({ error: 'Failed to auto end day' });
  }
});

// Get attendance analytics
router.get('/analytics', auth, async (req, res) => {
  try {
    const { startDate, endDate, userId, department } = req.query;

    const start = startDate ? new Date(startDate) : new Date(new Date().getFullYear(), new Date().getMonth(), 1);
    const end = endDate ? new Date(endDate) : new Date();

    // Build match condition
    const matchCondition = {
      date: { $gte: start, $lte: end }
    };

    if (userId) {
      matchCondition.user = new mongoose.Types.ObjectId(userId);
    }

    if (department) {
      const users = await User.find({ department }).select('_id');
      matchCondition.user = { $in: users.map(u => u._id) };
    }

    // Get overall statistics
    const stats = await Attendance.getAttendanceStats(start, end, userId);

    // Get daily breakdown
    const dailyStats = await Attendance.aggregate([
      { $match: matchCondition },
      {
        $group: {
          _id: { $dateToString: { format: '%Y-%m-%d', date: '$date' } },
          totalEmployees: { $addToSet: '$user' },
          presentCount: { $sum: { $cond: ['$isPresent', 1, 0] } },
          verifiedCount: { $sum: { $cond: ['$isVerified', 1, 0] } },
          leaveCount: { $sum: { $cond: ['$isLeave', 1, 0] } },
          discrepancyCount: { $sum: { $cond: ['$hasDiscrepancy', 1, 0] } },
          avgHours: { $avg: '$hoursWorked' },
          totalOvertimeHours: { $sum: '$overtimeHours' }
        }
      },
      {
        $project: {
          date: '$_id',
          totalEmployees: { $size: '$totalEmployees' },
          presentCount: 1,
          verifiedCount: 1,
          leaveCount: 1,
          discrepancyCount: 1,
          absentCount: { $subtract: [{ $size: '$totalEmployees' }, '$presentCount'] },
          attendanceRate: {
            $multiply: [
              { $divide: ['$presentCount', { $size: '$totalEmployees' }] },
              100
            ]
          },
          avgHours: { $round: ['$avgHours', 2] },
          totalOvertimeHours: { $round: ['$totalOvertimeHours', 2] }
        }
      },
      { $sort: { date: 1 } }
    ]);

    // Get top performers
    const topPerformers = await Attendance.aggregate([
      { $match: matchCondition },
      {
        $group: {
          _id: '$user',
          attendanceRate: {
            $avg: { $cond: ['$isPresent', 100, 0] }
          },
          avgHours: { $avg: '$hoursWorked' },
          totalOvertimeHours: { $sum: '$overtimeHours' },
          discrepancies: { $sum: { $cond: ['$hasDiscrepancy', 1, 0] } }
        }
      },
      { $sort: { attendanceRate: -1, avgHours: -1 } },
      { $limit: 10 },
      {
        $lookup: {
          from: 'users',
          localField: '_id',
          foreignField: '_id',
          as: 'user'
        }
      },
      { $unwind: '$user' },
      {
        $project: {
          name: '$user.name',
          email: '$user.email',
          avatar: '$user.avatar',
          attendanceRate: { $round: ['$attendanceRate', 1] },
          avgHours: { $round: ['$avgHours', 2] },
          totalOvertimeHours: { $round: ['$totalOvertimeHours', 2] },
          discrepancies: 1
        }
      }
    ]);

    res.json({
      success: true,
      data: {
        summary: stats,
        dailyBreakdown: dailyStats,
        topPerformers,
        dateRange: { start, end }
      }
    });

  } catch (error) {
    console.error('Analytics error:', error);
    res.status(500).json({ error: 'Failed to fetch analytics' });
  }
});

// Get user-specific attendance records
router.get('/user/:userId', auth, async (req, res) => {
  try {
    const { userId } = req.params;
    const { startDate, endDate, page = 1, limit = 30 } = req.query;

    // Verify user authorization
    if (req.user.id !== userId && req.user.role !== 'Admin') {
      return res.status(403).json({ error: 'Not authorized' });
    }

    const start = startDate ? new Date(startDate) : new Date(new Date().getFullYear(), new Date().getMonth(), 1);
    const end = endDate ? new Date(endDate) : new Date();

    const skip = (page - 1) * limit;

    const records = await Attendance.find({
      user: userId,
      date: { $gte: start, $lte: end }
    })
    .sort({ date: -1 })
    .skip(skip)
    .limit(parseInt(limit))
    .populate('leaveReference', 'reason leaveType')
    .populate('approvedBy', 'name');

    const total = await Attendance.countDocuments({
      user: userId,
      date: { $gte: start, $lte: end }
    });

    const stats = await Attendance.getAttendanceStats(start, end, userId);

    res.json({
      success: true,
      data: {
        records,
        pagination: {
          page: parseInt(page),
          limit: parseInt(limit),
          total,
          pages: Math.ceil(total / limit)
        },
        stats
      }
    });

  } catch (error) {
    console.error('User attendance error:', error);
    res.status(500).json({ error: 'Failed to fetch user attendance' });
  }
});

// Verify attendance for a specific day
router.get('/verify/:userId', auth, async (req, res) => {
  try {
    const { userId } = req.params;
    const { date } = req.query;

    const targetDate = date ? new Date(date) : new Date();
    targetDate.setHours(0, 0, 0, 0);

    const attendance = await Attendance.findOne({
      user: userId,
      date: targetDate
    }).populate('user', 'name email');

    if (!attendance) {
      return res.json({
        success: true,
        data: {
          isPresent: false,
          isVerified: false,
          message: 'No attendance record found for this date'
        }
      });
    }

    res.json({
      success: true,
      data: {
        ...attendance.toObject(),
        statusDisplay: attendance.statusDisplay,
        statusColor: attendance.statusColor
      }
    });

  } catch (error) {
    console.error('Verify attendance error:', error);
    res.status(500).json({ error: 'Failed to verify attendance' });
  }
});

// Get live attendance data for dashboard
router.get('/live', adminAuth, async (req, res) => {
  try {
    const { date, department, status } = req.query;
    const targetDate = date ? new Date(date) : new Date();

    // Set date range for the day
    const startOfDay = new Date(targetDate);
    startOfDay.setHours(0, 0, 0, 0);
    const endOfDay = new Date(targetDate);
    endOfDay.setHours(23, 59, 59, 999);

    // Build query
    let query = {
      date: { $gte: startOfDay, $lte: endOfDay }
    };

    if (department) {
      const users = await User.find({ department }).select('_id');
      query.user = { $in: users.map(u => u._id) };
    }

    if (status) {
      if (status === 'present') {
        query.isPresent = true;
      } else if (status === 'absent') {
        query.isPresent = false;
      } else if (status === 'late') {
        query.isLate = true;
      } else if (status === 'on-leave') {
        query.isLeave = true;
      }
    }

    // Fetch attendance records with user details
    const attendance = await Attendance.find(query)
      .populate('user', 'name email avatar department')
      .sort({ updatedAt: -1 })
      .lean();

    // Calculate stats
    const totalEmployees = await User.countDocuments({ isActive: true });
    const presentToday = attendance.filter(a => a.isPresent).length;
    const absentToday = totalEmployees - presentToday;
    const lateToday = attendance.filter(a => a.isLate).length;
    const onTimeToday = presentToday - lateToday;

    const totalHoursToday = attendance.reduce((sum, a) => sum + (a.hoursWorked || 0), 0);
    const avgHoursToday = presentToday > 0 ? totalHoursToday / presentToday : 0;

    const stats = {
      totalEmployees,
      presentToday,
      absentToday,
      lateToday,
      onTimeToday,
      presentPercentage: totalEmployees > 0 ? (presentToday / totalEmployees) * 100 : 0,
      absentPercentage: totalEmployees > 0 ? (absentToday / totalEmployees) * 100 : 0,
      onTimePercentage: presentToday > 0 ? (onTimeToday / presentToday) * 100 : 0,
      avgHoursToday,
      totalHoursToday
    };

    // Format attendance data
    const formattedAttendance = attendance.map(record => ({
      ...record,
      status: record.isPresent ? (record.isLate ? 'late' : 'present') :
              record.isLeave ? 'on-leave' : 'absent',
      user: {
        ...record.user,
        tag: record.user.tag || 'Employee' // Default tag
      }
    }));

    res.json({
      success: true,
      data: {
        attendance: formattedAttendance,
        stats,
        date: targetDate.toISOString().split('T')[0]
      }
    });

  } catch (error) {
    console.error('Get live attendance error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch live attendance data'
    });
  }
});

module.exports = router;