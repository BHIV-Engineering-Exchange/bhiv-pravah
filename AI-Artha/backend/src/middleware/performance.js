import logger from '../config/logger.js';
import performanceService from '../services/performance.service.js';

/**
 * Request timing middleware
 */
export const requestTimer = (req, res, next) => {
  const startTime = Date.now();

  // Log when response finishes
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    const logData = {
      method: req.method,
      url: req.originalUrl || req.url,
      status: res.statusCode,
      duration: `${duration}ms`,
      ip: req.ip || req.connection.remoteAddress,
      userAgent: req.get('user-agent'),
    };

    // Record metrics
    performanceService.recordRequest(duration, res.statusCode);

    // Log slow requests
    if (duration > 1000) {
      logger.warn('Slow request detected', logData);
    } else {
      logger.info('Request completed', logData);
    }
  });

  next();
};

/**
 * Memory usage monitor
 */
export const memoryMonitor = () => {
  setInterval(() => {
    const memUsage = process.memoryUsage();
    const memoryData = {
      rss: `${Math.round(memUsage.rss / 1024 / 1024)}MB`,
      heapTotal: `${Math.round(memUsage.heapTotal / 1024 / 1024)}MB`,
      heapUsed: `${Math.round(memUsage.heapUsed / 1024 / 1024)}MB`,
      external: `${Math.round(memUsage.external / 1024 / 1024)}MB`,
    };

    // Record memory metrics
    performanceService.recordMemoryUsage(memUsage);

    logger.info('Memory usage', memoryData);

    // Alert if memory usage is high
    if (memUsage.heapUsed > 500 * 1024 * 1024) {
      // > 500MB
      logger.warn('High memory usage detected', memoryData);
    }
  }, 60000); // Check every minute
};