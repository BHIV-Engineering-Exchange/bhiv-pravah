# 🚀 Biometric Attendance & Salary System - Quick Start Guide

## ⚡ 5-Minute Setup

### 1. Prerequisites
✅ MongoDB running
✅ Node.js installed
✅ Server and client already set up

### 2. Install Dependencies
```bash
# Already done! These packages were installed:
# - xlsx (Excel processing)
# - csv-parser (CSV parsing)
# - moment (date handling)
# - multer (file uploads)
```

### 3. Start the System
```bash
# Terminal 1 - Start Backend (if not running)
cd server
npm start

# Terminal 2 - Start Frontend (if not running)
cd client
npm start
```

### 4. Access the Dashboard
```
http://localhost:5173/biometric-attendance-dashboard
```

---

## 📝 First-Time Setup (5 Steps)

### Step 1: Create Employee Master Records

Before uploading biometric data, set up employee salary configuration:

**API Endpoint:** `POST /api/biometric-attendance/employee-master`

**Example Request:**
```javascript
{
  "userId": "675333df5f90bed08b0f0ba4",  // Get from Users collection
  "employeeId": "EMP001",
  "biometricId": "BIO123",
  "salaryType": "Monthly",
  "monthlySalary": 6000,
  "standardShiftHours": 8,
  "overtimeEnabled": true,
  "overtimeRate": 1.5,
  "allowances": {
    "housing": 500,
    "transport": 200,
    "medical": 100
  },
  "deductions": {
    "tax": 300,
    "insurance": 100
  }
}
```

**Quick Test with curl:**
```bash
curl -X POST http://localhost:5001/api/biometric-attendance/employee-master \
  -H "Content-Type: application/json" \
  -H "x-auth-token: YOUR_TOKEN_HERE" \
  -d '{
    "userId": "YOUR_USER_ID",
    "employeeId": "EMP001",
    "salaryType": "Monthly",
    "monthlySalary": 6000
  }'
```

### Step 2: Prepare Sample Biometric Data

Create a CSV file named `sample_attendance.csv`:

```csv
employee_id,biometric_id,punch_time,device_id,location
EMP001,BIO123,2025-12-06 09:00:00,DEVICE1,Main Office
EMP001,BIO123,2025-12-06 18:30:00,DEVICE1,Main Office
EMP002,BIO456,2025-12-06 09:15:00,DEVICE2,Branch Office
EMP002,BIO456,2025-12-06 17:45:00,DEVICE2,Branch Office
EMP003,BIO789,2025-12-06 08:55:00,DEVICE1,Main Office
EMP003,BIO789,2025-12-06 18:00:00,DEVICE1,Main Office
```

### Step 3: Upload Biometric Data

1. Go to dashboard: `http://localhost:5173/biometric-attendance-dashboard`
2. Click **Upload Data** tab
3. Click **Select File** and choose your CSV
4. Click **Upload & Process**
5. Wait for success message

### Step 4: Derive Daily Attendance

1. Stay on **Upload Data** tab
2. Scroll to **Derive Daily Attendance** section
3. Click **Derive Attendance from Punches**
4. System will group punches and calculate hours

### Step 5: View Salary Calculation

1. Click **Salary Calculation** tab
2. Select date range (start: 2025-12-01, end: 2025-12-31)
3. View results:
   - Grand Total Summary
   - Employee-wise breakdown
4. Click **Export** to download Excel report

---

## 🎯 Key Features at a Glance

### Dashboard Tabs

1. **📤 Upload Data**
   - Upload CSV/Excel files
   - View upload history
   - Derive attendance from punches

2. **💰 Salary Calculation**
   - Select date range
   - Filter by department/work type
   - View grand totals and employee breakdown
   - Export to Excel

3. **📋 Detailed Logs**
   - View daily punch-in/out records
   - Filter by date/employee/status
   - Export attendance logs

4. **📊 Employee Summary**
   - Aggregated data by employee
   - Present/absent/leave statistics
   - Total hours and earnings

---

## 📊 Sample Data Scenarios

### Scenario 1: Full Day Present
```
Punch In:  09:00 AM
Punch Out: 06:00 PM
Hours: 9 hours
Status: Present
Regular Hours: 8
Overtime: 1 hour
```

### Scenario 2: Half Day
```
Punch In:  09:00 AM
Punch Out: 01:00 PM
Hours: 4 hours
Status: Half Day
Regular Hours: 4
Overtime: 0
```

### Scenario 3: Late Arrival
```
Punch In:  10:30 AM (Late!)
Punch Out: 06:30 PM
Hours: 8 hours
Status: Late
Regular Hours: 8
Overtime: 0
```

### Scenario 4: Overtime
```
Punch In:  09:00 AM
Punch Out: 08:00 PM
Hours: 11 hours
Status: Present
Regular Hours: 8
Overtime: 3 hours
```

