const mongoose = require('mongoose');
require('dotenv').config();

const User = require('./models/User');
const Attendance = require('./models/Attendance');
const Task = require('./models/Task');
const MonitoringAlert = require('./models/MonitoringAlert');

async function getData() {
  try {
    console.log('📊 Connecting to MongoDB...');
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('✅ MongoDB Connected\n');

    // Stats
    const stats = {
      users: await User.countDocuments(),
      attendance: await Attendance.countDocuments(),
      tasks: await Task.countDocuments(),
      alerts: await MonitoringAlert.countDocuments()
    };
    console.log('📊 DATABASE STATISTICS:');
    console.log(JSON.stringify(stats, null, 2));

    // Users
    console.log('\n👥 SAMPLE USERS (First 3):');
    const users = await User.find().select('name email department role').limit(3);
    console.log(JSON.stringify(users, null, 2));

    // Recent Attendance
    console.log('\n📅 RECENT ATTENDANCE (Last 3):');
    const attendance = await Attendance.find().sort({ date: -1 }).select('user date startTime endTime hoursWorked').limit(3).populate('user', 'name');
    console.log(JSON.stringify(attendance, null, 2));

    // Recent Tasks
    console.log('\n📋 RECENT TASKS (Last 3):');
    const tasks = await Task.find().sort({ createdAt: -1 }).select('title status priority dueDate').limit(3);
    console.log(JSON.stringify(tasks, null, 2));

    // Recent Alerts
    console.log('\n🚨 RECENT ALERTS (Last 3):');
    const alerts = await MonitoringAlert.find().sort({ timestamp: -1 }).select('type severity title resolved').limit(3);
    console.log(JSON.stringify(alerts, null, 2));

    await mongoose.connection.close();
    console.log('\n✅ Done');
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

getData();
