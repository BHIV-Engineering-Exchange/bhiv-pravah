import 'dotenv/config';
import logger from '../src/config/logger.js';

// Validate required environment variables
const requiredEnvVars = [
  'MONGODB_URI',
  'JWT_SECRET',
  'JWT_REFRESH_SECRET',
  'HMAC_SECRET'
];

const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);

if (missingVars.length > 0) {
  logger.error(`Missing required environment variables: ${missingVars.join(', ')}`);
  process.exit(1);
}

// Start the server
logger.info('Starting ARTHA backend server...');
import('../src/server.js')
  .then(() => {
    logger.info('Server started successfully');
  })
  .catch(err => {
    logger.error('Failed to start server:', err);
    process.exit(1);
  });