### Scenario 5: Missing Punch Out
```
Punch In:  09:00 AM
Punch Out: (none)
Status: Absent (incomplete)
Discrepancy: Yes - Missing punch out
```

---

## 🧪 Testing the System

### Test 1: Upload Sample Data
```bash
# Use the dashboard or test with API
curl -X POST http://localhost:5001/api/biometric-attendance/upload \
  -H "x-auth-token: YOUR_TOKEN" \
  -F "file=@sample_attendance.csv"
```

### Test 2: Derive Attendance
```bash
curl -X POST http://localhost:5001/api/biometric-attendance/derive-attendance \
  -H "Content-Type: application/json" \
  -H "x-auth-token: YOUR_TOKEN" \
  -d '{
    "startDate": "2025-12-01",
    "endDate": "2025-12-31"
  }'
```

### Test 3: Calculate Salary
```bash
curl -X POST http://localhost:5001/api/biometric-attendance/salary-calculation \
  -H "Content-Type: application/json" \
  -H "x-auth-token: YOUR_TOKEN" \
  -d '{
    "startDate": "2025-12-01",
    "endDate": "2025-12-31"
  }'
```

### Test 4: Get Today's KPIs
```bash
curl -X GET http://localhost:5001/api/biometric-attendance/dashboard-kpis \
  -H "x-auth-token: YOUR_TOKEN"
```

---

## 🎨 Dashboard Screenshots Guide

### Main Dashboard View
- **Top**: KPI cards showing today's stats
- **Tabs**: Upload, Salary, Logs, Aggregates
- **Filters**: Date range, department, work type
- **Export**: Download Excel reports

### KPI Cards Display:
```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│ Total Employees │ Present Today   │ Avg Hours Today │ Est. Payroll    │
│      50         │      45         │      7.8 hrs    │   $125,000      │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

---

## 💡 Pro Tips

### 1. **Batch Upload**
Upload multiple days of data at once. The system will automatically group by date.

### 2. **Regular Sync**
Upload biometric data weekly to catch discrepancies early.

### 3. **Export Often**
Export salary reports at month-end for payroll processing.

### 4. **Review Discrepancies**
Check upload history for unmatched employees and fix mapping.

### 5. **Configure Standards**
Set correct standard shift hours per employee for accurate overtime calculation.

---

## 🔧 Common CSV Formats Supported

### Format 1: Standard
```csv
employee_id,punch_time,device_id,location
EMP001,2025-12-06 09:00:00,DEVICE1,Office
```

### Format 2: With Biometric ID
```csv
emp_id,card_no,timestamp,terminal
EMP001,BIO123,06/12/2025 09:00,T1
```

### Format 3: Minimal
```csv
id,time
EMP001,2025-12-06 09:00
```

The system intelligently detects and maps columns!

---

## 📈 Expected Results

After following this guide, you should see:

✅ **Employee Master Records** created for all employees
✅ **Biometric Punches** uploaded and matched
✅ **Daily Attendance** derived with hours calculated
✅ **Salary Calculations** showing accurate amounts
✅ **Dashboard KPIs** displaying current stats
✅ **Excel Exports** ready for payroll

---

## 🚨 Troubleshooting Quick Fixes

### Problem: "No matching user found"
**Fix:** Create Employee Master record with correct employeeId

### Problem: Salary shows $0.00
**Fix:** Set salary configuration in Employee Master

### Problem: Upload fails
**Fix:** Check CSV format, ensure columns match expected names

### Problem: Hours calculation wrong
**Fix:** Verify punch times are in correct format and timezone

### Problem: Dashboard shows "Loading..."
**Fix:** Check backend is running on port 5001, check network tab for errors

---

## 📞 Need Help?

1. **Check Server Logs**: `cd server && npm start` (look for errors)
2. **Check Browser Console**: F12 → Console tab
3. **Verify API**: Test endpoints with curl or Postman
4. **Review Documentation**: See `BIOMETRIC_ATTENDANCE_SALARY_SYSTEM.md`

---

## 🎉 You're All Set!

Your biometric attendance and salary management system is now fully operational!

**Next Steps:**
1. Create Employee Master records for all employees
2. Upload your first biometric data file
3. Derive attendance and review results
4. Calculate salaries for the current period
5. Export reports for payroll

**Dashboard URL:** `http://localhost:5173/biometric-attendance-dashboard`

---

## ⚙️ System Architecture Summary

```
User Uploads CSV/Excel
        ↓
Biometric Processor parses file
        ↓
BiometricPunch records created
        ↓
Employee matching via EmployeeMaster
        ↓
Derive Attendance groups punches
        ↓
DailyAttendance records with hours
        ↓
Salary Service calculates pay
        ↓
Dashboard displays results
        ↓
Export to Excel for payroll
```

---

**Ready to Process Your First Payroll!** 🎊

For detailed documentation, see: `BIOMETRIC_ATTENDANCE_SALARY_SYSTEM.md`
