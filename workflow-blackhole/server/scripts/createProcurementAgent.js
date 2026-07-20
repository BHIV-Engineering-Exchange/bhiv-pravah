require('dotenv').config();
const mongoose = require('mongoose');
const User = require('../models/User');

async function createProcurementAgent() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('Connected to MongoDB');

    // Check if procurement agent already exists
    const procurementEmailCheck = process.env.PROCUREMENT_EMAIL || 'procurement@infiverse.test';
    const existingAgent = await User.findOne({ email: procurementEmailCheck });
    if (existingAgent) {
      console.log('Procurement agent already exists:', existingAgent.name);
      process.exit(0);
    }

    const procurementPassword = process.env.PROCUREMENT_PASSWORD;
    const procurementEmail = process.env.PROCUREMENT_EMAIL || 'procurement@infiverse.test';
    
    if (!procurementPassword) {
      console.error('Error: PROCUREMENT_PASSWORD environment variable is required');
      process.exit(1);
    }

    // Create procurement agent
    const procurementAgent = new User({
      name: 'Procurement Agent',
      email: procurementEmail,
      password: procurementPassword,
      role: 'Procurement Agent'
    });

    await procurementAgent.save();
    console.log('✅ Procurement agent created successfully!');
    console.log('Email:', procurementEmail);
    console.log('Role: Procurement Agent');

    process.exit(0);
  } catch (error) {
    console.error('Error creating procurement agent:', error);
    process.exit(1);
  }
}

createProcurementAgent();