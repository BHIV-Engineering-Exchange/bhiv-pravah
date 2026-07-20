const mongoose = require('mongoose');
require('dotenv').config();

mongoose.connect(process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/workflow')
  .then(async () => {
    const EmployeeActivity = require('./models/EmployeeActivity');
    
    const userId = '681dc8122ae66516796d4854';
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    const records = await EmployeeActivity.find({
      employee: userId,
      timestamp: { $gte: today, $lt: tomorrow }
    }).sort({ timestamp: -1 }).limit(5).lean();
    
    console.log('📊 Latest', records.length, 'activity records:\n');
    records.forEach(r => {
      console.log('Time:', r.timestamp);
      console.log('  Mouse:', r.mouseEvents || r.mouse_activity_score || 'N/A');
      console.log('  Keyboard:', r.keyboardEvents || r.keystroke_count || 'N/A');
      console.log('  Idle:', r.idle_duration || r.idleSeconds || 0, 'seconds');
      console.log('  Productivity:', r.productivityScore || 'N/A');
      console.log('---');
    });
    
    process.exit(0);
  })
  .catch(err => {
    console.error('Error:', err);
    process.exit(1);
  });
