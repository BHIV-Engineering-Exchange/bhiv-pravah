const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const crypto = require('crypto');
require('dotenv').config();

// Generate secure random password
function generatePassword() {
  return crypto.randomBytes(12).toString('base64').replace(/[^a-zA-Z0-9]/g, '').slice(0, 16);
}

async function createTestUser() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    const User = require('./models/User');
    
    const testPassword = process.env.TEST_USER_PASSWORD || generatePassword();
    const hashedPassword = await bcrypt.hash(testPassword, 10);
    
    let testUser = await User.findOne({ email: 'testuser@blackhole.com' });
    
    if (testUser) {
      testUser.password = hashedPassword;
      await testUser.save();
      console.log('✅ Updated existing test user\n');
    } else {
      testUser = new User({
        name: 'Test User',
        email: 'testuser@blackhole.com',
        password: hashedPassword,
        role: 'User'
      });
      await testUser.save();
      console.log('✅ Created new test user\n');
    }
    
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📋 TEST USER CREDENTIALS');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`Email:    testuser@blackhole.com`);
    console.log(`Password: ${testPassword}`);
    console.log(`User ID:  ${testUser._id}`);
    console.log(`Role:     ${testUser.role}`);
    console.log('⚠️  Save this password securely!');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
    
    await mongoose.connection.close();
    process.exit(0);
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

createTestUser();
