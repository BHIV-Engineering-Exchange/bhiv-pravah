import insightflowService from '../services/insightflow.service.js';
import logger from '../config/logger.js';

// @desc    Log RL experience
// @route   POST /api/v1/insightflow/experience
// @access  Private
export const logExperience = async (req, res) => {
  try {
    const experience = await insightflowService.logExperience({
      ...req.body,
      userId: req.user._id,
    });
    
    res.status(201).json({
      success: true,
      data: experience,
    });
  } catch (error) {
    logger.error('Log experience error:', error);
    res.status(400).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get experiences
// @route   GET /api/v1/insightflow/experiences
// @access  Private (admin)
export const getExperiences = async (req, res) => {
  try {
    const filters = {
      sessionId: req.query.sessionId,
      userId: req.query.userId,
      action: req.query.action,
      dateFrom: req.query.dateFrom,
      dateTo: req.query.dateTo,
    };
    
    const pagination = {
      page: parseInt(req.query.page) || 1,
      limit: parseInt(req.query.limit) || 100,
    };
    
    const result = await insightflowService.getExperiences(filters, pagination);
    
    res.json({
      success: true,
      data: result.experiences,
      pagination: result.pagination,
    });
  } catch (error) {
    logger.error('Get experiences error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get experience stats
// @route   GET /api/v1/insightflow/stats
// @access  Private (admin)
export const getExperienceStats = async (req, res) => {
  try {
    const stats = await insightflowService.getExperienceStats(
      req.query.dateFrom,
      req.query.dateTo
    );
    
    res.json({
      success: true,
      data: stats,
    });
  } catch (error) {
    logger.error('Get experience stats error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};