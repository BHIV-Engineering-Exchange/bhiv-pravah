import dotenv from 'dotenv';
import { validateEnvironment } from '../src/config/validation.js';
import logger from '../src/config/logger.js';

// Load environment variables
dotenv.config({ path: '.env.production' });

const startProduction = async () => {
  try {
    logger.info('Starting Artha in production mode...');
    
    // Validate environment
    logger.info('Validating environment configuration...');
    validateEnvironment();
    
    // Import and start server after validation
    const { default: app } = await import('../src/server.js');
    
    logger.info('Production startup completed successfully');
  } catch (error) {
    logger.error('Production startup failed:', error.message);
    process.exit(1);
  }
};

startProduction();