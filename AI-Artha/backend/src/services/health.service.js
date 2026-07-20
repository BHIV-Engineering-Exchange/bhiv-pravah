import mongoose from 'mongoose';
import { getRedisClient } from '../config/redis.js';
import logger from '../config/logger.js';
import performanceService from './performance.service.js';

class HealthService {
  async checkDatabase() {
    try {
      const state = mongoose.connection.readyState;
      const states = {
        0: 'disconnected',
        1: 'connected',
        2: 'connecting',
        3: 'disconnecting',
      };

      return {
        status: state === 1 ? 'healthy' : 'unhealthy',
        state: states[state],
        host: mongoose.connection.host,
        name: mongoose.connection.name,
      };
    } catch (error) {
      logger.error('Database health check error:', error);
      return {
        status: 'unhealthy',
        error: error.message,
      };
    }
  }

  async checkRedis() {
    try {
      const redisClient = getRedisClient();
      if (!redisClient) {
        return {
          status: 'disabled',
          message: 'Redis not configured',
        };
      }

      const pong = await redisClient.ping();
      return {
        status: pong === 'PONG' ? 'healthy' : 'unhealthy',
        response: pong,
      };
    } catch (error) {
      logger.error('Redis health check error:', error);
      return {
        status: 'unhealthy',
        error: error.message,
      };
    }
  }

  async checkDiskSpace() {
    try {
      const fs = await import('fs');
      const stats = fs.statSync('./');
      
      return {
        status: 'healthy',
        available: 'N/A', // Would need additional package for detailed disk info
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error.message,
      };
    }
  }

  async getSystemHealth() {
    const [database, redis, disk] = await Promise.all([
      this.checkDatabase(),
      this.checkRedis(),
      this.checkDiskSpace(),
    ]);

    // Get performance health status
    const performanceHealth = performanceService.getHealthStatus();

    const overall = 
      database.status === 'healthy' && 
      (redis.status === 'healthy' || redis.status === 'disabled') &&
      disk.status === 'healthy' &&
      performanceHealth.status === 'healthy'
        ? 'healthy' 
        : performanceHealth.status === 'warning' ? 'warning' : 'unhealthy';

    return {
      status: overall,
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '0.1.0',
      environment: process.env.NODE_ENV,
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      performance: performanceHealth.metrics,
      issues: performanceHealth.issues,
      components: {
        database,
        redis,
        disk,
      },
    };
  }
}

export default new HealthService();