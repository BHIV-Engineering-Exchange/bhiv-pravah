const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const moment = require('moment-timezone');
const EnhancedBiometricProcessor = require('../services/enhancedBiometricProcessor');
const AttendanceDataMigration = require('../utils/attendanceDataMigration');
const AttendanceDebugger = require('../utils/attendanceDebugger');
const DailyAttendance = require('../models/DailyAttendance');
const BiometricPunch = require('../models/BiometricPunch');
const EmployeeMaster = require('../models/EmployeeMaster');
const User = require('../models/User');
const Department = require('../models/Department');
const auth = require('../middleware/auth');

// Configure multer
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    const uploadDir = path.join(__dirname, '../uploads/biometric');
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
    cb(null, uploadDir);
  },
  filename: function (req, file, cb) {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, 'biometric-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({
  storage: storage,
  fileFilter: function (req, file, cb) {
    const allowedTypes = ['.csv', '.xlsx', '.xls'];
    const ext = path.extname(file.originalname).toLowerCase();
    if (allowedTypes.includes(ext)) {
      cb(null, true);
    } else {
      cb(new Error('Only CSV and Excel files are allowed'));
    }
  },
  limits: {
    fileSize: 50 * 1024 * 1024
  }
});

const processor = new EnhancedBiometricProcessor();
const debugger = new AttendanceDebugger();

/**
 * @route   POST /api/biometric/upload
 * @desc    Upload biometric data file with enhanced identity resolution
 * @access  Private (Admin/Manager)
 */
