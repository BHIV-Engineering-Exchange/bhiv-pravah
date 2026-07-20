import RLExperience from '../models/RLExperience.js';
import logger from '../config/logger.js';
import axios from 'axios';

class InsightFlowService {
  /**
   * Log an experience to the buffer
   */
  async logExperience(experienceData) {
    try {
      const experience = await RLExperience.create(experienceData);
      
      // If InsightCore endpoint is configured, send telemetry
      if (process.env.INSIGHTCORE_ENABLED === 'true' && process.env.INSIGHTCORE_ENDPOINT) {
        this.sendToInsightCore(experience).catch(err => {
          logger.warn('Failed to send telemetry to InsightCore:', err.message);
        });
      }
      
      return experience;
    } catch (error) {
      logger.error('Log experience error:', error);
      throw error;
    }
  }
  
  /**
   * Get experiences with filters
   */
  async getExperiences(filters = {}, pagination = {}) {
    const {
      sessionId,
      userId,
      action,
      dateFrom,
      dateTo,
    } = filters;
    
    const {
      page = 1,
      limit = 100,
    } = pagination;
    
    const query = {};
    
    if (sessionId) {
      query.sessionId = sessionId;
    }
    
    if (userId) {
      query.userId = userId;
    }
    
    if (action) {
      query.action = action;
    }
    
    if (dateFrom || dateTo) {
      query['metadata.timestamp'] = {};
      if (dateFrom) query['metadata.timestamp'].$gte = new Date(dateFrom);
      if (dateTo) query['metadata.timestamp'].$lte = new Date(dateTo);
    }
    
    const skip = (page - 1) * limit;
    
    const [experiences, total] = await Promise.all([
      RLExperience.find(query)
        .populate('userId', 'name email role')
        .sort({ 'metadata.timestamp': -1 })
        .skip(skip)
        .limit(limit),
      RLExperience.countDocuments(query),
    ]);
    
    return {
      experiences,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    };
  }
  
  /**
   * Get experience statistics
   */
  async getExperienceStats(dateFrom, dateTo) {
    const match = {};
    
    if (dateFrom || dateTo) {
      match['metadata.timestamp'] = {};
      if (dateFrom) match['metadata.timestamp'].$gte = new Date(dateFrom);
      if (dateTo) match['metadata.timestamp'].$lte = new Date(dateTo);
    }
    
    const [actionStats, rewardStats, errorStats] = await Promise.all([
      // Group by action
      RLExperience.aggregate([
        { $match: match },
        {
          $group: {
            _id: '$action',
            count: { $sum: 1 },
            avgReward: { $avg: '$reward' },
            avgDuration: { $avg: '$metadata.duration' },
          },
        },
        { $sort: { count: -1 } },
      ]),
      
      // Reward distribution
      RLExperience.aggregate([
        { $match: match },
        {
          $group: {
            _id: null,
            totalReward: { $sum: '$reward' },
            avgReward: { $avg: '$reward' },
            maxReward: { $max: '$reward' },
            minReward: { $min: '$reward' },
          },
        },
      ]),
      
      // Error statistics
      RLExperience.aggregate([
        { $match: { ...match, 'metadata.errorOccurred': true } },
        {
          $group: {
            _id: '$metadata.errorType',
            count: { $sum: 1 },
          },
        },
        { $sort: { count: -1 } },
      ]),
    ]);
    
    return {
      actionStats,
      rewardStats: rewardStats[0] || {},
      errorStats,
    };
  }
  
  /**
   * Send telemetry to InsightCore (external RL service)
   */
  async sendToInsightCore(experience) {
    try {
      const payload = {
        state: experience.state,
        action: experience.action,
        reward: experience.reward,
        next_state: experience.nextState,
        done: experience.isTerminal,
        metadata: experience.metadata,
      };
      
      await axios.post(process.env.INSIGHTCORE_ENDPOINT, payload, {
        timeout: 5000,
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': process.env.INSIGHTCORE_API_KEY || '',
        },
      });
      
      logger.info('Telemetry sent to InsightCore');
    } catch (error) {
      logger.error('InsightCore send error:', error.message);
      throw error;
    }
  }
  
  /**
   * Calculate reward for an action
   */
  calculateReward(action, outcome) {
    // Reward calculation logic
    const rewards = {
      // Positive rewards
      'invoice.created': 10,
      'invoice.sent': 15,
      'payment.recorded': 20,
      'expense.approved': 10,
      'ledger.verified': 25,
      
      // Negative rewards
      'validation.error': -5,
      'double_entry.failed': -15,
      'payment.failed': -10,
      'expense.rejected': -5,
    };
    
    let baseReward = rewards[action] || 0;
    
    // Adjust based on outcome
    if (outcome.errorOccurred) {
      baseReward -= 5;
    }
    
    if (outcome.duration) {
      // Penalize slow actions (>5 seconds)
      if (outcome.duration > 5000) {
        baseReward -= 2;
      }
    }
    
    return baseReward;
  }
}

export default new InsightFlowService();