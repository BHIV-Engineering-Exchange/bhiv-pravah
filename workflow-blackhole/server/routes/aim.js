const express = require("express");
const router = express.Router();
const Aim = require("../models/Aim");
const Progress = require("../models/Progress");
const Attendance = require("../models/Attendance");
const DailyAttendance = require("../models/DailyAttendance");
const User = require("../models/User");
const auth = require("../middleware/auth");
const adminAuth = require("../middleware/adminAuth");
const { sendAimReminder } = require("../utils/emailService");

// ============================================================================
// UNIFIED AIMS ROUTES - ALL AIM FUNCTIONALITY IN ONE FILE
// ============================================================================

// @route   GET api/aims
// @desc    Get all aims (with filters) - Admin only
// @access  Private (Admin/Manager)
router.get("/", auth, adminAuth, async (req, res) => {
  try {
    const { department, date, user } = req.query;

    // Build filter object
    const filter = {};
    if (department) filter.department = department;
    if (user) filter.user = user;
    
    if (date) {
      const queryDate = new Date(date);
      filter.date = {
        $gte: new Date(queryDate.setHours(0, 0, 0, 0)),
        $lt: new Date(queryDate.setHours(23, 59, 59, 999)),
      };
    }

    const aims = await Aim.find(filter)
      .populate({
        path: "user",
        select: "name email department stillExist",
        match: { stillExist: 1 }, // Only populate active users
        populate: {
          path: "department",
          select: "name color"
        }
      })
      .populate("department", "name color")
      .sort({ date: -1 });

    // Filter out aims where user didn't populate (inactive users)
    const activeAims = aims.filter(aim => aim.user);

    res.json(activeAims);
  } catch (error) {
    console.error("Error fetching aims:", error);
    res.status(500).json({ error: "Server error" });
  }
});

// @route   GET api/aims/today/:id
// @desc    Get user's aim for today
// @access  Private
router.get("/today/:id", auth, async (req, res) => {
  try {
    const userId = req.params.id;
    
    // 🔒 SECURITY: Ensure user can only access their own aims
    if (req.user.id !== userId && req.user.role !== 'Admin') {
      console.log(`❌ Unauthorized access attempt: User ${req.user.id} trying to access aims for user ${userId}`);
      return res.status(403).json({ error: 'Not authorized to access this user\'s aims' });
    }
    
    // Check if user is active
    const user = await User.findOne({ 
      _id: userId, 
      stillExist: 1
    });
    if (!user) {
      return res.status(404).json({ error: "User not found or no longer active" });
    }
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    console.log(`🔍 [GET /aims/today/${userId}] Fetching aim for user: ${userId} (requested by: ${req.user.id})`);
    console.log(`📅 Date range: ${today.toISOString()} to ${tomorrow.toISOString()}`);
    
    const aim = await Aim.findOne({
      user: userId,
      date: {
        $gte: today,
        $lt: tomorrow
      }
    }).populate({
      path: 'user',
      select: 'name email stillExist',
      match: { stillExist: 1 }
    });
    
    if (aim && aim.user) {
      console.log(`✅ Found aim for user ${userId}:`, {
        aimId: aim._id,
        userId: aim.user._id,
        userName: aim.user.name,
        aimContent: aim.aims.substring(0, 50) + '...',
        createdAt: aim.createdAt
      });
    } else {
      console.log(`❌ No aim found for user ${userId} on ${today.toDateString()}`);
    }
    
    res.json(aim && aim.user ? aim : null);
  } catch (error) {
    console.error("Error fetching today's aim:", error);
    res.status(500).json({ error: "Server error" });
  }
});

// @route   GET api/aims/user/:userId
// @desc    Get aims for a specific user
// @access  Private
router.get("/user/:userId", auth, async (req, res) => {
  try {
    const { userId } = req.params;
    
    // 🔒 SECURITY: Ensure user can only access their own aims
    if (req.user.id !== userId && req.user.role !== 'Admin') {
      return res.status(403).json({ error: 'Not authorized to access this user\'s aims' });
    }
    
    // Check if user is active
    const user = await User.findOne({ 
      _id: userId, 
      stillExist: 1
    });
    if (!user) {
      return res.status(404).json({ error: "User not found or no longer active" });
    }
    
    const { from, to } = req.query;
    const filter = { user: userId };
    
    if (from && to) {
      filter.date = {
        $gte: new Date(from),
        $lte: new Date(to)
      };
    }
    
    const aims = await Aim.find(filter)
      .populate("department", "name color")
      .sort({ date: -1 });
      
    res.json(aims);
  } catch (error) {
    console.error("Error fetching user aims:", error);
    res.status(500).json({ error: "Server error" });
  }
});

