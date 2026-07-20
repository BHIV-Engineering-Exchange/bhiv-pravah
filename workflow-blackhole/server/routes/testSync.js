const express = require('express');
const router = express.Router();
const { syncProgressToAim, syncAttendanceToAim } = require('../utils/aimSync');
const auth = require('../middleware/auth');

// Test route to sync progress to aim
router.post('/sync-progress', auth, async (req, res) => {
  try {
    const { userId, progressPercentage, notes, achievements, blockers } = req.body;
    
    const result = await syncProgressToAim(userId, {
      progressPercentage,
      notes,
      achievements,
      blockers
    });
    
    res.json({
      success: true,
      message: 'Progress synced to aim successfully',
      aim: result
    });
  } catch (error) {
    console.error('Test sync progress error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to sync progress to aim'
    });
  }
});

// Test route to sync attendance to aim
router.post('/sync-attendance', auth, async (req, res) => {
  try {
    const { userId, startDayTime, endDayTime, workLocation, totalHoursWorked } = req.body;
    
    const result = await syncAttendanceToAim(userId, {
      startDayTime: startDayTime ? new Date(startDayTime) : null,
      endDayTime: endDayTime ? new Date(endDayTime) : null,
      workLocation,
      totalHoursWorked
    });
    
    res.json({
      success: true,
      message: 'Attendance synced to aim successfully',
      aim: result
    });
  } catch (error) {
    console.error('Test sync attendance error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to sync attendance to aim'
    });
  }
});

module.exports = router;