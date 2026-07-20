import { cacheGet, cacheSet } from '../config/redis.js';
import logger from '../config/logger.js';
import crypto from 'crypto';

/**
 * Cache middleware for GET requests with user-specific caching
 */
export const cacheMiddleware = (duration = 3600, options = {}) => {
  return async (req, res, next) => {
    // Only cache GET requests
    if (req.method !== 'GET') {
      return next();
    }

    // Generate cache key with user context for protected routes
    let key;
    if (req.user && !options.global) {
      // User-specific cache for protected routes
      key = `cache:user:${req.user._id}:${req.originalUrl || req.url}`;
    } else {
      // Global cache for public routes
      key = `cache:global:${req.originalUrl || req.url}`;
    }

    try {
      // Try to get cached data
      const cachedData = await cacheGet(key);

      if (cachedData) {
        logger.info(`Cache hit: ${key}`);
        return res.json(cachedData);
      }

      // Store original res.json
      const originalJson = res.json.bind(res);

      // Override res.json to cache the response
      res.json = function (data) {
        // Only cache successful responses
        if (res.statusCode >= 200 && res.statusCode < 300) {
          cacheSet(key, data, duration).catch((err) => {
            logger.error('Cache set error:', err);
          });
        }

        // Send the response
        return originalJson(data);
      };

      next();
    } catch (error) {
      logger.error('Cache middleware error:', error);
      next();
    }
  };
};

/**
 * Global cache middleware (for public routes)
 */
export const globalCacheMiddleware = (duration = 3600) => {
  return cacheMiddleware(duration, { global: true });
};

/**
 * Cache invalidation helper
 */
export const invalidateCache = (pattern) => {
  // This would be implemented with Redis SCAN command
  // For now, we'll implement pattern-based invalidation in the service layer
  logger.info(`Cache invalidation requested for pattern: ${pattern}`);
};