// @route   GET api/aims/all
// @desc    Get all aims with user data for admin view
// @access  Admin only
router.get("/all", auth, adminAuth, async (req, res) => {
  try {
    const { date } = req.query;
    
    let filter = {};
    if (date) {
      const targetDate = new Date(date);
      targetDate.setHours(0, 0, 0, 0);
      const nextDate = new Date(targetDate);
      nextDate.setDate(nextDate.getDate() + 1);
      
      filter.date = {
        $gte: targetDate,
        $lt: nextDate
      };
    }
    
    const aims = await Aim.find(filter)
      .populate({
        path: "user",
        select: "name email department stillExist",
        match: { stillExist: 1 }, // Only populate active users
        populate: {
          path: "department",
          select: "name color"
        }
      })
      .populate("department", "name color")
      .sort({ updatedAt: -1 });

    // Filter out aims where user didn't populate (inactive users)
    const activeAims = aims.filter(aim => aim.user);
      
    res.json(activeAims);
  } catch (error) {
    console.error("Error fetching all aims:", error);
    res.status(500).json({ error: "Server error" });
  }
});

// @route   GET api/aims/with-progress
// @desc    Get aims with their related progress data (ENHANCED VERSION)
// @access  Private
router.get("/with-progress", auth, async (req, res) => {
  try {
    const { department, date, user } = req.query;
    console.log('🔍 Enhanced aims query params:', { department, date, user });
    console.log('👤 Request user:', { id: req.user.id, role: req.user.role });

    // Build filter object for aims
    const aimFilter = {};
    
    // 🔒 SECURITY FIX: Non-admin users can only see their own aims
    if (req.user.role !== 'Admin') {
      aimFilter.user = req.user.id;
      console.log('🔒 Non-admin user - filtering by user ID:', req.user.id);
    } else {
      // Admin can filter by department and specific user
      if (department && department !== "all") aimFilter.department = department;
      if (user) aimFilter.user = user;
      console.log('👑 Admin user - applying filters:', { department, user });
    }
    
    let queryDate = new Date();
    if (date) {
      queryDate = new Date(date);
    }
    
    const startOfDay = new Date(queryDate);
    startOfDay.setHours(0, 0, 0, 0);
    const endOfDay = new Date(queryDate);
    endOfDay.setHours(23, 59, 59, 999);
    
    aimFilter.date = {
      $gte: startOfDay,
      $lte: endOfDay
    };

    console.log('🎯 Final aim filter:', aimFilter);

    // 🏢 DEPARTMENT FIX: Properly populate user with department, only active users
    const aims = await Aim.find(aimFilter)
      .populate({
        path: "user",
        select: "name email department stillExist",
        match: { stillExist: 1 }, // Only populate active users
        populate: {
          path: "department",
          select: "name color"
        }
      })
      .populate("department", "name color")
      .sort({ date: -1 });

    // Filter out aims where user didn't populate (inactive users)
    const activeAims = aims.filter(aim => aim.user);

    console.log(`📊 Found ${activeAims.length} aims for active users on date ${queryDate.toISOString().split('T')[0]}`);

    // Log department info for debugging
    activeAims.forEach(aim => {
      console.log(`👤 User: ${aim.user?.name}, Department: ${aim.user?.department?.name || 'No Department'}, Aim Department: ${aim.department?.name || 'No Aim Department'}`);
    });

    // Enhance each aim with progress and attendance data
    const enhancedAims = await Promise.all(activeAims.map(async (aim) => {
      const aimObj = aim.toObject();
      console.log(`🔄 Processing aim for user: ${aim.user?.name} (${aim.user?._id})`);

      // Use the same date range for progress search
      const progressFilter = {
        user: aim.user._id,
        date: {
          $gte: startOfDay,
          $lte: endOfDay
        }
      };

      // Get all progress entries for this user on this date
      const progressEntries = await Progress.find(progressFilter)
        .populate("task", "title description")
        .sort({ date: -1 });

      console.log(`📈 Found ${progressEntries.length} progress entries for user ${aim.user?.name}`);

      // Get attendance data for work session info
      const attendanceData = await Attendance.findOne({
        user: aim.user._id,
        date: {
          $gte: startOfDay,
          $lte: endOfDay
        }
      });

      // Get daily attendance data (enhanced model)
      const dailyAttendanceData = await DailyAttendance.findOne({
        user: aim.user._id,
        date: {
          $gte: startOfDay,
          $lte: endOfDay
        }
      });

      // Calculate aggregated progress data
      let totalProgressPercentage = 0;
      let allNotes = [];
      let allAchievements = [];
      let allBlockers = [];

      if (progressEntries.length > 0) {
        // Get the latest progress percentage
        totalProgressPercentage = progressEntries[0].progressPercentage || 0;
        
        // Collect all notes, achievements, and blockers
        progressEntries.forEach(entry => {
          if (entry.notes && entry.notes.trim()) allNotes.push(entry.notes.trim());
          if (entry.achievements && entry.achievements.trim()) allAchievements.push(entry.achievements.trim());
          if (entry.blockers && entry.blockers.trim()) allBlockers.push(entry.blockers.trim());
        });
      }

      // Update work session info from attendance data
      let workSessionInfo = aimObj.workSessionInfo || {};
      
      if (attendanceData) {
        workSessionInfo = {
          ...workSessionInfo,
          startDayTime: attendanceData.startDayTime,
          endDayTime: attendanceData.endDayTime,
          totalHoursWorked: attendanceData.hoursWorked || 0,
          workLocationTag: attendanceData.workPattern === 'Remote' ? 'WFH' : 'Office'
        };
      }

      if (dailyAttendanceData) {
        workSessionInfo = {
          ...workSessionInfo,
          startDayTime: dailyAttendanceData.startDayTime || workSessionInfo.startDayTime,
          endDayTime: dailyAttendanceData.endDayTime || workSessionInfo.endDayTime,
          totalHoursWorked: dailyAttendanceData.totalHoursWorked || workSessionInfo.totalHoursWorked,
          workLocationTag: dailyAttendanceData.workLocationType === 'Home' ? 'WFH' : 
                          dailyAttendanceData.workLocationType === 'Remote' ? 'Remote' : 'Office'
        };
      }

      // Determine if aim is pending based on progress
      const isPending = progressEntries.length === 0 || 
                       (progressEntries.length > 0 && totalProgressPercentage === 0 && 
                        allNotes.length === 0 && allAchievements.length === 0);

      // 🏢 DEPARTMENT FIX: Use user's department if aim doesn't have one
      const finalDepartment = aimObj.department || aim.user?.department || null;

      return {
        ...aimObj,
        // 🏢 DEPARTMENT FIX: Ensure department is properly set
        department: finalDepartment,
        // Update progress data from actual progress entries
        progressPercentage: totalProgressPercentage,
        progressNotes: allNotes.join('; '),
        achievements: allAchievements.join('; '),
        blockers: allBlockers.join('; '),
        workSessionInfo,
        // Add raw progress entries for detailed view
        progressEntries: progressEntries,
        // Add attendance data
        attendanceData: attendanceData,
        dailyAttendanceData: dailyAttendanceData,
        // Determine if aim is pending based on progress
        isPending: isPending
      };
    }));

    console.log(`✅ Returning ${enhancedAims.length} enhanced aims for active users`);

    res.json({
      success: true,
      data: enhancedAims
    });

  } catch (error) {
    console.error("❌ Error fetching enhanced aims:", error);
    res.status(500).json({ 
      success: false,
      error: "Failed to fetch enhanced aims",
      details: error.message 
    });
  }
});

