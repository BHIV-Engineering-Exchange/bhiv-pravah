import dotenv from 'dotenv';
import mongoose from 'mongoose';
import logger from '../src/config/logger.js';

// Import all models to ensure indexes are created
import '../src/models/User.js';
import '../src/models/ChartOfAccounts.js';
import '../src/models/JournalEntry.js';
import '../src/models/AccountBalance.js';
import '../src/models/Invoice.js';
import '../src/models/Expense.js';
import '../src/models/GSTReturn.js';
import '../src/models/TDSEntry.js';
import '../src/models/AuditLog.js';
import '../src/models/RLExperience.js';

dotenv.config();

const createIndexes = async () => {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    logger.info('Database connected');

    // Create indexes for all collections
    const collections = await mongoose.connection.db.listCollections().toArray();

    for (const collection of collections) {
      const collectionName = collection.name;
      logger.info(`Creating indexes for ${collectionName}...`);

      try {
        const model = mongoose.model(
          collectionName.charAt(0).toUpperCase() + collectionName.slice(1, -1)
        );
        await model.createIndexes();
        logger.info(`✓ Indexes created for ${collectionName}`);
      } catch (err) {
        logger.warn(`⚠ Could not create indexes for ${collectionName}: ${err.message}`);
      }
    }

    // Additional compound indexes for performance
    const JournalEntry = mongoose.model('JournalEntry');
    await JournalEntry.collection.createIndex({ status: 1, date: -1 });
    await JournalEntry.collection.createIndex({ 'lines.account': 1, date: -1 });
    logger.info('✓ Additional compound indexes created');

    const Invoice = mongoose.model('Invoice');
    await Invoice.collection.createIndex({ status: 1, dueDate: 1 });
    await Invoice.collection.createIndex({ customerName: 1, invoiceDate: -1 });
    logger.info('✓ Invoice indexes created');

    const Expense = mongoose.model('Expense');
    await Expense.collection.createIndex({ status: 1, date: -1 });
    await Expense.collection.createIndex({ category: 1, date: -1 });
    logger.info('✓ Expense indexes created');

    logger.info('✅ All indexes created successfully!');
    process.exit(0);
  } catch (error) {
    logger.error('Create indexes error:', error);
    process.exit(1);
  }
};

createIndexes();