/**
 * Migration Script: Add Employee Fields to Users
 * 
 * This script adds employeeId and hourlyRate fields to existing User records
 * Run this once after implementing the salary management system
 * 
 * Usage: node scripts/add-employee-fields.js
 */

const mongoose = require('mongoose');
require('dotenv').config();

const User = require('../models/User');

// Configuration
const DEFAULT_HOURLY_RATE = 25; // Default hourly rate in USD
const EMPLOYEE_ID_PREFIX = 'EMP'; // Prefix for auto-generated employee IDs

/**
 * Generate employee ID from user index
 */
const generateEmployeeId = (index) => {
  return `${EMPLOYEE_ID_PREFIX}${String(index).padStart(4, '0')}`;
};

/**
 * Determine hourly rate based on user role
 */
const getHourlyRateByRole = (role) => {
  const rateMap = {
    'Admin': 50,
    'Manager': 40,
    'User': 25,
    'Procurement Agent': 30
  };
  return rateMap[role] || DEFAULT_HOURLY_RATE;
};

/**
 * Main migration function
 */
const migrateUsers = async () => {
  try {
    console.log('🔄 Starting migration...\n');
    
    // Connect to MongoDB
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('✅ Connected to MongoDB\n');
    
    // Find all active users without employeeId
    const users = await User.find({
      stillExist: 1,
      employeeId: { $exists: false }
    }).sort({ createdAt: 1 });
    
    console.log(`📊 Found ${users.length} users to update\n`);
    
    if (users.length === 0) {
      console.log('ℹ️  No users need updating. All users already have employeeId.');
      process.exit(0);
    }
    
    // Track statistics
    let updated = 0;
    let errors = 0;
    
    // Get the starting index for employee IDs
    const existingEmployeeIds = await User.find({ 
      employeeId: { $exists: true } 
    }).select('employeeId');
    
    const maxId = existingEmployeeIds.reduce((max, user) => {
      const num = parseInt(user.employeeId.replace(EMPLOYEE_ID_PREFIX, ''));
      return num > max ? num : max;
    }, 0);
    
    let nextId = maxId + 1;
    
    console.log('🚀 Processing users...\n');
    
    // Update each user
    for (const user of users) {
      try {
        const employeeId = generateEmployeeId(nextId);
        const hourlyRate = getHourlyRateByRole(user.role);
        
        user.employeeId = employeeId;
        user.hourlyRate = hourlyRate;
        
        await user.save();
        
        console.log(`✅ Updated: ${user.name} (${user.email})`);
        console.log(`   Employee ID: ${employeeId}`);
        console.log(`   Hourly Rate: $${hourlyRate}/hour`);
        console.log(`   Role: ${user.role}\n`);
        
        updated++;
        nextId++;
      } catch (error) {
        console.error(`❌ Error updating ${user.email}:`, error.message, '\n');
        errors++;
      }
    }
    
    // Summary
    console.log('━'.repeat(50));
    console.log('📈 Migration Summary:');
    console.log(`   Total users processed: ${users.length}`);
    console.log(`   Successfully updated: ${updated}`);
    console.log(`   Errors: ${errors}`);
    console.log('━'.repeat(50));
    
    if (updated > 0) {
      console.log('\n✅ Migration completed successfully!');
      console.log('\nNext steps:');
      console.log('1. Review the updated user records in your database');
      console.log('2. Adjust hourly rates as needed for specific employees');
      console.log('3. Start using the Biometric Salary Management system');
    }
    
  } catch (error) {
    console.error('❌ Migration failed:', error);
    process.exit(1);
  } finally {
    // Disconnect from MongoDB
    await mongoose.disconnect();
    console.log('\n🔌 Disconnected from MongoDB');
  }
};

/**
 * Alternative: Update specific users with custom rates
 * Uncomment and modify as needed
 */
const updateSpecificUsers = async () => {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    
    // Example: Update specific users
    const updates = [
      { email: 'john.doe@example.com', employeeId: 'EMP0001', hourlyRate: 45 },
      { email: 'jane.smith@example.com', employeeId: 'EMP0002', hourlyRate: 40 },
      // Add more users as needed
    ];
    
    for (const update of updates) {
      await User.findOneAndUpdate(
        { email: update.email },
        { 
          employeeId: update.employeeId,
          hourlyRate: update.hourlyRate
        },
        { new: true }
      );
      console.log(`✅ Updated ${update.email}`);
    }
    
    await mongoose.disconnect();
  } catch (error) {
    console.error('Error:', error);
  }
};

// Run migration
if (require.main === module) {
  migrateUsers();
  
  // Or run specific updates:
  // updateSpecificUsers();
}

module.exports = { migrateUsers, updateSpecificUsers };