// @route   POST api/aims/postaim/:id
// @desc    Create or update today's aim
// @access  Private
router.post("/postaim/:id", auth, async (req, res) => {
  try {
    const { aims, completionStatus, completionComment, workLocation, achievements, blockers, progressPercentage } = req.body;
    const userId = req.params.id;

    // 🔒 SECURITY: Ensure user can only create/update their own aims
    if (req.user.id !== userId && req.user.role !== 'Admin') {
      return res.status(403).json({ error: 'Not authorized to create/update aims for this user' });
    }

    if (!userId) {
      return res.status(400).json({ error: "User ID is required" });
    }

    if (!aims) {
      return res.status(400).json({ error: "Aims are required" });
    }

    // Validate completion comment if status is not Pending
    if (completionStatus && completionStatus !== 'Pending' && (!completionComment || completionComment.trim() === '')) {
      return res.status(400).json({ error: "Completion comment is required when marking aim as completed or MVP achieved" });
    }

    // Check if user is active
    const user = await User.findOne({ 
      _id: userId, 
      stillExist: 1
    });
    if (!user) {
      return res.status(404).json({ error: "User not found or no longer active" });
    }

    // Get today's date (start of day)
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    console.log(`🎯 [POST /aims/postaim/${userId}] Creating/updating aim for user: ${userId} (requested by: ${req.user.id})`);
    console.log(`📝 Aim content: ${aims.substring(0, 100)}...`);

    // Check if user already has an aim for today
    let aim = await Aim.findOne({
      user: userId,
      date: {
        $gte: today,
        $lt: tomorrow,
      },
    });

    if (aim) {
      // Update existing aim
      console.log(`📝 Updating existing aim ${aim._id} for user ${userId}`);
      aim.aims = aims;
      if (completionStatus) aim.completionStatus = completionStatus;
      if (completionComment !== undefined) aim.completionComment = completionComment;
      if (workLocation) aim.workLocation = workLocation;
      if (achievements !== undefined) aim.achievements = achievements;
      if (blockers !== undefined) aim.blockers = blockers;
      if (progressPercentage !== undefined) aim.progressPercentage = progressPercentage;
      aim.updatedAt = Date.now();
    } else {
      // Create new aim
      console.log(`🆕 Creating new aim for user ${userId}`);
      aim = new Aim({
        user: userId,
        department: user.department,
        aims,
        completionStatus: completionStatus || 'Pending',
        completionComment: completionComment || '',
        workLocation: workLocation || 'Office',
        achievements: achievements || '',
        blockers: blockers || '',
        progressPercentage: progressPercentage || 0,
        date: today,
      });
    }

    await aim.save();

    console.log(`✅ Aim saved successfully for user ${userId}:`, {
      aimId: aim._id,
      content: aim.aims.substring(0, 50) + '...',
      status: aim.completionStatus
    });

    // Notify via Socket.IO
    if (req.io) {
      req.io.emit("aim-updated", {
        aim,
        user: {
          id: userId,
          name: user.name,
        },
      });
    }

    res.json(aim);
  } catch (error) {
    console.error("Error creating/updating aim:", error);
    res.status(500).json({ error: error.message || "Server error" });
  }
});

