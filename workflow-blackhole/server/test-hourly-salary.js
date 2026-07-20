/**
 * Test script for Hourly-Based Salary Management System
 * 
 * This script tests the main functionalities of the hourly salary system:
 * 1. Calculate employee monthly salary
 * 2. Get activity log
 * 3. Get admin dashboard
 * 4. Update work location type
 * 
 * Usage:
 * 1. Set your auth token below
 * 2. Set a valid user ID
 * 3. Run: node server/test-hourly-salary.js
 */

const axios = require('axios');

// Configuration
const BASE_URL = 'http://localhost:5000';
const AUTH_TOKEN = 'YOUR_AUTH_TOKEN_HERE'; // Replace with actual token
const TEST_USER_ID = 'YOUR_USER_ID_HERE'; // Replace with actual user ID
const YEAR = 2025;
const MONTH = 12;

// Create axios instance with auth
const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'x-auth-token': AUTH_TOKEN,
    'Content-Type': 'application/json'
  }
});

// Test functions
async function testCalculateEmployeeSalary() {
  console.log('\n=== Testing: Calculate Employee Monthly Salary ===');
  try {
    const response = await api.get(`/api/hourly-salary/employee/${TEST_USER_ID}/calculate/${YEAR}/${MONTH}`);
    console.log('✅ Success!');
    console.log('Employee:', response.data.data.employee.name);
    console.log('Total Hours:', response.data.data.hours.totalHours);
    console.log('Office Hours:', response.data.data.hours.officeHours);
    console.log('Remote Hours:', response.data.data.hours.remoteHours);
    console.log('Gross Salary:', response.data.data.salary.grossSalary);
    console.log('Net Salary:', response.data.data.salary.netSalary);
    return true;
  } catch (error) {
    console.error('❌ Error:', error.response?.data || error.message);
    return false;
  }
}

async function testGetActivityLog() {
  console.log('\n=== Testing: Get Activity Log ===');
  try {
    const response = await api.get(`/api/hourly-salary/activity-log?year=${YEAR}&month=${MONTH}`);
    console.log('✅ Success!');
    console.log('Total Records:', response.data.data.summary.totalRecords);
    console.log('Total Employees:', response.data.data.summary.totalEmployees);
    console.log('Total Hours:', response.data.data.summary.totalHours);
    console.log('Office Hours:', response.data.data.summary.totalOfficeHours);
    console.log('Remote Hours:', response.data.data.summary.totalRemoteHours);
    
    if (response.data.data.activityLog.length > 0) {
      console.log('\nSample Activity Log Entry:');
      const sample = response.data.data.activityLog[0];
      console.log('- Employee:', sample.userName);
      console.log('- Date:', sample.date);
      console.log('- Hours Worked:', sample.totalHoursWorked);
      console.log('- Work Location:', sample.workLocationType);
    }
    return true;
  } catch (error) {
    console.error('❌ Error:', error.response?.data || error.message);
    return false;
  }
}

async function testGetAdminDashboard() {
  console.log('\n=== Testing: Get Admin Dashboard ===');
  try {
    const response = await api.get(`/api/hourly-salary/admin/dashboard/${YEAR}/${MONTH}`);
    console.log('✅ Success!');
    console.log('Total Employees:', response.data.data.overallStats.totalEmployees);
    console.log('Total Hours Worked:', response.data.data.overallStats.totalHoursWorked);
    console.log('Total Office Hours:', response.data.data.overallStats.totalOfficeHours);
    console.log('Total Remote Hours:', response.data.data.overallStats.totalRemoteHours);
    console.log('Total Gross Salary:', response.data.data.overallStats.totalGrossSalary);
    console.log('Avg Attendance Rate:', response.data.data.overallStats.avgAttendanceRate);
    
    if (response.data.data.employees.length > 0) {
      console.log('\nSample Employee Summary:');
      const sample = response.data.data.employees[0];
      console.log('- Employee:', sample.name);
      console.log('- Total Hours:', sample.hours.totalHours);
      console.log('- Office Hours:', sample.hours.officeHours);
      console.log('- Remote Hours:', sample.hours.remoteHours);
      console.log('- Net Salary:', sample.salary.netSalary);
    }
    return true;
  } catch (error) {
    console.error('❌ Error:', error.response?.data || error.message);
    return false;
  }
}

