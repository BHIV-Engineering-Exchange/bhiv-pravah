import logger from '../config/logger.js';
import { getRedisClient } from '../config/redis.js';

class PerformanceService {
  constructor() {
    this.metrics = {
      requests: {
        total: 0,
        slow: 0,
        errors: 0,
      },
      responseTime: {
        min: Infinity,
        max: 0,
        avg: 0,
        total: 0,
      },
      memory: {
        peak: 0,
        current: 0,
      },
    };
  }

  /**
   * Record request metrics
   */
  recordRequest(duration, statusCode) {
    this.metrics.requests.total++;
    
    if (duration > 1000) {
      this.metrics.requests.slow++;
    }
    
    if (statusCode >= 400) {
      this.metrics.requests.errors++;
    }

    // Update response time metrics
    this.metrics.responseTime.min = Math.min(this.metrics.responseTime.min, duration);
    this.metrics.responseTime.max = Math.max(this.metrics.responseTime.max, duration);
    this.metrics.responseTime.total += duration;
    this.metrics.responseTime.avg = this.metrics.responseTime.total / this.metrics.requests.total;
  }

  /**
   * Record memory usage
   */
  recordMemoryUsage(memUsage) {
    this.metrics.memory.current = memUsage.heapUsed;
    this.metrics.memory.peak = Math.max(this.metrics.memory.peak, memUsage.heapUsed);
  }

  /**
   * Get current performance metrics
   */
  getMetrics() {
    const memUsage = process.memoryUsage();
    
    return {
      uptime: process.uptime(),
      requests: {
        ...this.metrics.requests,
        slowPercentage: this.metrics.requests.total > 0 
          ? ((this.metrics.requests.slow / this.metrics.requests.total) * 100).toFixed(2)
          : 0,
        errorPercentage: this.metrics.requests.total > 0
          ? ((this.metrics.requests.errors / this.metrics.requests.total) * 100).toFixed(2)
          : 0,
      },
      responseTime: {
        ...this.metrics.responseTime,
        min: this.metrics.responseTime.min === Infinity ? 0 : this.metrics.responseTime.min,
        avg: Math.round(this.metrics.responseTime.avg),
      },
      memory: {
        current: {
          rss: Math.round(memUsage.rss / 1024 / 1024),
          heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024),
          heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024),
          external: Math.round(memUsage.external / 1024 / 1024),
        },
        peak: Math.round(this.metrics.memory.peak / 1024 / 1024),
      },
      redis: this.getRedisMetrics(),
    };
  }

  /**
   * Get Redis connection metrics
   */
  getRedisMetrics() {
    const redisClient = getRedisClient();
    
    if (!redisClient) {
      return { status: 'disabled' };
    }

    return {
      status: redisClient.isReady ? 'connected' : 'disconnected',
      // Additional Redis metrics could be added here
    };
  }

  /**
   * Reset metrics (useful for testing or periodic resets)
   */
  resetMetrics() {
    this.metrics = {
      requests: {
        total: 0,
        slow: 0,
        errors: 0,
      },
      responseTime: {
        min: Infinity,
        max: 0,
        avg: 0,
        total: 0,
      },
      memory: {
        peak: 0,
        current: 0,
      },
    };
    
    logger.info('Performance metrics reset');
  }

  /**
   * Get system health based on performance metrics
   */
  getHealthStatus() {
    const metrics = this.getMetrics();
    const issues = [];

    // Check for high error rate
    if (parseFloat(metrics.requests.errorPercentage) > 5) {
      issues.push('High error rate detected');
    }

    // Check for slow response times
    if (parseFloat(metrics.requests.slowPercentage) > 10) {
      issues.push('High percentage of slow requests');
    }

    // Check memory usage
    if (metrics.memory.current.heapUsed > 500) {
      issues.push('High memory usage');
    }

    return {
      status: issues.length === 0 ? 'healthy' : 'warning',
      issues,
      metrics,
    };
  }
}

export default new PerformanceService();