// @route   PUT api/aims/:id
// @desc    Update an aim
// @access  Private
router.put("/:id", auth, async (req, res) => {
  try {
    const { aims, completed, completionStatus, completionComment, workLocation, achievements, blockers, progressPercentage } = req.body;
    
    // Find aim by ID
    const aim = await Aim.findById(req.params.id);
    
    if (!aim) {
      return res.status(404).json({ error: "Aim not found" });
    }
    
    // Check if user owns the aim or is admin
    if (aim.user.toString() !== req.user.id && req.user.role !== "Admin") {
      return res.status(401).json({ error: "Not authorized" });
    }
    
    // Check if user is still active
    const user = await User.findOne({ 
      _id: aim.user, 
      stillExist: 1
    });
    if (!user) {
      return res.status(404).json({ error: "User not found or no longer active" });
    }
    
    // Validate completion comment if status is not Pending
    if (completionStatus && completionStatus !== 'Pending' && (!completionComment || completionComment.trim() === '')) {
      return res.status(400).json({ error: "Completion comment is required when marking aim as completed or MVP achieved" });
    }
    
    // Update fields
    if (aims !== undefined) aim.aims = aims;
    if (completed !== undefined) aim.completed = completed;
    if (completionStatus !== undefined) aim.completionStatus = completionStatus;
    if (completionComment !== undefined) aim.completionComment = completionComment;
    if (workLocation !== undefined) aim.workLocation = workLocation;
    if (achievements !== undefined) aim.achievements = achievements;
    if (blockers !== undefined) aim.blockers = blockers;
    if (progressPercentage !== undefined) aim.progressPercentage = progressPercentage;
    aim.updatedAt = Date.now();
    
    await aim.save();
    
    // Notify via Socket.IO
    if (req.io) {
      req.io.emit("aim-updated", { aim });
    }
    
    res.json(aim);
  } catch (error) {
    console.error("Error updating aim:", error);
    res.status(500).json({ error: error.message || "Server error" });
  }
});

