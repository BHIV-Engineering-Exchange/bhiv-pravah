const express = require('express');
const router = express.Router();
const Aim = require('../models/Aim');
const Progress = require('../models/Progress');
const User = require('../models/User');
const DailyAttendance = require('../models/DailyAttendance');
const auth = require('../middleware/auth');
const adminAuth = require('../middleware/adminAuth');

// Get all aims with progress data for admin view
router.get('/all-with-progress', adminAuth, async (req, res) => {
  try {
    const { date } = req.query;
    const targetDate = date ? new Date(date) : new Date();
    
    // Set date range for the day
    const startOfDay = new Date(targetDate);
    startOfDay.setHours(0, 0, 0, 0);
    const endOfDay = new Date(targetDate);
    endOfDay.setHours(23, 59, 59, 999);

    // Fetch all aims for the date
    const aims = await Aim.find({
      date: {
        $gte: startOfDay,
        $lte: endOfDay
      }
    }).populate('user', 'name email avatar department').lean();

    // Fetch all progress for the date
    const progress = await Progress.find({
      date: {
        $gte: startOfDay,
        $lte: endOfDay
      }
    }).lean();

    // Fetch attendance data to get work location
    const attendance = await DailyAttendance.find({
      date: {
        $gte: startOfDay,
        $lte: endOfDay
      }
    }).lean();

    // Create maps for quick lookup
    const progressMap = new Map();
    progress.forEach(p => {
      const userId = p.user.toString();
      progressMap.set(userId, p);
    });

    const attendanceMap = new Map();
    attendance.forEach(a => {
      const userId = a.user.toString();
      attendanceMap.set(userId, a);
    });

    // Combine aims with progress and attendance data
    const aimsWithProgress = aims.map(aim => {
      const userId = aim.user._id.toString();
      const userProgress = progressMap.get(userId);
      const userAttendance = attendanceMap.get(userId);

      return {
        ...aim,
        // Add progress data
        progress: userProgress ? {
          notes: userProgress.notes,
          achievements: userProgress.achievements,
          blockers: userProgress.blockers,
          progressPercentage: userProgress.progressPercentage,
          hasContent: !!(
            (userProgress.notes && userProgress.notes.trim()) ||
            (userProgress.achievements && userProgress.achievements.trim()) ||
            (userProgress.blockers && userProgress.blockers.trim())
          )
        } : null,
        // Add work location from attendance
        actualWorkLocation: userAttendance?.workLocationType || aim.workLocation || 'Office',
        attendanceStatus: userAttendance?.status || 'Not Started',
        startDayTime: userAttendance?.startDayTime,
        endDayTime: userAttendance?.endDayTime,
        totalHoursWorked: userAttendance?.totalHoursWorked || 0
      };
    });

    res.json({
      success: true,
      data: aimsWithProgress,
      date: targetDate.toISOString().split('T')[0]
    });

  } catch (error) {
    console.error('Error fetching aims with progress:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch aims with progress data',
      details: error.message
    });
  }
});

// Get user's aim with progress for a specific date
router.get('/user/:userId/with-progress', auth, async (req, res) => {
  try {
    const { userId } = req.params;
    const { date } = req.query;
    
    // Verify authorization
    if (req.user.id !== userId && req.user.role !== 'Admin') {
      return res.status(403).json({ 
        success: false,
        error: 'Not authorized' 
      });
    }

    const targetDate = date ? new Date(date) : new Date();
    
    // Set date range for the day
    const startOfDay = new Date(targetDate);
    startOfDay.setHours(0, 0, 0, 0);
    const endOfDay = new Date(targetDate);
    endOfDay.setHours(23, 59, 59, 999);

    // Fetch user's aim for the date
    const aim = await Aim.findOne({
      user: userId,
      date: {
        $gte: startOfDay,
        $lte: endOfDay
      }
    }).populate('user', 'name email avatar').lean();

    // Fetch user's progress for the date
    const progress = await Progress.findOne({
      user: userId,
      date: {
        $gte: startOfDay,
        $lte: endOfDay
      }
    }).lean();

    // Fetch attendance data
    const attendance = await DailyAttendance.findOne({
      user: userId,
      date: {
        $gte: startOfDay,
        $lte: endOfDay
      }
    }).lean();

    if (!aim) {
      return res.json({
        success: true,
        data: null,
        message: 'No aim found for this date'
      });
    }

    // Combine aim with progress and attendance data
    const aimWithProgress = {
      ...aim,
      progress: progress ? {
        notes: progress.notes,
        achievements: progress.achievements,
        blockers: progress.blockers,
        progressPercentage: progress.progressPercentage,
        hasContent: !!(
          (progress.notes && progress.notes.trim()) ||
          (progress.achievements && progress.achievements.trim()) ||
          (progress.blockers && progress.blockers.trim())
        )
      } : null,
      actualWorkLocation: attendance?.workLocationType || aim.workLocation || 'Office',
      attendanceStatus: attendance?.status || 'Not Started',
      startDayTime: attendance?.startDayTime,
      endDayTime: attendance?.endDayTime,
      totalHoursWorked: attendance?.totalHoursWorked || 0
    };

    res.json({
      success: true,
      data: aimWithProgress,
      date: targetDate.toISOString().split('T')[0]
    });

  } catch (error) {
    console.error('Error fetching user aim with progress:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch user aim with progress',
      details: error.message
    });
  }
});

module.exports = router;