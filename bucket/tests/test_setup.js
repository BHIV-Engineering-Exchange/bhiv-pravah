/**
 * Jest Global Test Setup
 * Initializes test environment and validates prerequisites
 */

const fs = require('fs').promises;
const path = require('path');

module.exports = async () => {
  console.log('🚀 Setting up test environment...');

  // Load environment variables first
  require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

  // Ensure test results directory exists
  const testResultsDir = path.join(__dirname, 'test_results');
  await fs.mkdir(testResultsDir, { recursive: true });

  // Validate environment variables
  const requiredEnvVars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY'];
  const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);

  if (missingVars.length > 0) {
    console.error('❌ Missing required environment variables:');
    missingVars.forEach(varName => console.error(`   - ${varName}`));
    console.error('\nPlease ensure AI_integration/.env contains the required variables.');
    process.exit(1);
  }

  // Validate AI_integration/.env exists
  const envPath = path.join(__dirname, '..', '.env');
  try {
    await fs.access(envPath);
  } catch {
    console.error('❌ AI_integration/.env file not found');
    console.error('Please create the .env file with Supabase credentials.');
    process.exit(1);
  }

  console.log('✅ Test environment setup complete');
  console.log(`📁 Test results will be saved to: ${testResultsDir}`);
};