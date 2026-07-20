require('dotenv').config();
const mongoose = require('mongoose');
const path = require('path');

const User = require(path.join(__dirname, '..', 'models', 'User'));
const Department = require(path.join(__dirname, '..', 'models', 'Department'));

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/infiverse-bhl';

async function run() {
  try {
    await mongoose.connect(MONGODB_URI, { useNewUrlParser: true, useUnifiedTopology: true });
    console.log('Connected to MongoDB for seeding admin');

    const adminEmail = 'admin.local@infiverse.test';
    let admin = await User.findOne({ email: adminEmail });
    if (admin) {
      console.log('Admin user already exists:', admin._id.toString());
      process.exit(0);
    }

    // pick an existing department if any
    const dept = await Department.findOne();

    const adminPassword = process.env.ADMIN_PASSWORD;
    if (!adminPassword) {
      console.error('Error: ADMIN_PASSWORD environment variable is required');
      process.exit(1);
    }

    const newUser = new User({
      name: 'Local Admin',
      email: adminEmail,
      password: adminPassword,
      role: 'Admin',
      department: dept ? dept._id : undefined,
      stillExist: 1,
    });

    const saved = await newUser.save();
    console.log('Admin user created:', saved._id.toString(), 'email:', adminEmail);
    process.exit(0);
  } catch (err) {
    console.error('Seeding admin error:', err);
    process.exit(1);
  }
}

run();
