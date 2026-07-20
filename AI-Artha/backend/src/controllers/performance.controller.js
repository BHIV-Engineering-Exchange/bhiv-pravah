import performanceService from '../services/performance.service.js';
import logger from '../config/logger.js';

// @desc    Get performance metrics
// @route   GET /api/v1/performance/metrics
// @access  Private (admin only)
export const getMetrics = async (req, res) => {
  try {
    const metrics = performanceService.getMetrics();
    
    res.json({
      success: true,
      data: metrics,
    });
  } catch (error) {
    logger.error('Get performance metrics error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get performance health status
// @route   GET /api/v1/performance/health
// @access  Private (admin only)
export const getHealthStatus = async (req, res) => {
  try {
    const healthStatus = performanceService.getHealthStatus();
    
    res.json({
      success: true,
      data: healthStatus,
    });
  } catch (error) {
    logger.error('Get performance health error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Reset performance metrics
// @route   POST /api/v1/performance/reset
// @access  Private (admin only)
export const resetMetrics = async (req, res) => {
  try {
    performanceService.resetMetrics();
    
    res.json({
      success: true,
      message: 'Performance metrics reset successfully',
    });
  } catch (error) {
    logger.error('Reset performance metrics error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};