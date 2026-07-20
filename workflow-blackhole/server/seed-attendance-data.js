const mongoose = require('mongoose');
const DailyAttendance = require('./models/DailyAttendance');
const User = require('./models/User');
const Aim = require('./models/Aim');

// Connect to MongoDB
mongoose.connect('mongodb://localhost:27017/workflow-blackhole', {
  useNewUrlParser: true,
  useUnifiedTopology: true
})
.then(() => console.log('✅ Connected to MongoDB'))
.catch(err => console.error('❌ MongoDB connection error:', err));

const seedAttendanceData = async () => {
  try {
    console.log('🌱 Starting to seed attendance data...');

    // Get all users
    const users = await User.find({ stillExist: 1 }).limit(10);
    
    if (users.length === 0) {
      console.log('❌ No users found in database. Please create users first.');
      process.exit(1);
    }

    console.log(`📊 Found ${users.length} users`);

    // Clear existing attendance data
    await DailyAttendance.deleteMany({});
    await Aim.deleteMany({});
    console.log('🗑️  Cleared existing attendance data');

    const attendanceRecords = [];
    const aimRecords = [];

    // Create 30 days of historical data for each user
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (const user of users) {
      console.log(`\n👤 Creating data for ${user.name}...`);

      for (let i = 0; i < 30; i++) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);

        // 80% attendance rate
        const isPresent = Math.random() > 0.2;

        if (isPresent) {
          // Random start time between 9 AM and 11 AM
          const startHour = 9 + Math.floor(Math.random() * 2);
          const startMinute = Math.floor(Math.random() * 60);
          const startDayTime = new Date(date);
          startDayTime.setHours(startHour, startMinute, 0, 0);

          // Random work duration between 7 and 10 hours
          const workHours = 7 + Math.random() * 3;
          const endDayTime = new Date(startDayTime);
          endDayTime.setHours(endDayTime.getHours() + workHours);

          const totalHoursWorked = workHours;
          const regularHours = Math.min(8, workHours);
          const overtimeHours = Math.max(0, workHours - 8);

          const dailyWage = 258;
          const earnedAmount = (totalHoursWorked / 8) * dailyWage + 
                              (overtimeHours * (dailyWage / 8) * 1.5);

          // Create attendance record
          const attendance = {
            user: user._id,
            date: date,
            startDayTime: startDayTime,
            endDayTime: endDayTime,
            totalHoursWorked: Math.round(totalHoursWorked * 100) / 100,
            regularHours: Math.round(regularHours * 100) / 100,
            overtimeHours: Math.round(overtimeHours * 100) / 100,
            status: totalHoursWorked >= 8 ? 'Present' : totalHoursWorked >= 4 ? 'Half Day' : 'Present',
            workLocationType: Math.random() > 0.3 ? 'Office' : 'Home',
            startDayLocation: {
              latitude: 19.1663 + (Math.random() - 0.5) * 0.01,
              longitude: 72.8526 + (Math.random() - 0.5) * 0.01,
              address: 'Blackhole Infiverse, Goregaon West, Mumbai',
              accuracy: 10 + Math.random() * 20
            },
            earnedAmount: Math.round(earnedAmount * 100) / 100,
            dailyWage: dailyWage,
            isVerified: true,
            approvalStatus: 'Auto-Approved',
            source: Math.random() > 0.5 ? 'StartDay' : 'Biometric',
            verificationMethod: 'StartDay'
          };

          attendanceRecords.push(attendance);

          // Create corresponding AIM
          const completionStatuses = ['Completed', 'MVP Achieved', 'Completed'];
          const aim = {
            user: user._id,
            date: date,
            aims: `Daily work objectives for ${date.toDateString()} - ${Math.random() > 0.5 ? 'Complete feature implementation' : 'Bug fixes and testing'}`,
            completionStatus: completionStatuses[Math.floor(Math.random() * completionStatuses.length)],
            progressPercentage: 80 + Math.floor(Math.random() * 20),
            completionComment: `Successfully completed tasks. ${Math.random() > 0.5 ? 'Delivered on time.' : 'Excellent progress made.'}`,
            workLocation: attendance.workLocationType,
            workSessionInfo: {
              startDayTime: startDayTime,
              endDayTime: endDayTime
            }
          };

          aimRecords.push(aim);
        }
      }
    }

    // Insert all records
    console.log(`\n💾 Inserting ${attendanceRecords.length} attendance records...`);
    await DailyAttendance.insertMany(attendanceRecords);
    
    console.log(`💾 Inserting ${aimRecords.length} AIMS records...`);
    await Aim.insertMany(aimRecords);

    console.log('\n✅ Successfully seeded attendance data!');
    console.log(`   - ${attendanceRecords.length} attendance records created`);
    console.log(`   - ${aimRecords.length} AIMS records created`);
    console.log(`   - Data for ${users.length} users`);
    console.log(`   - 30 days of historical data\n`);

    process.exit(0);
  } catch (error) {
    console.error('❌ Error seeding data:', error);
    process.exit(1);
  }
};

// Run the seed function
seedAttendanceData();
