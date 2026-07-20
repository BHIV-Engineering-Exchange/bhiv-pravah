const express = require("express");
const router = express.Router();
const Progress = require("../models/Progress");
const Aim = require("../models/Aim");
const User = require("../models/User");

// Test route to check progress data
router.get("/check-progress", async (req, res) => {
  try {
    const { userId, date } = req.query;
    
    let queryDate = new Date();
    if (date) {
      queryDate = new Date(date);
    }
    
    const startOfDay = new Date(queryDate);
    startOfDay.setHours(0, 0, 0, 0);
    const endOfDay = new Date(queryDate);
    endOfDay.setHours(23, 59, 59, 999);

    // Get all progress entries for today
    const allTodayProgress = await Progress.find({
      date: {
        $gte: startOfDay,
        $lte: endOfDay
      }
    }).populate("user", "name email").populate("task", "title");

    // Get specific user progress if userId provided
    let userProgress = [];
    if (userId) {
      userProgress = await Progress.find({
        user: userId,
        date: {
          $gte: startOfDay,
          $lte: endOfDay
        }
      }).populate("task", "title");
    }

    // Get all aims for today
    const allTodayAims = await Aim.find({
      date: {
        $gte: startOfDay,
        $lte: endOfDay
      }
    }).populate("user", "name email");

    res.json({
      success: true,
      debug: {
        queryDate: queryDate.toISOString().split('T')[0],
        dateRange: {
          start: startOfDay.toISOString(),
          end: endOfDay.toISOString()
        },
        totalProgressEntries: allTodayProgress.length,
        totalAims: allTodayAims.length,
        allTodayProgress: allTodayProgress.map(p => ({
          id: p._id,
          user: p.user?.name,
          task: p.task?.title,
          percentage: p.progressPercentage,
          notes: p.notes,
          achievements: p.achievements,
          blockers: p.blockers,
          date: p.date.toISOString()
        })),
        userProgress: userProgress.map(p => ({
          id: p._id,
          task: p.task?.title,
          percentage: p.progressPercentage,
          notes: p.notes,
          achievements: p.achievements,
          blockers: p.blockers,
          date: p.date.toISOString()
        })),
        allTodayAims: allTodayAims.map(a => ({
          id: a._id,
          user: a.user?.name,
          aims: a.aims,
          progressPercentage: a.progressPercentage,
          progressNotes: a.progressNotes,
          date: a.date.toISOString()
        }))
      }
    });

  } catch (error) {
    console.error("Error checking progress:", error);
    res.status(500).json({ 
      success: false,
      error: "Failed to check progress",
      details: error.message 
    });
  }
});

// Test route to create sample progress
router.post("/create-sample-progress", async (req, res) => {
  try {
    const { userId, taskId } = req.body;
    
    if (!userId) {
      return res.status(400).json({ error: "userId is required" });
    }

    // Create sample progress entry
    const sampleProgress = new Progress({
      user: userId,
      task: taskId || userId, // Use userId as taskId if not provided
      progressPercentage: 75,
      notes: "Sample progress notes - working on daily tasks",
      achievements: "Completed initial setup and configuration",
      blockers: "Waiting for API documentation",
      date: new Date()
    });

    await sampleProgress.save();

    res.json({
      success: true,
      message: "Sample progress created",
      progress: sampleProgress
    });

  } catch (error) {
    console.error("Error creating sample progress:", error);
    res.status(500).json({ 
      success: false,
      error: "Failed to create sample progress",
      details: error.message 
    });
  }
});

module.exports = router;