import databaseService from '../services/database.service.js';
import logger from '../config/logger.js';

// @desc    Get database statistics
// @route   GET /api/v1/database/stats
// @access  Private (admin only)
export const getDatabaseStats = async (req, res) => {
  try {
    const stats = await databaseService.getDatabaseStats();
    
    res.json({
      success: true,
      data: stats,
    });
  } catch (error) {
    logger.error('Get database stats error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get collection statistics
// @route   GET /api/v1/database/collections
// @access  Private (admin only)
export const getCollectionStats = async (req, res) => {
  try {
    const stats = await databaseService.getCollectionStats();
    
    res.json({
      success: true,
      data: stats,
    });
  } catch (error) {
    logger.error('Get collection stats error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get index information
// @route   GET /api/v1/database/indexes
// @access  Private (admin only)
export const getIndexInfo = async (req, res) => {
  try {
    const indexInfo = await databaseService.getIndexInfo();
    
    res.json({
      success: true,
      data: indexInfo,
    });
  } catch (error) {
    logger.error('Get index info error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get optimization suggestions
// @route   GET /api/v1/database/optimize
// @access  Private (admin only)
export const getOptimizationSuggestions = async (req, res) => {
  try {
    const suggestions = await databaseService.suggestOptimizations();
    
    res.json({
      success: true,
      data: suggestions,
    });
  } catch (error) {
    logger.error('Get optimization suggestions error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Create all indexes
// @route   POST /api/v1/database/indexes
// @access  Private (admin only)
export const createIndexes = async (req, res) => {
  try {
    const results = await databaseService.createAllIndexes();
    
    res.json({
      success: true,
      data: results,
      message: 'Index creation completed',
    });
  } catch (error) {
    logger.error('Create indexes error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};