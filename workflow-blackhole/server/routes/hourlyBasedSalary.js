const express = require('express');
const router = express.Router();
const hourlyBasedSalaryController = require('../controllers/hourlyBasedSalaryController');
const authenticateToken = require('../middleware/auth');
const adminAuth = require('../middleware/adminAuth');

/**
 * Hourly-Based Salary Management Routes
 * All routes calculate salary based on worked hours from daily attendance
 * Tracks office vs remote hours for better insights
 */

// ============================================
// Employee Salary Calculation Routes
// ============================================

/**
 * Calculate monthly salary for a specific employee
 * GET /api/hourly-salary/employee/:userId/calculate/:year/:month
 * Returns detailed salary breakdown with hours worked, office/remote split
 */
router.get(
  '/employee/:userId/calculate/:year/:month',
  authenticateToken,
  hourlyBasedSalaryController.calculateEmployeeMonthlySalary
);

/**
 * Get detailed hours breakdown for an employee (office vs remote)
 * GET /api/hourly-salary/employee/:userId/hours-breakdown/:year/:month
 */
router.get(
  '/employee/:userId/hours-breakdown/:year/:month',
  authenticateToken,
  hourlyBasedSalaryController.getEmployeeHoursBreakdown
);

// ============================================
// Activity Log Routes
// ============================================

/**
 * Get activity log showing all employees' worked hours
 * GET /api/hourly-salary/activity-log
 * Query params: year, month, startDate, endDate
 * Shows daily worked hours for all employees with office/remote breakdown
 */
router.get(
  '/activity-log',
  authenticateToken,
  hourlyBasedSalaryController.getEmployeeActivityLog
);

// ============================================
// Admin Dashboard Routes
// ============================================

/**
 * Get admin dashboard with summary of all employees
 * GET /api/hourly-salary/admin/dashboard/:year/:month
 * Shows total hours (office + remote), salary calculations for all employees
 */
router.get(
  '/admin/dashboard/:year/:month',
  authenticateToken,
  adminAuth,
  hourlyBasedSalaryController.getAdminDashboard
);

// ============================================
// Work Location Management Routes
// ============================================

/**
 * Update work location type for a specific attendance record
 * PATCH /api/hourly-salary/attendance/:attendanceId/location
 * Body: { workLocationType: 'Office' | 'Home' | 'Remote' | 'Hybrid' }
 */
router.patch(
  '/attendance/:attendanceId/location',
  authenticateToken,
  hourlyBasedSalaryController.updateWorkLocationType
);

// ============================================
// Hourly Rate Management Routes
// ============================================

/**
 * Bulk update hourly rates for employees
 * POST /api/hourly-salary/admin/hourly-rates/bulk-update
 * Body: { updates: [{ userId, hourlyRate }] }
 */
router.post(
  '/admin/hourly-rates/bulk-update',
  authenticateToken,
  adminAuth,
  hourlyBasedSalaryController.bulkUpdateHourlyRates
);

// ============================================
// Quick Access Routes (for current month)
// ============================================

/**
 * Get current month salary for logged-in user
 * GET /api/hourly-salary/my-salary/current
 */
router.get(
  '/my-salary/current',
  authenticateToken,
  async (req, res) => {
    try {
      const now = new Date();
      const year = now.getFullYear();
      const month = now.getMonth() + 1;
      
      req.params = { userId: req.user.id, year, month };
      await hourlyBasedSalaryController.calculateEmployeeMonthlySalary(req, res);
    } catch (error) {
      res.status(500).json({ 
        success: false, 
        message: 'Error fetching current salary',
        error: error.message 
      });
    }
  }
);

/**
 * Get current month activity log
 * GET /api/hourly-salary/activity-log/current
 */
router.get(
  '/activity-log/current',
  authenticateToken,
  async (req, res) => {
    try {
      const now = new Date();
      req.query = { 
        year: now.getFullYear(), 
        month: now.getMonth() + 1 
      };
      await hourlyBasedSalaryController.getEmployeeActivityLog(req, res);
    } catch (error) {
      res.status(500).json({ 
        success: false, 
        message: 'Error fetching current activity log',
        error: error.message 
      });
    }
  }
);

/**
 * Get current month admin dashboard
 * GET /api/hourly-salary/admin/dashboard/current
 */
router.get(
  '/admin/dashboard/current',
  authenticateToken,
  adminAuth,
  async (req, res) => {
    try {
      const now = new Date();
      req.params = { 
        year: now.getFullYear(), 
        month: now.getMonth() + 1 
      };
      await hourlyBasedSalaryController.getAdminDashboard(req, res);
    } catch (error) {
      res.status(500).json({ 
        success: false, 
        message: 'Error fetching current dashboard',
        error: error.message 
      });
    }
  }
);

module.exports = router;
