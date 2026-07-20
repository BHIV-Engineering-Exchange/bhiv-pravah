require('dotenv').config();
const mongoose = require('mongoose');
const User = require('./models/User');

async function testLogin() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('Connected to MongoDB');

    // List all users
    const users = await User.find({}, 'name email role');
    console.log('\n=== Available Users ===');
    users.forEach(user => {
      console.log(`Name: ${user.name}`);
      console.log(`Email: ${user.email}`);
      console.log(`Role: ${user.role}`);
      console.log('---');
    });

    // Test admin login
    const adminEmail = process.env.ADMIN_EMAIL || 'admin.local@infiverse.test';
    
    const admin = await User.findOne({ email: adminEmail });
    if (admin) {
      console.log(`\n=== Admin User Found ===`);
      console.log(`Name: ${admin.name}`);
      console.log(`Email: ${admin.email}`);
      console.log(`Role: ${admin.role}`);
    } else {
      console.log('\n❌ Admin user not found');
    }

    // Test procurement agent login
    const procurementEmail = process.env.PROCUREMENT_EMAIL || 'procurement@infiverse.test';
    
    const procurementAgent = await User.findOne({ email: procurementEmail });
    if (procurementAgent) {
      console.log(`\n=== Procurement Agent Found ===`);
      console.log(`Name: ${procurementAgent.name}`);
      console.log(`Email: ${procurementAgent.email}`);
      console.log(`Role: ${procurementAgent.role}`);
    } else {
      console.log('\n❌ Procurement agent not found');
    }

    process.exit(0);
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

testLogin();