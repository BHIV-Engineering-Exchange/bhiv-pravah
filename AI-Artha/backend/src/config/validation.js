import logger from './logger.js';
import { getResolvedUrls } from './urls.js';

const REQUIRED_PROD_VARS = [
  'MONGODB_URI',
  'JWT_SECRET',
  'HMAC_SECRET',
];

const RECOMMENDED_VARS = [
  'API_PUBLIC_URL',
  'REDIS_PASSWORD',
  'FRONTEND_URL',
  'APP_URL',
  'LOG_LEVEL',
];

export const validateEnvironment = () => {
  const errors = [];
  const warnings = [];

  REQUIRED_PROD_VARS.forEach(varName => {
    if (!process.env[varName]) {
      errors.push(`Missing required environment variable: ${varName}`);
    } else if (process.env[varName].includes('CHANGE_ME') ||
               process.env[varName].includes('YOUR_SUPER_SECRET') ||
               process.env[varName].length < 32) {
      errors.push(`Environment variable ${varName} appears to use default/weak value`);
    }
  });

  RECOMMENDED_VARS.forEach(varName => {
    if (!process.env[varName]) {
      warnings.push(`Recommended environment variable not set: ${varName}`);
    }
  });

  if (process.env.NODE_ENV === 'production') {
    const hasSpa =
      (process.env.FRONTEND_URL && !process.env.FRONTEND_URL.includes('localhost')) ||
      (process.env.APP_URL && !process.env.APP_URL.includes('localhost'));
    if (!hasSpa) {
      warnings.push(
        'Set FRONTEND_URL (legacy) or APP_URL to your production SPA origin (https://…, no trailing slash)',
      );
    }
    try {
      const { SPA_URL, API_PUBLIC_URL } = getResolvedUrls();
      const spaHost = new URL(SPA_URL).hostname;
      const apiHost = new URL(API_PUBLIC_URL).hostname;
      if (
        (apiHost === 'localhost' || apiHost === '127.0.0.1') &&
        spaHost !== 'localhost' &&
        spaHost !== '127.0.0.1'
      ) {
        warnings.push(
          'Set API_PUBLIC_URL to your deployed API base URL when the SPA is not on localhost.',
        );
      }
    } catch {
      /* ignore invalid URL env */
    }
  }

  if (errors.length > 0) {
    logger.error('Environment validation failed:');
    errors.forEach(error => logger.error(`  - ${error}`));
    throw new Error('Environment validation failed. Check logs for details.');
  }

  if (warnings.length > 0) {
    logger.warn('Environment validation warnings:');
    warnings.forEach(warning => logger.warn(`  - ${warning}`));
  }

  logger.info('Environment validation passed');
  return true;
};

export const validateDatabaseConfig = () => {
  if (!process.env.MONGODB_URI) {
    throw new Error('MONGODB_URI is required');
  }
  if (!process.env.MONGODB_URI.includes('@') && process.env.NODE_ENV === 'production') {
    logger.warn('MongoDB URI does not contain credentials - ensure authentication is configured');
  }
};

export const validateJWTConfig = () => {
  const jwtSecret = process.env.JWT_SECRET;
  if (!jwtSecret) {
    throw new Error('JWT_SECRET is required for API token signing and verification');
  }
  if (jwtSecret.length < 32) {
    throw new Error('JWT_SECRET must be at least 32 characters long');
  }
};

export const validateRedisConfig = () => {
  if (process.env.REDIS_HOST && !process.env.REDIS_PASSWORD) {
    logger.warn('Redis host configured but no password set - consider setting REDIS_PASSWORD');
  }
};

export default {
  validateEnvironment,
  validateDatabaseConfig,
  validateJWTConfig,
  validateRedisConfig,
};
