import mongoose from 'mongoose';
import dotenv from 'dotenv';
import fs from 'fs/promises';
import path from 'path';

dotenv.config();

const backupDatabase = async () => {
  try {
    console.log('🔄 Starting database backup...\n');

    await mongoose.connect(process.env.MONGODB_URI);
    console.log('✅ Connected to MongoDB\n');

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupDir = path.join(process.cwd(), 'backups', timestamp);
    await fs.mkdir(backupDir, { recursive: true });

    const collections = [
      'users',
      'chartofaccounts',
      'journalentries',
      'invoices',
      'expenses',
      'accountbalances',
      'companysettings',
      'gstreturns',
      'tdsentries',
      'auditlogs'
    ];

    console.log('📦 Backing up collections...\n');

    for (const collectionName of collections) {
      try {
        const collection = mongoose.connection.collection(collectionName);
        const data = await collection.find({}).toArray();
        
        if (data.length > 0) {
          const filePath = path.join(backupDir, `${collectionName}.json`);
          await fs.writeFile(filePath, JSON.stringify(data, null, 2));
          console.log(`✅ ${collectionName}: ${data.length} documents`);
        } else {
          console.log(`ℹ️  ${collectionName}: empty`);
        }
      } catch (error) {
        console.log(`⚠️  ${collectionName}: not found`);
      }
    }

    console.log(`\n✅ Backup completed: ${backupDir}\n`);

  } catch (error) {
    console.error('❌ Backup failed:', error);
    process.exit(1);
  } finally {
    await mongoose.connection.close();
    process.exit(0);
  }
};

backupDatabase();
