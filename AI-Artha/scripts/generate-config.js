import crypto from 'crypto';
import fs from 'fs';
import path from 'path';

// Generate secure random string
const generateSecret = (length = 64) => {
  return crypto.randomBytes(length).toString('hex');
};

// Generate strong password
const generatePassword = (length = 32) => {
  const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*';
  let password = '';
  for (let i = 0; i < length; i++) {
    password += charset.charAt(Math.floor(Math.random() * charset.length));
  }
  return password;
};

const generateProductionConfig = () => {
  console.log('🔐 Generating secure production configuration...\n');

  const config = {
    // MongoDB
    MONGO_ROOT_USER: 'artha_admin',
    MONGO_ROOT_PASSWORD: generatePassword(24),
    
    // Redis
    REDIS_PASSWORD: generatePassword(24),
    
    // JWT Secrets
    JWT_SECRET: generateSecret(32),
    JWT_REFRESH_SECRET: generateSecret(32),
    HMAC_SECRET: generateSecret(32),
    
    // API URL (to be customized)
    VITE_API_URL: 'https://your-domain.com/api/v1'
  };

  // Generate root .env file
  const rootEnvContent = Object.entries(config)
    .map(([key, value]) => `${key}=${value}`)
    .join('\n');

  // Generate backend .env.production file
  const backendConfig = {
    NODE_ENV: 'production',
    PORT: '5000',
    API_VERSION: 'v1',
    MONGODB_URI: `mongodb://${config.MONGO_ROOT_USER}:${config.MONGO_ROOT_PASSWORD}@mongodb:27017/artha_prod?authSource=admin`,
    JWT_SECRET: config.JWT_SECRET,
    JWT_EXPIRE: '24h',
    JWT_REFRESH_SECRET: config.JWT_REFRESH_SECRET,
    HMAC_SECRET: config.HMAC_SECRET,
    RATE_LIMIT_WINDOW_MS: '900000',
    RATE_LIMIT_MAX: '100',
    REDIS_HOST: 'redis',
    REDIS_PORT: '6379',
    REDIS_PASSWORD: config.REDIS_PASSWORD,
    INSIGHTCORE_ENDPOINT: 'http://your-insightcore-service/telemetry',
    INSIGHTCORE_ENABLED: 'false',
    INSIGHTCORE_API_KEY: '',
    STORAGE_TYPE: 'local',
    AWS_BUCKET_NAME: '',
    AWS_REGION: '',
    AWS_ACCESS_KEY_ID: '',
    AWS_SECRET_ACCESS_KEY: '',
    FRONTEND_URL: 'https://your-domain.com',
    ADMIN_EMAIL: 'admin@your-domain.com',
    ADMIN_PASSWORD: generatePassword(16),
    LOG_LEVEL: 'info'
  };

  const backendEnvContent = Object.entries(backendConfig)
    .map(([key, value]) => `${key}=${value}`)
    .join('\n');

  // Write files
  try {
    fs.writeFileSync('.env.production', rootEnvContent);
    fs.writeFileSync('backend/.env.production', backendEnvContent);
    
    console.log('✅ Configuration files generated successfully!\n');
    console.log('📁 Files created:');
    console.log('  - .env.production (root level)');
    console.log('  - backend/.env.production\n');
    
    console.log('🔑 Generated credentials:');
    console.log(`  MongoDB User: ${config.MONGO_ROOT_USER}`);
    console.log(`  MongoDB Password: ${config.MONGO_ROOT_PASSWORD}`);
    console.log(`  Redis Password: ${config.REDIS_PASSWORD}`);
    console.log(`  Admin Email: ${backendConfig.ADMIN_EMAIL}`);
    console.log(`  Admin Password: ${backendConfig.ADMIN_PASSWORD}\n`);
    
    console.log('⚠️  IMPORTANT SECURITY NOTES:');
    console.log('  1. Change VITE_API_URL to your actual domain');
    console.log('  2. Change FRONTEND_URL to your actual domain');
    console.log('  3. Change ADMIN_EMAIL to your email');
    console.log('  4. Store these credentials securely');
    console.log('  5. Never commit these files to version control');
    console.log('  6. Change admin password after first login\n');
    
  } catch (error) {
    console.error('❌ Error generating configuration:', error.message);
    process.exit(1);
  }
};

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  generateProductionConfig();
}

export default generateProductionConfig;