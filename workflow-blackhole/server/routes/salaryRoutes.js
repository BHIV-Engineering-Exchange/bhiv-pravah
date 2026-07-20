const express = require('express');
const router = express.Router();
const salaryController = require('../controllers/salaryController');
const protect = require('../middleware/auth');
const adminAuth = require('../middleware/adminAuth');

/**
 * Salary Management Routes
 * All routes require authentication
 * Admin-only routes require adminAuth middleware
 */

// Upload biometric attendance file and calculate salaries
// POST /api/salary/upload
router.post('/upload', protect, adminAuth, salaryController.uploadAndCalculate);

// Get salary records for a specific month
// GET /api/salary/:month (format: YYYY-MM)
router.get('/:month', protect, salaryController.getSalaryByMonth);

// Update hourly rate for a specific salary record
// PUT /api/salary/:id/rate
router.put('/:id/rate', protect, adminAuth, salaryController.updateHourlyRate);

// Delete a salary record
// DELETE /api/salary/:id
router.delete('/:id', protect, adminAuth, salaryController.deleteSalaryRecord);

// Get salary statistics for a specific month
// GET /api/salary/stats/:month
router.get('/stats/:month', protect, salaryController.getSalaryStats);

// Holiday Management Routes

// Get all holidays (optional query params: month, year)
// GET /api/salary/holidays
router.get('/holidays', protect, salaryController.getAllHolidays);

// Add or update a holiday
// POST /api/salary/holidays
router.post('/holidays', protect, adminAuth, salaryController.manageHolidays);

// Delete a holiday
// DELETE /api/salary/holidays/:id
router.delete('/holidays/:id', protect, adminAuth, salaryController.deleteHoliday);

module.exports = router;
