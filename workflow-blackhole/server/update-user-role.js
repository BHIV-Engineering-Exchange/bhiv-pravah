require('dotenv').config();
const mongoose = require('mongoose');
const User = require('./models/User');

async function updateUserRole() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('Connected to MongoDB');

    // Get user ID from command line argument
    const userId = process.argv[2];
    const newRole = process.argv[3] || 'Manager';

    if (!userId) {
      // List all users if no ID provided
      const users = await User.find({}, 'name email role department').lean();
      console.log('\n📋 All Users:');
      console.log('─'.repeat(80));
      users.forEach(user => {
        console.log(`ID: ${user._id}`);
        console.log(`Name: ${user.name}`);
        console.log(`Email: ${user.email}`);
        console.log(`Role: ${user.role}`);
        console.log(`Department: ${user.department || 'N/A'}`);
        console.log('─'.repeat(80));
      });
      console.log('\nUsage: node update-user-role.js <userId> [role]');
      console.log('Example: node update-user-role.js 681dc4612ae66516796d47da Manager');
      process.exit(0);
    }

    // Update user role
    const user = await User.findByIdAndUpdate(
      userId,
      { role: newRole },
      { new: true }
    );

    if (!user) {
      console.log('❌ User not found');
      process.exit(1);
    }

    console.log('\n✅ User role updated successfully!');
    console.log('─'.repeat(50));
    console.log(`Name: ${user.name}`);
    console.log(`Email: ${user.email}`);
    console.log(`New Role: ${user.role}`);
    console.log('─'.repeat(50));

    process.exit(0);
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

updateUserRole();
