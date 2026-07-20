// index.js - Storage factory for creating storage instances
const LocalStorage = require('./LocalStorage');
const MongoStorage = require('./MongoStorage');

function createStorage() {
  const provider = process.env.STORAGE_PROVIDER || 'local';
  
  console.log(`[STORAGE] Initializing storage provider: ${provider}`);
  
  switch (provider.toLowerCase()) {
    case 'mongodb':
    case 'mongo':
      return new MongoStorage();
      
    case 's3':
    case 'aws':
      try {
        const S3Storage = require('./S3Storage');
        return new S3Storage();
      } catch (error) {
        console.error('[STORAGE] S3 not available. Install @aws-sdk/client-s3 first.');
        console.error('[STORAGE] Run: npm install @aws-sdk/client-s3');
        throw error;
      }
      
    case 'local':
    case 'filesystem':
    default:
      return new LocalStorage();
  }
}

module.exports = { 
  createStorage,
  LocalStorage,
  MongoStorage
};
