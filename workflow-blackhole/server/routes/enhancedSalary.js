const express = require('express');
const router = express.Router();
const enhancedSalaryController = require('../controllers/enhancedSalaryController');
const authenticateToken = require('../middleware/auth');

// Log all requests to this router
router.use((req, res, next) => {
  console.log(`[Enhanced Salary] ${req.method} ${req.path}`, req.params, req.query);
  next();
});

/**
 * Enhanced Salary Management Routes
 * Includes live attendance integration, biometric data upload, and WFH tracking
 */

// Biometric data upload
router.post(
  '/upload-biometric',
  authenticateToken,
  enhancedSalaryController.uploadMiddleware, // Multer middleware
  enhancedSalaryController.uploadBiometricData
);

// Calculate salary for specific employee
router.get(
  '/calculate/:userId/:year/:month',
  authenticateToken,
  enhancedSalaryController.calculateEmployeeSalary
);

// Get salary dashboard for all employees
router.get(
  '/dashboard/:year/:month',
  authenticateToken,
  enhancedSalaryController.getSalaryDashboard
);

// Get detailed hours breakdown for an employee
router.get(
  '/hours-breakdown/:userId/:year/:month',
  authenticateToken,
  enhancedSalaryController.getHoursBreakdown
);

// Get WFH vs Office analysis
router.get(
  '/wfh-analysis/:userId/:year/:month',
  authenticateToken,
  enhancedSalaryController.getWFHAnalysis
);

module.exports = router;
