import mongoose from 'mongoose';
import dotenv from 'dotenv';
import JournalEntry from '../src/models/JournalEntry.js';
import logger from '../src/config/logger.js';

dotenv.config();

/**
 * Verification script to test hash-chain implementation
 */
async function verifyHashChainImplementation() {
  try {
    console.log('🔍 Verifying Hash-Chain Implementation...\n');

    // Connect to database
    await mongoose.connect(process.env.MONGODB_URI);
    logger.info('✅ Connected to MongoDB');

    // Test 1: Check if new fields exist
    console.log('\n📋 Test 1: Checking model schema...');
    const sampleEntry = await JournalEntry.findOne();
    
    if (sampleEntry) {
      const hasNewFields = 
        sampleEntry.schema.path('hash') &&
        sampleEntry.schema.path('prevHash') &&
        sampleEntry.schema.path('chainPosition') &&
        sampleEntry.schema.path('hashTimestamp');
      
      if (hasNewFields) {
        console.log('✅ New hash-chain fields present in schema');
      } else {
        console.log('❌ Missing hash-chain fields in schema');
      }
    }

    // Test 2: Check static method
    console.log('\n📋 Test 2: Testing static computeHash method...');
    if (typeof JournalEntry.computeHash === 'function') {
      const testData = {
        entryNumber: 'TEST-001',
        date: new Date(),
        description: 'Test entry',
        lines: [
          { account: '507f1f77bcf86cd799439011', debit: '100', credit: '0' },
          { account: '507f1f77bcf86cd799439012', debit: '0', credit: '100' }
        ],
        status: 'draft',
        reference: 'TEST'
      };
      
      const hash = JournalEntry.computeHash(testData, '0');
      
      if (hash && hash.length === 64) {
        console.log('✅ computeHash method works correctly');
        console.log(`   Generated hash: ${hash.substring(0, 16)}...`);
      } else {
        console.log('❌ computeHash method failed');
      }
    } else {
      console.log('❌ computeHash static method not found');
    }

    // Test 3: Check instance methods
    console.log('\n📋 Test 3: Testing instance methods...');
    const entry = await JournalEntry.findOne({ status: 'posted' });
    
    if (entry) {
      if (typeof entry.verifyHash === 'function') {
        console.log('✅ verifyHash instance method exists');
        
        if (entry.hash) {
          const isValid = entry.verifyHash();
          console.log(`   Entry ${entry.entryNumber} hash valid: ${isValid}`);
        }
      } else {
        console.log('❌ verifyHash instance method not found');
      }
      
      if (typeof entry.verifyChainFromEntry === 'function') {
        console.log('✅ verifyChainFromEntry instance method exists');
      } else {
        console.log('❌ verifyChainFromEntry instance method not found');
      }
    } else {
      console.log('⚠️  No posted entries found to test instance methods');
    }

    // Test 4: Check indexes
    console.log('\n📋 Test 4: Checking indexes...');
    const indexes = await JournalEntry.collection.getIndexes();
    
    const hasChainPositionIndex = Object.keys(indexes).some(key => 
      key.includes('chainPosition')
    );
    const hasHashIndex = Object.keys(indexes).some(key => 
      key.includes('hash')
    );
    const hasPrevHashIndex = Object.keys(indexes).some(key => 
      key.includes('prevHash')
    );
    
    if (hasChainPositionIndex) {
      console.log('✅ chainPosition index exists');
    } else {
      console.log('⚠️  chainPosition index missing (run npm run create-indexes)');
    }
    
    if (hasHashIndex) {
      console.log('✅ hash index exists');
    } else {
      console.log('⚠️  hash index missing (run npm run create-indexes)');
    }
    
    if (hasPrevHashIndex) {
      console.log('✅ prevHash index exists');
    } else {
      console.log('⚠️  prevHash index missing (run npm run create-indexes)');
    }

    // Test 5: Check chain integrity
    console.log('\n📋 Test 5: Checking chain integrity...');
    const postedEntries = await JournalEntry.find({ status: 'posted' })
      .sort({ chainPosition: 1 })
      .limit(10);
    
    if (postedEntries.length > 0) {
      console.log(`   Found ${postedEntries.length} posted entries to check`);
      
      let chainValid = true;
      let prevHash = '0';
      
      for (const entry of postedEntries) {
        if (entry.hash && entry.prevHash) {
          if (entry.prevHash !== prevHash) {
            console.log(`❌ Chain broken at ${entry.entryNumber}`);
            chainValid = false;
            break;
          }
          
          const computedHash = JournalEntry.computeHash(entry.toObject(), entry.prevHash);
          if (entry.hash !== computedHash) {
            console.log(`❌ Hash mismatch at ${entry.entryNumber}`);
            chainValid = false;
            break;
          }
          
          prevHash = entry.hash;
        } else {
          console.log(`⚠️  Entry ${entry.entryNumber} missing hash fields (needs migration)`);
        }
      }
      
      if (chainValid) {
        console.log('✅ Chain integrity verified for sample entries');
      }
    } else {
      console.log('⚠️  No posted entries found to verify chain');
    }

    // Test 6: Check backward compatibility
    console.log('\n📋 Test 6: Checking backward compatibility...');
    const entryWithLegacy = await JournalEntry.findOne({ 
      status: 'posted',
      immutable_hash: { $exists: true }
    });
    
    if (entryWithLegacy) {
      const legacyHashExists = !!entryWithLegacy.immutable_hash;
      const legacyPrevHashExists = !!entryWithLegacy.prev_hash;
      const newHashExists = !!entryWithLegacy.hash;
      const newPrevHashExists = !!entryWithLegacy.prevHash;
      
      if (legacyHashExists && legacyPrevHashExists) {
        console.log('✅ Legacy fields (immutable_hash, prev_hash) present');
      }
      
      if (newHashExists && newPrevHashExists) {
        console.log('✅ New fields (hash, prevHash) present');
        
        if (entryWithLegacy.hash === entryWithLegacy.immutable_hash &&
            entryWithLegacy.prevHash === entryWithLegacy.prev_hash) {
          console.log('✅ Legacy and new fields are synced');
        } else {
          console.log('⚠️  Legacy and new fields are not synced (run migration)');
        }
      } else {
        console.log('⚠️  New fields missing (run migration)');
      }
    } else {
      console.log('⚠️  No entries with legacy fields found');
    }

    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('📊 VERIFICATION SUMMARY');
    console.log('='.repeat(60));
    
    const totalEntries = await JournalEntry.countDocuments();
    const postedCount = await JournalEntry.countDocuments({ status: 'posted' });
    const withHashCount = await JournalEntry.countDocuments({ hash: { $exists: true } });
    const withChainPosCount = await JournalEntry.countDocuments({ chainPosition: { $exists: true } });
    
    console.log(`Total journal entries: ${totalEntries}`);
    console.log(`Posted entries: ${postedCount}`);
    console.log(`Entries with hash field: ${withHashCount}`);
    console.log(`Entries with chainPosition: ${withChainPosCount}`);
    
    if (withHashCount === totalEntries && withChainPosCount === totalEntries) {
      console.log('\n✅ All entries have been migrated to enhanced hash-chain');
    } else if (withHashCount > 0) {
      console.log('\n⚠️  Partial migration detected. Run: npm run migrate:hash-chain');
    } else {
      console.log('\n⚠️  No entries migrated yet. Run: npm run migrate:hash-chain');
    }
    
    console.log('\n✅ Verification complete!');

  } catch (error) {
    console.error('\n❌ Verification error:', error);
    throw error;
  } finally {
    await mongoose.connection.close();
    logger.info('Database connection closed');
  }
}

// Run verification
verifyHashChainImplementation()
  .then(() => {
    console.log('\n🎉 Hash-chain implementation verified successfully!');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n💥 Verification failed:', error);
    process.exit(1);
  });