router.post('/upload', auth, upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ 
        success: false,
        error: 'No file uploaded' 
      });
    }

    console.log(`📤 Processing enhanced biometric upload: ${req.file.originalname}`);

    const result = await processor.parseFile(
      req.file.path,
      req.file.originalname,
      req.user.id
    );

    // Add recommendations if there were issues
    let recommendations = [];
    if (result.errors.length > 0 || result.ambiguousMatches.length > 0) {
      recommendations = debugger.generateFixRecommendations({
        issues: {
          idMappingIssues: result.errors,
          duplicatePunches: []
        }
      });
    }

    res.json({
      success: true,
      message: 'Biometric data uploaded and processed with enhanced identity resolution',
      data: result,
      recommendations: recommendations
    });

  } catch (error) {
    console.error('❌ Upload error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route   POST /api/biometric/derive-attendance
 * @desc    Derive daily attendance from biometric with improved merge logic
 * @access  Private (Admin/Manager)
 */
router.post('/derive-attendance', auth, async (req, res) => {
  try {
    const { startDate, endDate } = req.body;

    if (!startDate || !endDate) {
      return res.status(400).json({ 
        success: false,
        error: 'Start date and end date are required' 
      });
    }

    console.log(`📊 Deriving attendance with enhanced merge logic: ${startDate} to ${endDate}`);

    const result = await processor.deriveDailyAttendance(startDate, endDate);

    res.json({
      success: true,
      message: 'Attendance derived successfully with 20-minute tolerance',
      data: result,
      summary: {
        created: result.created,
        updated: result.updated,
        errors: result.errors.length,
        mergeDetails: {
          processed: result.mergeDetails.length,
          byCase: this._groupByMergeCase(result.mergeDetails)
        }
      }
    });

  } catch (error) {
    console.error('❌ Error deriving attendance:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route   POST /api/biometric/run-migration
 * @desc    Run full data migration and cleanup
 * @access  Private (Admin only)
 */
router.post('/run-migration', auth, async (req, res) => {
  try {
    // Check admin role
    const adminUser = await User.findById(req.user.id);
    if (!adminUser || !['admin', 'manager'].includes(adminUser.role)) {
      return res.status(403).json({
        success: false,
        error: 'Only admins/managers can run migrations'
      });
    }

    const { startDate, endDate } = req.body;

    if (!startDate || !endDate) {
      return res.status(400).json({
        success: false,
        error: 'Start date and end date are required'
      });
    }

    console.log(`🔄 Starting migration: ${startDate} to ${endDate}`);

    const migration = new AttendanceDataMigration();
    const result = await migration.runFullMigration(startDate, endDate);

    res.json({
      success: true,
      message: 'Migration completed successfully',
      data: result,
      stats: migration.stats
    });

  } catch (error) {
    console.error('❌ Migration error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route   GET /api/biometric/audit
 * @desc    Run audit on current attendance data
 * @access  Private (Admin/Manager)
 */
router.get('/audit', auth, async (req, res) => {
  try {
    const { startDate, endDate } = req.query;

    if (!startDate || !endDate) {
      return res.status(400).json({
        success: false,
        error: 'Start date and end date are required'
      });
    }

    const start = new Date(startDate);
    const end = new Date(endDate);

    const attendance = await DailyAttendance.find({
      date: { $gte: start, $lte: end }
    }).populate('user');

    const punches = await BiometricPunch.find({
      date: { $gte: start, $lte: end }
    }).populate('user');

    const employees = await EmployeeMaster.find({});

    const auditReport = await debugger.generateAuditReport(
      attendance,
      punches,
      employees
    );

    const recommendations = debugger.generateFixRecommendations(auditReport);

    res.json({
      success: true,
      auditReport,
      recommendations,
      summary: {
        totalIssues: auditReport.totalIssuesFound,
        issuesByCategory: Object.keys(auditReport.issues).reduce((acc, cat) => {
          acc[cat] = auditReport.issues[cat].length;
          return acc;
        }, {})
      }
    });

  } catch (error) {
    console.error('❌ Audit error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route   GET /api/attendance/daily
 * @desc    Get daily attendance with merge details
 * @access  Private
 */
router.get('/daily', auth, async (req, res) => {
  try {
    const { date, departmentId, userId } = req.query;

    const query = {};

    if (date) {
      const d = moment(date).tz('Asia/Kolkata');
      query.date = {
        $gte: d.startOf('day').toDate(),
        $lte: d.endOf('day').toDate()
      };
    }

    if (userId) {
      query.user = userId;
    }

    let records = await DailyAttendance.find(query)
      .populate('user', 'name email department')
      .sort({ date: -1, 'user.name': 1 });

    // Filter by department if specified
    if (departmentId) {
      records = records.filter(r => 
        r.user?.department?.toString() === departmentId
      );
    }

    // Format response with merge details and salary info
    const formattedRecords = await Promise.all(records.map(async (record) => {
      const employee = await EmployeeMaster.findOne({ user: record.user._id });

      return {
        _id: record._id,
        employee: {
          _id: record.user._id,
          name: record.user.name,
          email: record.user.email,
          department: record.user.department
        },
        date: record.date,
        status: record.status,
        isPresent: record.isPresent,
        times: {
          final_in: record.biometricTimeIn,
          final_out: record.biometricTimeOut,
          worked_hours: record.totalHoursWorked
        },
        mergeDetails: record.attendanceMergeDetails || {},
        salary: {
          basicForDay: record.basicSalaryForDay || 0,
          hourlyRate: employee?.calculatedHourlyRate || 0
        },
        verification: {
          method: record.verificationMethod,
          isVerified: record.isVerified
        }
      };
    }));

    res.json({
      success: true,
      data: formattedRecords,
      count: formattedRecords.length
    });

  } catch (error) {
    console.error('❌ Error fetching attendance:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route   GET /api/attendance/reconcile
 * @desc    Get reconciliation summary with merge statistics
 * @access  Private
 */
router.get('/reconcile', auth, async (req, res) => {
  try {
    const { startDate, endDate } = req.query;

    if (!startDate || !endDate) {
      return res.status(400).json({
        success: false,
        error: 'Start date and end date are required'
      });
    }

    const start = new Date(startDate);
    const end = new Date(endDate);

    const attendance = await DailyAttendance.find({
      date: { $gte: start, $lte: end }
    });

    // Analyze merge cases
    const mergeCaseCounts = {};
    const remarksCounts = {};
    let totalMismatches = 0;
    let withinTolerance = 0;

    for (const record of attendance) {
      const mergeDetail = record.attendanceMergeDetails;
      if (mergeDetail) {
        mergeCaseCounts[mergeDetail.case] = (mergeCaseCounts[mergeDetail.case] || 0) + 1;
        remarksCounts[mergeDetail.remarks] = (remarksCounts[mergeDetail.remarks] || 0) + 1;

        if (mergeDetail.remarks.includes('MISMATCH')) {
          totalMismatches++;
        } else {
          withinTolerance++;
        }
      }
    }

    res.json({
      success: true,
      dateRange: { start, end },
      summary: {
        totalRecords: attendance.length,
        withinTolerance: withinTolerance,
        mismatchesDetected: totalMismatches,
        mergeDistribution: mergeCaseCounts,
        remarksDistribution: remarksCounts
      }
    });

  } catch (error) {
    console.error('❌ Error getting reconciliation:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Helper: Group merge details by case
 */
function _groupByMergeCase(mergeDetails) {
  const grouped = {};
  for (const detail of mergeDetails) {
    const caseType = detail.mergeDetails?.case || 'UNKNOWN';
    grouped[caseType] = (grouped[caseType] || 0) + 1;
  }
  return grouped;
}

module.exports = router;