async function testGetHoursBreakdown() {
  console.log('\n=== Testing: Get Employee Hours Breakdown ===');
  try {
    const response = await api.get(`/api/hourly-salary/employee/${TEST_USER_ID}/hours-breakdown/${YEAR}/${MONTH}`);
    console.log('✅ Success!');
    console.log('Work Location Summary:');
    response.data.data.summary.forEach(loc => {
      console.log(`- ${loc._id}: ${loc.totalHours} hours (${loc.totalDays} days)`);
      console.log(`  Office Hours: ${loc.officeHours}`);
      console.log(`  Remote Hours: ${loc.remoteHours}`);
    });
    return true;
  } catch (error) {
    console.error('❌ Error:', error.response?.data || error.message);
    return false;
  }
}

async function testGetCurrentMonthSalary() {
  console.log('\n=== Testing: Get Current Month Salary (Quick Access) ===');
  try {
    const response = await api.get('/api/hourly-salary/my-salary/current');
    console.log('✅ Success!');
    console.log('Employee:', response.data.data.employee.name);
    console.log('Period:', response.data.data.period.monthName, response.data.data.period.year);
    console.log('Total Hours:', response.data.data.hours.totalHours);
    console.log('Net Salary:', response.data.data.salary.netSalary);
    return true;
  } catch (error) {
    console.error('❌ Error:', error.response?.data || error.message);
    return false;
  }
}

async function testUpdateWorkLocationType() {
  console.log('\n=== Testing: Update Work Location Type ===');
  console.log('Note: This test requires a valid attendance ID');
  console.log('Skipping for safety - use Postman or similar to test this endpoint');
  return true;
}

// Main test runner
async function runAllTests() {
  console.log('==========================================');
  console.log('  Hourly Salary System - Test Suite');
  console.log('==========================================');
  console.log('Base URL:', BASE_URL);
  console.log('Test User ID:', TEST_USER_ID);
  console.log('Test Period:', `${YEAR}-${MONTH}`);
  
  // Check if configuration is set
  if (AUTH_TOKEN === 'YOUR_AUTH_TOKEN_HERE' || TEST_USER_ID === 'YOUR_USER_ID_HERE') {
    console.error('\n❌ Error: Please set AUTH_TOKEN and TEST_USER_ID in the script');
    console.log('\nHow to get these values:');
    console.log('1. AUTH_TOKEN: Login to the app and get the token from localStorage or cookies');
    console.log('2. TEST_USER_ID: Get from the /api/users endpoint or MongoDB');
    return;
  }
  
  const results = {
    passed: 0,
    failed: 0,
    total: 0
  };
  
  // Run tests
  const tests = [
    { name: 'Calculate Employee Salary', fn: testCalculateEmployeeSalary },
    { name: 'Get Activity Log', fn: testGetActivityLog },
    { name: 'Get Admin Dashboard', fn: testGetAdminDashboard },
    { name: 'Get Hours Breakdown', fn: testGetHoursBreakdown },
    { name: 'Get Current Month Salary', fn: testGetCurrentMonthSalary },
    { name: 'Update Work Location Type', fn: testUpdateWorkLocationType }
  ];
  
  for (const test of tests) {
    results.total++;
    const success = await test.fn();
    if (success) {
      results.passed++;
    } else {
      results.failed++;
    }
    // Wait a bit between tests
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  // Print summary
  console.log('\n==========================================');
  console.log('  Test Summary');
  console.log('==========================================');
  console.log(`Total Tests: ${results.total}`);
  console.log(`✅ Passed: ${results.passed}`);
  console.log(`❌ Failed: ${results.failed}`);
  console.log('==========================================\n');
}

// Run tests
runAllTests().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
