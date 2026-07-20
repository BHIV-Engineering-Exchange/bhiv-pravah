#!/usr/bin/env node

/**
 * Cleanup Script for Default Aims
 * Removes auto-generated default aims that were created during attendance start
 */

const mongoose = require('mongoose');
const Aim = require('../models/Aim');
require('dotenv').config();

async function cleanupDefaultAims() {
  try {
    console.log('🧹 Starting cleanup of default aims...');
    
    // Connect to MongoDB
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('✅ Connected to MongoDB');

    // Find all default aims
    const defaultAims = await Aim.find({
      aims: 'Daily work objectives - to be updated'
    }).populate('user', 'name email');

    console.log(`📊 Found ${defaultAims.length} default aims to clean up`);

    if (defaultAims.length === 0) {
      console.log('✅ No default aims found. Database is clean!');
      return;
    }

    // Log details of aims to be deleted
    console.log('\n📋 Default aims to be deleted:');
    defaultAims.forEach((aim, index) => {
      console.log(`${index + 1}. User: ${aim.user?.name || 'Unknown'} (${aim.user?.email || 'No email'}) - Date: ${aim.date.toDateString()}`);
    });

    // Delete default aims
    const deleteResult = await Aim.deleteMany({
      aims: 'Daily work objectives - to be updated'
    });

    console.log(`\n✅ Successfully deleted ${deleteResult.deletedCount} default aims`);
    console.log('🎯 Users can now set their own fresh aims without pre-filled content');

  } catch (error) {
    console.error('❌ Error during cleanup:', error);
    throw error;
  } finally {
    // Close database connection
    await mongoose.connection.close();
    console.log('🔌 Database connection closed');
  }
}

// Run the cleanup if this script is executed directly
if (require.main === module) {
  cleanupDefaultAims()
    .then(() => {
      console.log('\n🎉 Cleanup completed successfully!');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n💥 Cleanup failed:', error.message);
      process.exit(1);
    });
}

module.exports = cleanupDefaultAims;