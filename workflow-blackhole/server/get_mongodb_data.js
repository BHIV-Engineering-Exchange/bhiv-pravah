const mongoose = require('mongoose');
require('dotenv').config();

// Import models
const User = require('./models/User');
const Attendance = require('./models/Attendance');
const Task = require('./models/Task');
const MonitoringAlert = require('./models/MonitoringAlert');

async function getMongoDB Data() {
  try {
    console.log('📊 Connecting to MongoDB...');
    await mongoose.connect(process.env.MONGODB_URI, {
      useNewUrlParser: true,
      useUnifiedTopology: true
    });
    console.log('✅ MongoDB Connected');

    // Get users
    console.log('\n👥 USERS:');
    const users = await User.find().limit(5);
    console.log(JSON.stringify(users, null, 2));

    // Get attendance
    console.log('\n📅 ATTENDANCE (Last 5):');
    const attendance = await Attendance.find().sort({ date: -1 }).limit(5);
    console.log(JSON.stringify(attendance, null, 2));

    // Get tasks
    console.log('\n📋 TASKS (Last 5):');
    const tasks = await Task.find().sort({ createdAt: -1 }).limit(5);
    console.log(JSON.stringify(tasks, null, 2));

    // Get alerts
    console.log('\n🚨 ALERTS (Last 5):');
    const alerts = await MonitoringAlert.find().sort({ timestamp: -1 }).limit(5);
    console.log(JSON.stringify(alerts, null, 2));

    // Get stats
    console.log('\n📊 STATISTICS:');
    const stats = {
      totalUsers: await User.countDocuments(),
      totalAttendance: await Attendance.countDocuments(),
      totalTasks: await Task.countDocuments(),
      totalAlerts: await MonitoringAlert.countDocuments()
    };
    console.log(JSON.stringify(stats, null, 2));

    mongoose.connection.close();
    process.exit(0);
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

getMongoDB Data();
