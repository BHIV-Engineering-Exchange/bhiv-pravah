#!/usr/bin/env node
require('dotenv').config();

/**
 * Test Real Activity Tracking
 * 
 * This script tests the REAL activity tracking implementation
 * Run this AFTER starting the Electron agent
 */

const axios = require('axios');

const API_URL = 'http://localhost:5001';
let authToken = '';
let attendanceId = '';

async function testWorkflow() {
  console.log('\n🧪 Testing REAL Activity Tracking Implementation\n');
  console.log('='.repeat(60));

  try {
    // Step 1: Login
    console.log('\n📝 Step 1: Login as employee...');
    const testEmail = process.env.TEST_EMAIL;
    const testPassword = process.env.TEST_PASSWORD;
    
    if (!testEmail || !testPassword) {
      console.error('❌ Error: TEST_EMAIL and TEST_PASSWORD environment variables are required');
      process.exit(1);
    }
    
    const loginResponse = await axios.post(`${API_URL}/api/auth/login`, {
      email: testEmail,
      password: testPassword
    });
    
    authToken = loginResponse.data.token;
    console.log('✅ Login successful');
    console.log('   Token:', authToken.substring(0, 20) + '...');

    // Step 2: Start Day
    console.log('\n📝 Step 2: Starting work day...');
    const startDayResponse = await axios.post(
      `${API_URL}/api/attendance/start`, 
      {
        location: { type: 'office' },
        notes: 'Testing real tracking'
      },
      {
        headers: { 'x-auth-token': authToken }
      }
    );
    
    attendanceId = startDayResponse.data.attendance._id;
    console.log('✅ Day started');
    console.log('   Attendance ID:', attendanceId);
    console.log('   Start Time:', startDayResponse.data.attendance.startTime);

    // Step 3: Check Status (Electron polls this)
    console.log('\n📝 Step 3: Checking attendance status (Electron polling simulation)...');
    const statusResponse = await axios.get(
      `${API_URL}/api/attendance/status`,
      {
        headers: { 'x-auth-token': authToken }
      }
    );
    
    console.log('✅ Status retrieved');
    console.log('   Day Started:', statusResponse.data.dayStarted);
    console.log('   Attendance ID:', statusResponse.data.attendanceId);

    // Step 4: Wait for Electron to send activity
    console.log('\n📝 Step 4: Waiting for Electron agent to send activity data...');
    console.log('⏳ Make sure Electron agent is running!');
    console.log('⏳ The agent should detect dayStarted=true and start tracking');
    console.log('⏳ Move your mouse and type to generate activity');
    console.log('⏳ Activity data will be sent every 30 seconds');
    
    // Give user time to interact
    await new Promise(resolve => {
      let countdown = 35;
      const timer = setInterval(() => {
        process.stdout.write(`\r   Waiting ${countdown}s for activity data... `);
        countdown--;
        if (countdown < 0) {
          clearInterval(timer);
          console.log('\n');
          resolve();
        }
      }, 1000);
    });

    // Step 5: Check if activity was recorded
    console.log('\n📝 Step 5: Checking if activity was recorded in database...');
    const Activity = require('./server/models/EmployeeActivity');
    const activities = await Activity.find({ attendanceId }).sort({ timestamp: -1 }).limit(1);
    
    if (activities.length > 0) {
      const activity = activities[0];
      console.log('✅ Activity data found!');
      console.log('   Timestamp:', activity.timestamp);
      console.log('   Mouse Events:', activity.stats.mouseEvents);
      console.log('   Keyboard Events:', activity.stats.keyboardEvents);
      console.log('   Idle Seconds:', activity.stats.idleSeconds);
      console.log('   Productive %:', activity.stats.productivePercentage);
      console.log('   Tracking Mode:', activity.stats.trackingMode);
      
      // Verify it's NOT simulated
      if (activity.stats.trackingMode === 'ELECTRON_NATIVE') {
        console.log('\n🎉 SUCCESS: Real tracking is working!');
        console.log('   ✅ Using Electron native APIs');
        console.log('   ✅ NO simulation or mock data');
      } else {
        console.log('\n⚠️  WARNING: Unexpected tracking mode:', activity.stats.trackingMode);
      }
      
      // Check for realistic values
      if (activity.stats.mouseEvents === 0 && activity.stats.keyboardEvents === 0) {
        console.log('\n⚠️  INFO: No activity detected - did you move mouse/type?');
      }
    } else {
      console.log('❌ No activity data found');
      console.log('   Possible reasons:');
      console.log('   1. Electron agent not running');
      console.log('   2. Electron hasn\'t sent data yet (waits 30s)');
      console.log('   3. Network error between Electron and backend');
    }

    // Step 6: End Day
    console.log('\n📝 Step 6: Ending work day...');
    await axios.post(
      `${API_URL}/api/attendance/end`,
      {},
      {
        headers: { 'x-auth-token': authToken }
      }
    );
    console.log('✅ Day ended');

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    if (error.response) {
      console.error('   Status:', error.response.status);
      console.error('   Data:', error.response.data);
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log('\n✅ Test workflow complete\n');
}

// Run test
testWorkflow().catch(console.error);
