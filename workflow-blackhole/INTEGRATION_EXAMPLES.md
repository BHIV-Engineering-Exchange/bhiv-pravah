/**
 * INTEGRATION EXAMPLES
 * Real-world usage examples for the new biometric system
 */

// ==========================================
// EXAMPLE 1: Upload & Process Biometric File
// ==========================================

const express = require('express');
const multer = require('multer');
const EnhancedBiometricProcessor = require('./services/enhancedBiometricProcessor');

const upload = multer({ dest: './uploads/' });
const processor = new EnhancedBiometricProcessor();

app.post('/upload-biometric', upload.single('file'), async (req, res) => {
  try {
    // Upload and process with enhanced ID resolution
    const result = await processor.parseFile(
      req.file.path,
      req.file.originalname,
      req.user.id
    );

    res.json({
      success: true,
      message: `Processed ${result.processedRecords} records`,
      successful: result.successfulMatches,
      errors: result.errors.length,
      ambiguous: result.ambiguousMatches.length,
      duplicatesRemoved: result.duplicatesDetected
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ==========================================
// EXAMPLE 2: Get Attendance with Salary
// ==========================================

app.get('/dashboard/daily', async (req, res) => {
  const { date, departmentId } = req.query;

  const attendance = await DailyAttendance.find({
    date: {
      $gte: new Date(date).setHours(0, 0, 0),
      $lte: new Date(date).setHours(23, 59, 59)
    }
  })
    .populate('user')
    .lean();

  // Format with salary display
  const formatted = attendance.map(record => ({
    employee: record.user.name,
    status: record.status,
    clockIn: record.biometricTimeIn?.toLocaleTimeString(),
    clockOut: record.biometricTimeOut?.toLocaleTimeString(),
    workedHours: record.totalHoursWorked,
    earnings: `₹${record.basicSalaryForDay?.toLocaleString('en-IN')}`,
    mergeStatus: record.attendanceMergeDetails?.remarks,
    alert: record.attendanceMergeDetails?.remarks?.includes('MISMATCH') ? '⚠️' : '✅'
  }));

  res.json(formatted);
});

// ==========================================
// EXAMPLE 3: Run Migration for Date Range
// ==========================================

const AttendanceDataMigration = require('./utils/attendanceDataMigration');

app.post('/admin/migrate-attendance', async (req, res) => {
  // Check admin role
  if (req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Admin only' });
  }

  const { startDate, endDate } = req.body;

  try {
    const migration = new AttendanceDataMigration();
    
    console.log(`Starting migration from ${startDate} to ${endDate}...`);
    
    const result = await migration.runFullMigration(startDate, endDate);

    res.json({
      success: true,
      message: 'Migration completed',
      stats: {
        backedUp: result.stats.backedUp,
        cleaned: result.stats.cleaned,
        fixed: result.stats.fixed,
        reconciled: result.stats.reconciled,
        errors: result.stats.errors.length
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ==========================================
// EXAMPLE 4: Frontend - Display Attendance
// ==========================================

import React, { useState, useEffect } from 'react';
import { formatINR } from '@/utils/currencyFormatter';
import { SalaryCard, MismatchAlert, AttendanceSummary } from '@/utils/currencyFormatter';

function AttendanceDashboard() {
  const [attendance, setAttendance] = useState([]);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    fetchAttendance();
  }, []);

  const fetchAttendance = async () => {
    const response = await fetch(
      `/api/dashboard/attendance-summary?startDate=2024-12-01&endDate=2024-12-31`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    const data = await response.json();
    setAttendance(data.records);
    setSummary(data.summary);
  };

  return (
    <div className="attendance-dashboard p-8">
      <h1 className="text-3xl font-bold mb-8">Attendance Dashboard</h1>

      {/* Summary Section */}
      {summary && <AttendanceSummary summary={summary} showSalary={true} />}

      {/* Daily Records */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
        {attendance.map((record) => (
          <div key={record._id} className="attendance-card p-4 bg-white rounded-lg shadow">
            {/* Employee Info */}
            <div className="mb-4">
              <h3 className="font-semibold text-lg">{record.employee.name}</h3>
              <p className="text-sm text-gray-500">{record.date}</p>
              <span className={`badge mt-2 px-3 py-1 rounded-full text-sm font-semibold
                ${record.attendance.status === 'Present' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                {record.attendance.status}
              </span>
            </div>

            {/* Times */}
            <div className="border-t border-gray-200 py-3 mb-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Clock In:</span>
                <span className="font-medium">{record.times.clockIn || 'N/A'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Clock Out:</span>
                <span className="font-medium">{record.times.clockOut || 'N/A'}</span>
              </div>
              <div className="flex justify-between text-sm mt-2">
                <span className="text-gray-600">Worked Hours:</span>
                <span className="font-medium">{record.times.worked_hours}h</span>
              </div>
            </div>

            {/* Salary */}
            <SalaryCard
              label="Daily Earnings"
              amount={record.salary.earnedToday}
              type="positive"
            />

            {/* Merge Status */}
            {record.merge.hasAlert && (
              <MismatchAlert
                timeDiffIn={record.merge.timeDifferences?.inDiff}
                timeDiffOut={record.merge.timeDifferences?.outDiff}
                remarks={record.merge.remarks}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default AttendanceDashboard;

// ==========================================
// EXAMPLE 5: Frontend - Monthly Salary Report
// ==========================================

function MonthlySalaryReport() {
  const [monthlyData, setMonthlyData] = useState(null);

  useEffect(() => {
    fetchMonthlyData();
  }, []);

  const fetchMonthlyData = async () => {
    const response = await fetch(
      `/api/dashboard/employee/${userId}/monthly?year=2024&month=12`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    const data = await response.json();
    setMonthlyData(data);
  };

  if (!monthlyData) return <div>Loading...</div>;

  return (
    <div className="monthly-report p-8">
      <div className="header mb-8">
        <h1 className="text-3xl font-bold">Monthly Salary Report</h1>
        <p className="text-gray-600">
          {monthlyData.period.range.start} to {monthlyData.period.range.end}
        </p>
      </div>

      {/* Summary Cards */}
      <div className="summary-grid grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="card bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg">
          <p className="text-gray-600 text-sm">Present Days</p>
          <p className="text-2xl font-bold text-blue-900">{monthlyData.summary.presentDays}</p>
        </div>
        <div className="card bg-gradient-to-br from-red-50 to-red-100 p-4 rounded-lg">
          <p className="text-gray-600 text-sm">Absent Days</p>
          <p className="text-2xl font-bold text-red-900">{monthlyData.summary.absentDays}</p>
        </div>
        <div className="card bg-gradient-to-br from-yellow-50 to-yellow-100 p-4 rounded-lg">
          <p className="text-gray-600 text-sm">Half Days</p>
          <p className="text-2xl font-bold text-yellow-900">{monthlyData.summary.halfDays}</p>
        </div>
        <div className="card bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg">
          <p className="text-gray-600 text-sm">Total Hours</p>
          <p className="text-2xl font-bold text-green-900">{monthlyData.summary.totalHours}h</p>
        </div>
      </div>

      {/* Total Earnings */}
      <div className="earnings-section bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 rounded-lg mb-8">
        <p className="text-lg opacity-90">Total Earnings</p>
        <p className="text-4xl font-bold mt-2">{monthlyData.summary.formattedTotalEarnings}</p>
      </div>

      {/* Daily Breakdown */}
      <div className="daily-breakdown">
        <h2 className="text-xl font-bold mb-4">Daily Breakdown</h2>
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="p-3 text-left">Date</th>
              <th className="p-3 text-left">Status</th>
              <th className="p-3 text-left">Clock In</th>
              <th className="p-3 text-left">Clock Out</th>
              <th className="p-3 text-right">Hours</th>
              <th className="p-3 text-right">Earnings</th>
            </tr>
          </thead>
          <tbody>
            {monthlyData.dailyRecords.map((day) => (
              <tr key={day.date} className="border-b border-gray-200 hover:bg-gray-50">
                <td className="p-3">{day.date}</td>
                <td className="p-3">
                  <span className={`badge px-2 py-1 rounded text-xs font-semibold
                    ${day.status === 'Present' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                    {day.status}
                  </span>
                </td>
                <td className="p-3">{day.clockIn || '-'}</td>
                <td className="p-3">{day.clockOut || '-'}</td>
                <td className="p-3 text-right font-medium">{day.workedHours}</td>
                <td className="p-3 text-right font-semibold text-green-600">{day.formattedEarned}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default MonthlySalaryReport;

// ==========================================
// EXAMPLE 6: Get Audit Report
// ==========================================

app.get('/admin/audit', async (req, res) => {
  const { startDate, endDate } = req.query;

  try {
    const response = await fetch(
      `http://localhost:5000/api/biometric/audit?startDate=${startDate}&endDate=${endDate}`,
      { headers: { 'Authorization': `Bearer ADMIN_TOKEN` } }
    );

    const { auditReport, recommendations } = await response.json();

    console.log(`\n📊 Audit Report for ${startDate} to ${endDate}`);
    console.log(`Total Issues Found: ${auditReport.totalIssuesFound}`);
    console.log(`\nIssue Breakdown:`);
    
    for (const [category, issues] of Object.entries(auditReport.issues)) {
      if (Array.isArray(issues) && issues.length > 0) {
        console.log(`  ${category}: ${issues.length}`);
      }
    }

    console.log(`\nRecommendations:`);
    for (const rec of recommendations) {
      console.log(`\n${rec.category} (${rec.priority}):`);
      for (const fix of rec.fixes) {
        console.log(`  • ${fix}`);
      }
    }

    res.json({ auditReport, recommendations });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ==========================================
// EXAMPLE 7: Check for Mismatches
// ==========================================

app.get('/admin/mismatches', async (req, res) => {
  const { startDate, endDate } = req.query;

  try {
    const response = await fetch(
      `http://localhost:5000/api/dashboard/mismatches?startDate=${startDate}&endDate=${endDate}`,
      { headers: { 'Authorization': `Bearer ADMIN_TOKEN` } }
    );

    const { totalMismatches, records, summary } = await response.json();

    console.log(`\n⚠️  Time Mismatches Found: ${totalMismatches}`);
    console.log(`  HIGH severity: ${summary.high}`);
    console.log(`  MEDIUM severity: ${summary.medium}`);
    console.log(`  LOW severity: ${summary.low}`);

    console.log(`\nRecords Requiring Review:`);
    for (const record of records.slice(0, 10)) {
      console.log(`\n  ${record.employee.name} (${record.date})`);
      console.log(`    IN Diff: ${record.mismatch.inTimeDiff} min`);
      console.log(`    OUT Diff: ${record.mismatch.outTimeDiff} min`);
      console.log(`    Alert: ${record.alertSeverity}`);
    }

    res.json({ totalMismatches, records, summary });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ==========================================
// EXAMPLE 8: Test Identity Resolution
// ==========================================

const BiometricIdentityResolver = require('./utils/biometricIdentityResolver');

async function testIdentityResolution() {
  const resolver = new BiometricIdentityResolver();

  const employees = [
    { _id: '1', firstName: 'Rishabh', lastName: 'Yadav', biometric_code: 'E001' },
    { _id: '2', firstName: 'Rahul', lastName: 'Kadam', biometric_code: 'E002' },
    { _id: '3', firstName: 'Rahul', lastName: 'Kumar', biometric_code: 'E003' }
  ];

  // Test 1: Direct ID Match
  console.log('Test 1: Direct ID Match');
  const result1 = await resolver.mapBiometricToEmployee('E001', 'Rishabh Y', employees);
  console.log(result1.matchType); // DIRECT_ID_MATCH

  // Test 2: First Name Match (Multiple - Disambiguate by Surname Initial)
  console.log('\nTest 2: Surname Initial Match');
  const result2 = await resolver.mapBiometricToEmployee('UNKNOWN', 'Rahul K', employees);
  console.log(result2.employeeId); // Should resolve to Rahul Kumar

  // Test 3: Fuzzy Match (Typo Correction)
  console.log('\nTest 3: Fuzzy Match');
  const result3 = await resolver.mapBiometricToEmployee('UNKNOWN', 'Rishab Yadv', employees);
  console.log(result3.matchType); // FUZZY_MATCH

  // Test 4: Ambiguous Match
  console.log('\nTest 4: Ambiguous Match');
  const result4 = await resolver.mapBiometricToEmployee('UNKNOWN', 'Rahul', employees);
  console.log(result4.error); // AMBIGUOUS_MATCH
}

testIdentityResolution();

// ==========================================
// EXAMPLE 9: Test Merge Logic
// ==========================================

const AttendanceMergeLogic = require('./utils/attendanceMergeLogic');

async function testMergeLogic() {
  const merger = new AttendanceMergeLogic({
    timezone: 'Asia/Kolkata',
    tolerance: 20
  });

  // Test Case 1: Both exist and within tolerance
  console.log('Test Case 1: Both within 20-min tolerance');
  const result1 = await merger.mergeAttendance({
    employee_id: 'emp123',
    date: new Date('2024-12-15'),
    wf_in: new Date('2024-12-15T09:00:00'),
    wf_out: new Date('2024-12-15T18:00:00'),
    bio_in: new Date('2024-12-15T09:05:00'),
    bio_out: new Date('2024-12-15T17:55:00')
  });
  console.log(result1.merge_case); // CASE1_BOTH_MATCHED
  console.log(result1.merge_remarks); // MATCHED

  // Test Case 2: Mismatch > 20 minutes
  console.log('\nTest Case 2: Mismatch > 20 minutes');
  const result2 = await merger.mergeAttendance({
    employee_id: 'emp123',
    date: new Date('2024-12-15'),
    wf_in: new Date('2024-12-15T09:00:00'),
    wf_out: new Date('2024-12-15T18:00:00'),
    bio_in: new Date('2024-12-15T09:45:00'), // 45 min difference
    bio_out: new Date('2024-12-15T17:00:00')
  });
  console.log(result2.merge_case); // CASE1_BOTH_MISMATCH
  console.log(result2.merge_remarks); // MISMATCH_20+

  // Test Case 3: Only workflow exists
  console.log('\nTest Case 3: Only workflow exists');
  const result3 = await merger.mergeAttendance({
    employee_id: 'emp123',
    date: new Date('2024-12-15'),
    wf_in: new Date('2024-12-15T09:00:00'),
    wf_out: new Date('2024-12-15T18:00:00'),
    bio_in: null,
    bio_out: null
  });
  console.log(result3.merge_case); // CASE2_WF_ONLY
  console.log(result3.merge_remarks); // BIO_MISSING
}

testMergeLogic();

// ==========================================
// EXAMPLE 10: Quick Start Script Usage
// ==========================================

// Run from command line:
// node scripts/biometric-quickstart.js --action=audit --start=2024-12-01 --end=2024-12-31
// node scripts/biometric-quickstart.js --action=migrate --start=2024-12-01 --end=2024-12-31
// node scripts/biometric-quickstart.js --action=check-health
// node scripts/biometric-quickstart.js --action=cleanup
