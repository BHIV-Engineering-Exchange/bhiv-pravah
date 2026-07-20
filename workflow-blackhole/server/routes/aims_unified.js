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
router.get("/", adminAuth, async (req, res) => {
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
        select: "name email department",
        populate: {
          path: "department",
          select: "name color"
        }
      })
      .populate("department", "name color")
      .sort({ date: -1 });

    res.json(aims);
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
    }).populate('user', 'name email');
    
    if (aim) {
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
    
    res.json(aim || null);
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
router.get("/all", adminAuth, async (req, res) => {
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
        select: "name email department",
        populate: {
          path: "department",
          select: "name color"
        }
      })
      .populate("department", "name color")
      .sort({ updatedAt: -1 });
      
    res.json(aims);
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
      if (department && department !== "all") {
        // Filter by users in the department instead of aim department
        const usersInDept = await User.find({ department }).select('_id');
        aimFilter.user = { $in: usersInDept.map(u => u._id) };
      }
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

    // 🧹 FILTER OUT DEFAULT AIMS: Exclude auto-generated default aims
    aimFilter.aims = { $ne: 'Daily work objectives - to be updated' };

    console.log('🎯 Final aim filter:', aimFilter);

    // 🏢 DEPARTMENT FIX: Properly populate user with department
    const aims = await Aim.find(aimFilter)
      .populate({
        path: "user",
        select: "name email department",
        populate: {
          path: "department",
          select: "name color"
        }
      })
      .sort({ date: -1 });

    console.log(`📊 Found ${aims.length} aims for date ${queryDate.toISOString().split('T')[0]}`);

    // Log department info for debugging
    aims.forEach(aim => {
      console.log(`👤 User: ${aim.user?.name}, Department: ${aim.user?.department?.name || 'No Department'}`);
    });

    // Enhance each aim with progress and attendance data
    const enhancedAims = await Promise.all(aims.map(async (aim) => {
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

      return {
        ...aimObj,
        // 🏢 DEPARTMENT FIX: Use user's department as the primary department
        department: aim.user?.department || aimObj.department || null,
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

    console.log(`✅ Returning ${enhancedAims.length} enhanced aims`);

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

// @route   GET api/aims/all-with-progress
// @desc    Get all aims with progress data for admin view
// @access  Admin only
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
    }).populate({
      path: 'user',
      select: 'name email avatar department',
      populate: {
        path: 'department',
        select: 'name color'
      }
    }).lean();

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

// @route   GET api/aims/user/:userId/with-progress
// @desc    Get user's aim with progress for a specific date
// @access  Private
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

    const user = await User.findById(userId);
    if (!user) {
      return res.status(404).json({ error: "User not found" });
    }

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

    // Get all aims for today with full user and department data
    const todayAims = await Aim.find({
      date: { $gte: today, $lt: tomorrow }
    })
    .populate({
      path: "user",
      select: "name email department",
      populate: {
        path: "department",
        select: "name color"
      }
    })
    .populate("department", "name color")
    .sort({ createdAt: -1 });

    // Get all users with departments
    const allUsers = await User.find({})
      .populate("department", "name color")
      .sort({ name: 1 });

    // Check for shared aims (same content)
    const aimsByContent = {};
    todayAims.forEach(aim => {
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
      totalUsers: allUsers.length,
      totalAimsToday: todayAims.length,
      usersWithAims: todayAims.length,
      usersWithoutAims: allUsers.length - todayAims.length,
      duplicateAims: duplicates.length,
      duplicateDetails: duplicates.map(([content, aims]) => ({
        content: content.substring(0, 100) + (content.length > 100 ? '...' : ''),
        sharedBy: aims
      })),
      allAimsToday: todayAims.map(aim => ({
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
      allUsers: allUsers.map(user => ({
        userId: user._id,
        userName: user.name,
        userEmail: user.email,
        userDepartment: user.department?.name || 'No Department',
        hasAimToday: todayAims.some(aim => aim.user._id.toString() === user._id.toString())
      }))
    });
  } catch (error) {
    console.error("Error in debug route:", error);
    res.status(500).json({ error: "Debug error", details: error.message });
  }
});

// @route   POST api/aims/sync-progress
// @desc    Manually sync progress to aim
// @access  Private
router.post("/sync-progress", auth, async (req, res) => {
  try {
    const { userId, progressPercentage, notes, achievements, blockers } = req.body;
    
    // 🔒 SECURITY: Ensure user can only sync their own progress
    if (req.user.id !== userId && req.user.role !== 'Admin') {
      return res.status(403).json({ error: 'Not authorized to sync progress for this user' });
    }
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    // Find today's aim
    let todayAim = await Aim.findOne({
      user: userId,
      date: {
        $gte: today,
        $lt: tomorrow
      }
    });

    if (!todayAim) {
      // Create a default aim if none exists
      const user = await User.findById(userId);
      if (user) {
        todayAim = new Aim({
          user: userId,
          department: user.department,
          date: today,
          aims: 'Daily work objectives - to be updated',
          completionStatus: 'Pending',
          progressPercentage: 0
        });
      }
    }

    if (todayAim) {
      // Update aim with progress information
      todayAim.progressPercentage = progressPercentage || todayAim.progressPercentage;
      todayAim.progressNotes = notes || todayAim.progressNotes;
      todayAim.achievements = achievements || todayAim.achievements;
      todayAim.blockers = blockers || todayAim.blockers;
      
      await todayAim.save();

      // Emit socket event
      if (req.io) {
        req.io.emit("aim-updated", {
          aim: todayAim,
          user: { id: userId }
        });
      }

      res.json({
        success: true,
        message: "Progress synced to aim successfully",
        aim: todayAim
      });
    } else {
      res.status(404).json({
        success: false,
        error: "Could not create or find aim for user"
      });
    }

  } catch (error) {
    console.error("Error syncing progress to aim:", error);
    res.status(500).json({ 
      success: false,
      error: "Failed to sync progress to aim",
      details: error.message 
    });
  }
});

module.exports = router;