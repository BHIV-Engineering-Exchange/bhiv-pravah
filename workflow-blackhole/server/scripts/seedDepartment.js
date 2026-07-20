require('dotenv').config();
const mongoose = require('mongoose');
const path = require('path');

// Load app models
const Department = require(path.join(__dirname, '..', 'models', 'Department'));

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/infiverse-bhl';

async function run() {
  try {
    await mongoose.connect(MONGODB_URI, { useNewUrlParser: true, useUnifiedTopology: true });
    console.log('Connected to MongoDB for seeding departments');

    const existing = await Department.findOne({ name: 'Engineering' });
    if (existing) {
      console.log('Department already exists:', existing._id.toString());
      process.exit(0);
    }

    const dept = new Department({
      name: 'Engineering',
      description: 'Engineering Department',
      lead: null,
      members: []
    });

    const saved = await dept.save();
    console.log('Department created:', saved._id.toString());
    process.exit(0);
  } catch (err) {
    console.error('Seeding error:', err);
    process.exit(1);
  }
}

run();
