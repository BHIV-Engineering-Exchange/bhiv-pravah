const mongoose = require('mongoose');
require('dotenv').config();

mongoose.connect(process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/workflow')
  .then(async () => {
    const EmployeeActivity = require('./models/EmployeeActivity');
    const Attendance = require('./models/Attendance');
    
    const userId = '681dc8122ae66516796d4854';
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    console.log('='.repeat(60));
    console.log('Checking user:', userId, '(vinayak tiwari)');
    console.log('Date range:', today.toISOString(), 'to', tomorrow.toISOString());
    console.log('='.repeat(60));
    
    const todayActivity = await EmployeeActivity.find({
      employee: userId,
      timestamp: { $gte: today, $lt: tomorrow }
    }).sort({ timestamp: -1 });
    
    console.log('\n📊 TODAY activity records:', todayActivity.length);
    if (todayActivity.length > 0) {
      console.log('Latest 3 records:');
      todayActivity.slice(0, 3).forEach(act => {
        console.log('  -', act.timestamp.toISOString(), '| Mouse:', act.mouseEvents, '| Keyboard:', act.keyboardEvents);
      });
    }
    
    const attendance = await Attendance.findOne({
      user: userId,
      date: { $gte: today, $lt: tomorrow }
    });
    
    console.log('\n✅ TODAY attendance:');
    if (attendance) {
      console.log('  ID:', attendance._id);
      console.log('  Day started:', !!attendance.startDayTime, '| Time:', attendance.startDayTime);
      console.log('  Day ended:', !!attendance.endDayTime, '| Time:', attendance.endDayTime);
    } else {
      console.log('  ❌ NO ATTENDANCE RECORD FOR TODAY');
    }
    
    process.exit(0);
  })
  .catch(err => {
    console.error('Error:', err);
    process.exit(1);
  });