// @route   DELETE api/aims/:id
// @desc    Delete an aim
// @access  Private
router.delete("/:id", auth, async (req, res) => {
  try {
    const aim = await Aim.findById(req.params.id);
    
    if (!aim) {
      return res.status(404).json({ error: "Aim not found" });
    }
    
    // Check if user owns the aim or is admin
    if (aim.user.toString() !== req.user.id && req.user.role !== "Admin") {
      return res.status(401).json({ error: "Not authorized" });
    }
    
    await aim.remove();
    
    // Notify via Socket.IO
    if (req.io) {
      req.io.emit("aim-deleted", { id: req.params.id });
    }
    
    res.json({ msg: "Aim removed" });
  } catch (error) {
    console.error("Error deleting aim:", error);
    res.status(500).json({ error: "Server error" });
  }
});

// @route   GET api/aims/debug
// @desc    Debug aims data to check for shared aims
// @access  Private
router.get("/debug", auth, async (req, res) => {
  try {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    // Get all aims for today with full user and department data (only active users)
    const todayAims = await Aim.find({
      date: { $gte: today, $lt: tomorrow }
    })
    .populate({
      path: "user",
      select: "name email department stillExist",
      match: { stillExist: 1 }, // Only populate active users
      populate: {
        path: "department",
        select: "name color"
      }
    })
    .populate("department", "name color")
    .sort({ createdAt: -1 });

    // Filter out aims where user didn't populate (inactive users)
    const activeAims = todayAims.filter(aim => aim.user);

    // Get all active users with departments
    const allUsers = await User.find({ stillExist: 1 })
      .populate("department", "name color")
      .sort({ name: 1 });

    // Check for shared aims (same content)
    const aimsByContent = {};
    activeAims.forEach(aim => {
      const content = aim.aims.trim();
      if (!aimsByContent[content]) {
        aimsByContent[content] = [];
      }
      aimsByContent[content].push({
        aimId: aim._id,
        userId: aim.user._id,
        userName: aim.user.name,
        userEmail: aim.user.email,
        userDepartment: aim.user.department?.name || 'No Department',
        aimDepartment: aim.department?.name || 'No Aim Department',
        createdAt: aim.createdAt
      });
    });

    // Find duplicates
    const duplicates = Object.entries(aimsByContent).filter(([content, aims]) => aims.length > 1);

    res.json({
      debug: true,
      requestUser: {
        id: req.user.id,
        role: req.user.role
      },
      date: today.toDateString(),
      totalActiveUsers: allUsers.length,
      totalAimsToday: activeAims.length,
      usersWithAims: activeAims.length,
      usersWithoutAims: allUsers.length - activeAims.length,
      duplicateAims: duplicates.length,
      duplicateDetails: duplicates.map(([content, aims]) => ({
        content: content.substring(0, 100) + (content.length > 100 ? '...' : ''),
        sharedBy: aims
      })),
      allAimsToday: activeAims.map(aim => ({
        aimId: aim._id,
        userId: aim.user._id,
        userName: aim.user.name,
        userEmail: aim.user.email,
        userDepartment: aim.user.department?.name || 'No Department',
        aimDepartment: aim.department?.name || 'No Aim Department',
        content: aim.aims.substring(0, 100) + (aim.aims.length > 100 ? '...' : ''),
        createdAt: aim.createdAt,
        updatedAt: aim.updatedAt
      })),
      allActiveUsers: allUsers.map(user => ({
        userId: user._id,
        userName: user.name,
        userEmail: user.email,
        userDepartment: user.department?.name || 'No Department',
        hasAimToday: activeAims.some(aim => aim.user._id.toString() === user._id.toString())
      }))
    });
  } catch (error) {
    console.error("Error in debug route:", error);
    res.status(500).json({ error: "Debug error", details: error.message });
  }
});

module.exports = router;