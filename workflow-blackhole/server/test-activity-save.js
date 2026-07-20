require('dotenv').config();
const mongoose = require('mongoose');
const EmployeeActivity = require('./models/EmployeeActivity');

async function testActivitySave() {
  try {
    // Connect to MongoDB
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('✅ Connected to MongoDB');

    // Create test activity
    const testActivity = new EmployeeActivity({
      employee: '679b1743d4f69a1c61c68695', // Replace with actual user ID
      timestamp: new Date(),
      keystroke_count: 150,
      mouse_activity_score: 75,
      idle_duration: 30,
      active_application: {
        name: 'Test Application',
        title: 'Test Window'
      },
      session_id: 'test_session_123',
      work_hours: {
        start: new Date(),
        end: null
      }
    });

    // Calculate productivity score
    testActivity.calculateProductivityScore();

    // Save to database
    await testActivity.save();
    console.log('✅ Test activity saved successfully:', {
      id: testActivity._id,
      keystroke_count: testActivity.keystroke_count,
      mouse_activity_score: testActivity.mouse_activity_score,
      productivity_score: testActivity.productivity_score
    });

    // Verify it was saved
    const savedActivity = await EmployeeActivity.findById(testActivity._id);
    console.log('✅ Activity retrieved from database:', savedActivity ? 'YES' : 'NO');

    // Clean up test data
    await EmployeeActivity.deleteOne({ _id: testActivity._id });
    console.log('✅ Test data cleaned up');

    await mongoose.connection.close();
    console.log('\n✅ Test completed successfully - MongoDB activity storage is working!');
    process.exit(0);

  } catch (error) {
    console.error('❌ Test failed:', error);
    process.exit(1);
  }
}

testActivitySave();
