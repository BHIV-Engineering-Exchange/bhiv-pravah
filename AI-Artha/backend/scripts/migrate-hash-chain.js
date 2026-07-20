import mongoose from 'mongoose';
import dotenv from 'dotenv';
import JournalEntry from '../src/models/JournalEntry.js';
import logger from '../src/config/logger.js';

dotenv.config();

/**
 * Migration script to update existing journal entries with enhanced hash-chain fields
 */
async function migrateHashChain() {
  try {
    // Connect to database
    await mongoose.connect(process.env.MONGODB_URI);
    logger.info('Connected to MongoDB');

    // Get all posted entries sorted by creation date
    const entries = await JournalEntry.find({ status: 'posted' }).sort({ createdAt: 1 });

    logger.info(`Found ${entries.length} posted entries to migrate`);

    let prevHash = '0';
    let position = 0;

    for (const entry of entries) {
      // Set chain position
      entry.chainPosition = position;
      
      // Set prevHash (use existing prev_hash if available)
      entry.prevHash = entry.prev_hash || prevHash;
      
      // Compute and set hash
      const computedHash = JournalEntry.computeHash(entry.toObject(), entry.prevHash);
      entry.hash = computedHash;
      
      // Update legacy fields for backward compatibility
      entry.prev_hash = entry.prevHash;
      entry.immutable_hash = entry.hash;
      entry.immutable_chain_valid = true;
      entry.hashTimestamp = entry.postedAt || entry.createdAt;

      // Save without triggering pre-save hook
      await JournalEntry.updateOne(
        { _id: entry._id },
        {
          $set: {
            chainPosition: entry.chainPosition,
            prevHash: entry.prevHash,
            hash: entry.hash,
            prev_hash: entry.prevHash,
            immutable_hash: entry.hash,
            immutable_chain_valid: true,
            hashTimestamp: entry.hashTimestamp,
          }
        }
      );

      logger.info(`Migrated entry ${entry.entryNumber} at position ${position}`);

      prevHash = entry.hash;
      position++;
    }

    // Verify the chain after migration
    logger.info('Verifying migrated chain...');
    
    const verificationErrors = [];
    prevHash = '0';
    
    const verifyEntries = await JournalEntry.find({ status: 'posted' }).sort({ chainPosition: 1 });
    
    for (const entry of verifyEntries) {
      if (entry.prevHash !== prevHash) {
        verificationErrors.push({
          entryNumber: entry.entryNumber,
          position: entry.chainPosition,
          error: 'Chain broken',
          expected: prevHash,
          actual: entry.prevHash,
        });
      }
      
      const computedHash = JournalEntry.computeHash(entry.toObject(), entry.prevHash);
      if (entry.hash !== computedHash) {
        verificationErrors.push({
          entryNumber: entry.entryNumber,
          position: entry.chainPosition,
          error: 'Hash mismatch',
          expected: computedHash,
          actual: entry.hash,
        });
      }
      
      prevHash = entry.hash;
    }

    if (verificationErrors.length === 0) {
      logger.info('✅ Chain verification successful! All entries are valid.');
    } else {
      logger.error('❌ Chain verification failed:');
      verificationErrors.forEach(err => logger.error(JSON.stringify(err)));
    }

    logger.info(`Migration completed: ${entries.length} entries processed`);
    
    // Update draft entries with chainPosition
    const draftEntries = await JournalEntry.find({ status: 'draft' });
    for (const entry of draftEntries) {
      entry.chainPosition = position;
      entry.prevHash = prevHash;
      entry.prev_hash = prevHash;
      
      await JournalEntry.updateOne(
        { _id: entry._id },
        {
          $set: {
            chainPosition: entry.chainPosition,
            prevHash: entry.prevHash,
            prev_hash: entry.prevHash,
          }
        }
      );
      
      position++;
    }
    
    logger.info(`Updated ${draftEntries.length} draft entries`);

  } catch (error) {
    logger.error('Migration error:', error);
    throw error;
  } finally {
    await mongoose.connection.close();
    logger.info('Database connection closed');
  }
}

// Run migration
migrateHashChain()
  .then(() => {
    console.log('Migration completed successfully');
    process.exit(0);
  })
  .catch((error) => {
    console.error('Migration failed:', error);
    process.exit(1);
  });
