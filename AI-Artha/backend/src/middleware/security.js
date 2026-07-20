import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import { body, validationResult } from 'express-validator';
import AuditLog from '../models/AuditLog.js';
import logger from '../config/logger.js';
import { validateJWTConfig, validateRedisConfig } from '../config/validation.js';

// Helmet configuration
export const helmetConfig = helmet({
  contentSecurityPolicy: false, // Disable CSP for API
  crossOriginResourcePolicy: false, // Allow cross-origin requests
  crossOriginOpenerPolicy: false,
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true,
  },
});

// Validate security configuration on load
if (process.env.NODE_ENV === 'production') {
  try {
    validateJWTConfig();
    validateRedisConfig();
  } catch (error) {
    logger.error('Security configuration validation failed:', error.message);
  }
}

// Rate limiting - More lenient for development
export const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000,
  max: parseInt(process.env.RATE_LIMIT_MAX) || 1000, // Increased from 100 to 1000
  message: 'Too many requests from this IP, please try again later',
  standardHeaders: true,
  legacyHeaders: false,
  skip: (req) => process.env.NODE_ENV === 'development', // Skip in development
});

function authRateLimitKey(req) {
  const email = String(req.body?.email || '')
    .trim()
    .toLowerCase();
  return email ? `${req.ip}:${email}` : req.ip;
}

// Password login — tighter cap (brute-force protection)
export const authPasswordLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: parseInt(process.env.AUTH_PASSWORD_RATE_LIMIT_MAX, 10) || 50,
  keyGenerator: authRateLimitKey,
  message: 'Too many login attempts from this IP. Try again in a few minutes.',
  standardHeaders: true,
  legacyHeaders: false,
  skipSuccessfulRequests: true,
  skip: (req) => process.env.NODE_ENV === 'development',
});

export const authSignupLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: parseInt(process.env.AUTH_SIGNUP_RATE_LIMIT_MAX, 10) || 20,
  keyGenerator: authRateLimitKey,
  message: 'Too many signup attempts from this IP. Try again in a few minutes.',
  standardHeaders: true,
  legacyHeaders: false,
  skipSuccessfulRequests: true,
  skip: (req) => process.env.NODE_ENV === 'development',
});

/** @deprecated use authPasswordLimiter */
export const authLimiter = authPasswordLimiter;

// Legacy exports for backward compatibility
export const apiLimiter = limiter;

// Input validation helper
export const validate = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({
      success: false,
      errors: errors.array().map(err => ({
        field: err.param,
        message: err.msg,
      })),
    });
  }
  next();
};

// Sanitize input (remove potential XSS)
export const sanitizeInput = (req, res, next) => {
  const sanitize = (obj) => {
    for (const key in obj) {
      if (typeof obj[key] === 'string') {
        obj[key] = obj[key].trim();
        // Remove potential script tags
        obj[key] = obj[key].replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
      } else if (typeof obj[key] === 'object' && obj[key] !== null) {
        sanitize(obj[key]);
      }
    }
  };
  
  if (req.body) sanitize(req.body);
  if (req.query) sanitize(req.query);
  if (req.params) sanitize(req.params);
  
  next();
};

// Audit logger middleware
export const auditLogger = (action, entityType) => {
  return async (req, res, next) => {
    // Store original json method
    const originalJson = res.json.bind(res);
    
    res.json = function(data) {
      // Log after successful response
      if (res.statusCode >= 200 && res.statusCode < 300) {
        const entityId = data?.data?._id || data?.data?.id || req.params?.id || 'unknown';
        
        AuditLog.create({
          action,
          entityType,
          entityId: String(entityId),
          userId: req.user?._id,
          ipAddress: req.ip || req.connection.remoteAddress,
          userAgent: req.get('user-agent'),
          changes: req.body,
          metadata: {
            method: req.method,
            path: req.path,
            statusCode: res.statusCode,
          },
        }).catch(err => logger.error('Audit log error:', err));
      }
      
      return originalJson(data);
    };
    
    next();
  };
};

// Watermark middleware (adds traceable header)
export const watermark = (req, res, next) => {
  const watermarkId = `ARTHA-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  res.setHeader('X-Artha-Trace-Id', watermarkId);
  req.traceId = watermarkId;
  next();
};